# -*- coding: utf-8 -*-
import json

from pyrevit import DB
from System.Collections.Generic import List  # type: ignore

from revit_mcp.utils import (
    Tx,
    err,
    find_level_by_name,
    find_rebar_bar_type_by_name,
    find_rebar_shape_by_name,
    find_type_by_name,
    log_api_call,
    ok,
)


def register_routes(api):
    @api.route("/validate/create_wall_line/", methods=["POST"])
    def validate_create_wall_line(doc, request):
        data = request.data if isinstance(request.data, dict) else json.loads(request.data or "{}")
        log_api_call("POST", "/validate/create_wall_line/", data)
        try:
            level_name = data.get("level") or "Level 1"
            wall_type_name = data.get("wall_type")

            level = find_level_by_name(doc, level_name)
            if level is None:
                return ok({"canCreate": False, "reason": "Level not found: %s" % level_name})

            if wall_type_name:
                wt = find_type_by_name(doc, DB.BuiltInCategory.OST_Walls, wall_type_name)
                if wt is None:
                    return ok({"canCreate": False, "reason": "Wall type not found: %s" % wall_type_name})

            # Validate geometry inputs
            try:
                x1 = float(data.get("x1", 0.0))
                y1 = float(data.get("y1", 0.0))
                x2 = float(data.get("x2", 0.0))
                y2 = float(data.get("y2", 0.0))
                if (x1 == x2) and (y1 == y2):
                    return ok({"canCreate": False, "reason": "Line has zero length"})
            except Exception:
                return ok({"canCreate": False, "reason": "Invalid numeric inputs"})

            return ok({"canCreate": True})
        except Exception as ex:
            return err(ex)
    @api.route("/validate/place_column/", methods=["POST"])
    def validate_place_column(doc, request):
        data = request.data if isinstance(request.data, dict) else json.loads(request.data or "{}")
        log_api_call("POST", "/validate/place_column/", data)
        try:
            level_name = data.get("level") or "Level 1"
            type_name  = data.get("type")

            level = find_level_by_name(doc, level_name)
            if level is None:
                return ok({"canPlace": False, "reason": "Level not found: %s" % level_name})

            if type_name:
                col_type = find_type_by_name(doc, DB.BuiltInCategory.OST_StructuralColumns, type_name)
                if col_type is None:
                    return ok({"canPlace": False, "reason": "Column type not found: %s" % type_name})
            else:
                # At least verify there exists any structural column type
                it = DB.FilteredElementCollector(doc)\
                    .OfCategory(DB.BuiltInCategory.OST_StructuralColumns)\
                    .WhereElementIsElementType()
                has_any = any(True for _ in it)
                if not has_any:
                    return ok({"canPlace": False, "reason": "No structural column types available"})

            return ok({"canPlace": True})
        except Exception as ex:
            return err(ex)
    @api.route("/create_wall_line/", methods=["POST"])
    def create_wall_line(doc, request):
        data = request.data if isinstance(request.data, dict) else json.loads(request.data or "{}")
        log_api_call("POST", "/create_wall_line/", data)
        try:
            # inputs
            x1 = float(data["x1"])
            y1 = float(data["y1"])
            z  = float(data.get("z", 0.0))
            x2 = float(data["x2"])
            y2 = float(data["y2"])
            level_name = data.get("level") or "Level 1"
            wall_type_name = data.get("wall_type")  # optional

            level = find_level_by_name(doc, level_name)
            if level is None:
                return err("Level not found: " + level_name, 400)

            if wall_type_name:
                wt = find_type_by_name(doc, DB.BuiltInCategory.OST_Walls, wall_type_name)
                if wt is None:
                    return err("Wall type not found: " + wall_type_name, 400)
            else:
                wt = None

            line = DB.Line.CreateBound(DB.XYZ(x1, y1, z), DB.XYZ(x2, y2, z))
            with Tx(doc, "MCP: Create Wall"):
                wall = DB.Wall.Create(doc, line, level.Id, False)
                if wt:
                    wall.ChangeTypeId(wt.Id)
            return ok({"ok": True, "elementId": int(wall.Id.IntegerValue)})
        except Exception as ex:
            return err(ex)

    @api.route("/place_column/", methods=["POST"])
    def place_column(doc, request):
        data = request.data if isinstance(request.data, dict) else json.loads(request.data or "{}")
        log_api_call("POST", "/place_column/", data)
        try:
            x = float(data["x"])
            y = float(data["y"])
            z = float(data.get("z", 0.0))
            level_name = data.get("level") or "Level 1"
            type_name  = data.get("type")  # e.g., a Structural Column type name

            level = find_level_by_name(doc, level_name)
            if level is None:
                return err("Level not found: " + level_name, 400)

            col_type = find_type_by_name(doc, DB.BuiltInCategory.OST_StructuralColumns, type_name) if type_name else None
            if type_name and col_type is None:
                return err("Column type not found: " + type_name, 400)

            with Tx(doc, "MCP: Place Column"):
                if col_type:
                    if not col_type.IsActive:
                        col_type.Activate()
                        doc.Regenerate()
                pt = DB.XYZ(x, y, z)
                famsym = col_type if col_type else None
                if famsym:
                    col = doc.Create.NewFamilyInstance(pt, famsym, level, DB.Structure.StructuralType.Column)
                else:
                    # fallback: first available column type
                    it = DB.FilteredElementCollector(doc)\
                        .OfCategory(DB.BuiltInCategory.OST_StructuralColumns)\
                        .WhereElementIsElementType()
                    famsym = None
                    for t in it:
                        famsym = t
                        break
                    if famsym is None:
                        return err("No structural column types available.", 400)
                    if not famsym.IsActive:
                        famsym.Activate()
                        doc.Regenerate()
                    col = doc.Create.NewFamilyInstance(pt, famsym, level, DB.Structure.StructuralType.Column)

            return ok({"ok": True, "elementId": int(col.Id.IntegerValue)})
        except Exception as ex:
            return err(ex)

    @api.route("/quantify/walls/", methods=["GET"])
    def quantify_walls(doc, request):
        log_api_call("GET", "/quantify/walls/")
        try:
            walls = []
            total_area = 0.0
            
            # Coletar todas as paredes
            collector = DB.FilteredElementCollector(doc)\
                .OfClass(DB.Wall)\
                .WhereElementIsNotElementType()
            
            walls = iter(collector)
            
            for wall in collector:
                try:
                    # Obter o parâmetro de área
                    area_param = wall.get_Parameter(DB.BuiltInParameter.HOST_AREA_COMPUTED)
                    if area_param and area_param.HasValue:
                        # Área em pés quadrados (unidade interna do Revit)
                        area_sqft = area_param.AsDouble()
                        # Converter para metros quadrados (1 pé² = 0.09290304 m²)
                        area_sqm = area_sqft * 0.09290304
                        
                        # Como temos duas faces (interna e externa), multiplicamos por 2
                        paint_area = area_sqm * 2
                        
                        wall_info = {
                            "id": int(wall.Id.IntegerValue),
                            "name": wall.Name if hasattr(wall, "Name") else "Wall",
                            "area_m2": round(area_sqm, 2),
                            "paint_area_m2": round(paint_area, 2)
                        }
                        
                        walls.append(wall_info)
                        total_area += paint_area
                        
                except Exception:
                    # Se falhar em uma parede específica, continua com as outras
                    continue
            
            result = {
                "walls": walls,
                "total_walls": len(walls),
                "total_paint_area_m2": round(total_area, 2),
                "unit": "m²"
            }
            
            return ok(result)
        except Exception as ex:
            return err(ex)

    @api.route("/validate/rebar_cage_column/", methods=["POST"])
    def validate_rebar_cage_column(doc, request):
        data = request.data if isinstance(request.data, dict) else json.loads(request.data or "{}")
        log_api_call("POST", "/validate/rebar_cage_column/", data)
        try:
            col_id = int(data.get("columnId", -1))
            bar_type = data.get("barType")
            shape_name = data.get("stirrupShape")
            spacing = float(data.get("stirrupSpacing", 0.2))
            cover = float(data.get("cover", 0.03))

            if col_id <= 0:
                return ok({"canDetail": False, "reason": "columnId missing/invalid"})

            col = doc.GetElement(DB.ElementId(col_id))
            if col is None or not isinstance(col, DB.FamilyInstance):
                return ok({"canDetail": False, "reason": "Element is not a FamilyInstance"})

            if col.Category is None or col.Category.Id.IntegerValue != int(DB.BuiltInCategory.OST_StructuralColumns):
                return ok({"canDetail": False, "reason": "Element is not a structural column"})

            sm = col.get_Parameter(DB.BuiltInParameter.STRUCTURAL_MATERIAL_TYPE)
            if not sm or sm.AsInteger() != int(DB.Structure.StructuralMaterialType.Concrete):
                return ok({"canDetail": False, "reason": "Column is not concrete"})
            if bar_type and find_rebar_bar_type_by_name(doc, bar_type) is None:
                return ok({"canDetail": False, "reason": "RebarBarType not found: %s" % bar_type})

            if shape_name and find_rebar_shape_by_name(doc, shape_name) is None:
                return ok({"canDetail": False, "reason": "RebarShape not found: %s" % shape_name})

            if spacing <= 0.0:
                return ok({"canDetail": False, "reason": "stirrupSpacing must be > 0"})

            if cover < 0.0:
                return ok({"canDetail": False, "reason": "cover must be >= 0"})

            return ok({"canDetail": True})
        except Exception as ex:
            return err(ex)

    @api.route("/place/rebar_cage_column/", methods=["POST"])
    def place_rebar_cage_column(doc, request):
        data = request.data if isinstance(request.data, dict) else json.loads(request.data or "{}")
        log_api_call("POST", "/place/rebar_cage_column/", data)
        try:
            col_id = int(data["columnId"])
            bar_type_name = data.get("barType")
            stirrup_shape_name = data.get("stirrupShape")
            spacing = float(data.get("stirrupSpacing", 0.2))
            cover = float(data.get("cover", 0.03))

            col = doc.GetElement(DB.ElementId(col_id))
            if col is None or not isinstance(col, DB.FamilyInstance):
                return err("Invalid element", 400)

            bar_type = find_rebar_bar_type_by_name(doc, bar_type_name) if bar_type_name else None
            if bar_type is None:
                it = DB.FilteredElementCollector(doc).OfClass(DB.Structure.RebarBarType)
                bar_type = next((x for x in it), None)
            if bar_type is None:
                return err("No RebarBarType available.", 400)

            stirrup_shape = find_rebar_shape_by_name(doc, stirrup_shape_name) if stirrup_shape_name else None

            bb = col.get_BoundingBox(None)
            if bb is None:
                return err("Column has no bounding box", 400)

            tr = col.GetTransform()
            minp = tr.OfPoint(bb.Min)
            maxp = tr.OfPoint(bb.Max)

            x1, x2 = minp.X + cover, maxp.X - cover
            y1, y2 = minp.Y + cover, maxp.Y - cover
            z1, z2 = minp.Z + cover, maxp.Z - cover

            pA1, pA2 = DB.XYZ(x1, y1, z1), DB.XYZ(x1, y1, z2)
            pB1, pB2 = DB.XYZ(x2, y1, z1), DB.XYZ(x2, y1, z2)
            pC1, pC2 = DB.XYZ(x2, y2, z1), DB.XYZ(x2, y2, z2)
            pD1, pD2 = DB.XYZ(x1, y2, z1), DB.XYZ(x1, y2, z2)

            vA = DB.Line.CreateBound(pA1, pA2)
            vB = DB.Line.CreateBound(pB1, pB2)
            vC = DB.Line.CreateBound(pC1, pC2)
            vD = DB.Line.CreateBound(pD1, pD2)

            normal = tr.BasisX

            created_ids = []

            with Tx(doc, "MCP: Column Rebar (longitudinals + stirrups)"):
                for crv in [vA, vB, vC, vD]:
                    curves = List[DB.Curve]()
                    curves.Add(crv)
                    rb = DB.Structure.Rebar.CreateFromCurves(
                        doc,
                        DB.Structure.RebarStyle.Standard,
                        bar_type,
                        None,
                        None,
                        col,
                        normal,
                        curves,
                        DB.Structure.RebarHookOrientation.Left,
                        DB.Structure.RebarHookOrientation.Left,
                        True,
                        True
                    )
                    created_ids.append(int(rb.Id.IntegerValue))

                if stirrup_shape is not None:
                    zbase = z1 + spacing * 0.5
                    p1 = DB.XYZ(x1, y1, zbase)
                    p2 = DB.XYZ(x2, y1, zbase)
                    p3 = DB.XYZ(x2, y2, zbase)
                    p4 = DB.XYZ(x1, y2, zbase)
                    rect = List[DB.Curve]()
                    rect.Add(DB.Line.CreateBound(p1, p2))
                    rect.Add(DB.Line.CreateBound(p2, p3))
                    rect.Add(DB.Line.CreateBound(p3, p4))
                    rect.Add(DB.Line.CreateBound(p4, p1))

                    stir = DB.Structure.Rebar.CreateFromCurvesAndShape(
                        doc, stirrup_shape, bar_type, None, None, col, normal, rect
                    )
                    acc = stir.GetShapeDrivenAccessor()
                    acc.SetLayoutAsMaximumSpacing(spacing, z2 - z1, True, True, True)
                    created_ids.append(int(stir.Id.IntegerValue))

            return ok({"ok": True, "elementIds": created_ids})
        except Exception as ex:
            return err(ex)