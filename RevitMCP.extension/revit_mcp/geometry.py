# -*- coding: utf-8 -*-
import json

from pyrevit import DB

from revit_mcp.utils import (
    Tx,
    active_uidoc,
    ensure_plane_for_line,
    err,
    get_detail_view_validation,
    log_api_call,
    ok,
)


def register_routes(api):
    @api.route("/validate/detail_line_view/", methods=["GET"])
    def validate_detail_line_view(doc):
        log_api_call("GET", "/validate/detail_line_view/")
        try:
            v = active_uidoc().ActiveView
            info = get_detail_view_validation(v)
            return ok(info)
        except Exception as ex:
            return err(ex)

    @api.route("/draw_detail_line/", methods=["POST"])
    def draw_detail_line(doc, request):
        data = request.data if isinstance(request.data, dict) else json.loads(request.data or "{}")
        log_api_call("POST", "/draw_detail_line/", data)
        try:
            p1 = DB.XYZ(float(data["x1"]), float(data["y1"]), float(data.get("z1", 0.0)))
            p2 = DB.XYZ(float(data["x2"]), float(data["y2"]), float(data.get("z2", 0.0)))
            v  = active_uidoc().ActiveView
            info = get_detail_view_validation(v)
            if not info.get("canDrawDetailLine", False):
                return err(info.get("reason") or "Active view does not support detail lines", 400)
            with Tx(doc, "MCP: Detail Line"):
                el = doc.Create.NewDetailCurve(v, DB.Line.CreateBound(p1, p2))
                return ok({"ok": True, "elementId": int(el.Id.IntegerValue)})
        except Exception as ex:
            return err(ex)

    @api.route("/draw_model_line/", methods=["POST"])
    def draw_model_line(doc, request):
        data = request.data if isinstance(request.data, dict) else json.loads(request.data or "{}")
        log_api_call("POST", "/draw_model_line/", data)
        try:
            p1 = DB.XYZ(float(data["x1"]), float(data["y1"]), float(data["z1"]))
            p2 = DB.XYZ(float(data["x2"]), float(data["y2"]), float(data["z2"]))
            plane = ensure_plane_for_line(p1, p2)
            with Tx(doc, "MCP: Model Line SP"):
                sp = DB.SketchPlane.Create(doc, plane)
            with Tx(doc, "MCP: Model Line"):
                crv = DB.Line.CreateBound(p1, p2)
                el = doc.Create.NewModelCurve(crv, sp)
                return ok({"ok": True, "elementId": int(el.Id.IntegerValue)})
        except Exception as ex:
            return err(ex)

    # Bonus: polyline of model lines
    @api.route("/draw_model_polyline/", methods=["POST"])
    def draw_model_polyline(doc, request):
        data = request.data if isinstance(request.data, dict) else json.loads(request.data or "{}")
        log_api_call("POST", "/draw_model_polyline/", data)
        try:
            pts = data.get("points", [])  # [[x,y,z], [x,y,z], ...]
            if len(pts) < 2:
                return err("Need at least two points", 400)
            xyz = [DB.XYZ(float(p[0]), float(p[1]), float(p[2])) for p in pts]
            plane = ensure_plane_for_line(xyz[0], xyz[1])
            with Tx(doc, "MCP: Polyline SP"):
                sp = DB.SketchPlane.Create(doc, plane)
            ids = []
            with Tx(doc, "MCP: Polyline"):
                for i in range(len(xyz) - 1):
                    el = doc.Create.NewModelCurve(DB.Line.CreateBound(xyz[i], xyz[i+1]), sp)
                    ids.append(int(el.Id.IntegerValue))
            return ok({"ok": True, "elementIds": ids})
        except Exception as ex:
            return err(ex)
