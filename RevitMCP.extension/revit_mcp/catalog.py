# -*- coding: utf-8 -*-
from pyrevit import DB

from revit_mcp.utils import err, log_api_call, ok


def register_routes(api):
    @api.route("/levels/", methods=["GET"])
    def levels(doc):
        log_api_call("GET", "/levels/")
        try:
            rows = []
            it = DB.FilteredElementCollector(doc).OfClass(DB.Level)
            for lvl in it:
                rows.append({"id": int(lvl.Id.IntegerValue), "name": lvl.Name, "elev": lvl.Elevation})
            return ok({"levels": rows})
        except Exception as ex:
            return err(ex)

    @api.route("/types/", methods=["GET"])
    def types(doc):
        log_api_call("GET", "/types/")
        try:
            cats = [
                ("walls", DB.BuiltInCategory.OST_Walls),
                ("columns", DB.BuiltInCategory.OST_StructuralColumns),
                ("beams", DB.BuiltInCategory.OST_StructuralFraming),
                ("doors", DB.BuiltInCategory.OST_Doors),
                ("windows", DB.BuiltInCategory.OST_Windows),
            ]
            out = {}
            for key, bic in cats:
                lst = []
                it = DB.FilteredElementCollector(doc).OfCategory(bic).WhereElementIsElementType()
                for t in it:
                    # Let errors propagate - don't hide them
                    fam_name = t.FamilyName if hasattr(t, "FamilyName") else "Unknown"
                    type_name = t.Name if hasattr(t, "Name") else "Unknown"
                    lst.append({"id": int(t.Id.IntegerValue), "family": fam_name, "name": type_name})
                out[key] = lst
            # Rebar related types
            rebar_out = {}
            bar_types = []
            for t in DB.FilteredElementCollector(doc).OfClass(DB.Structure.RebarBarType):
                bar_types.append({"id": int(t.Id.IntegerValue), "name": t.Name})
            rebar_out["bar_types"] = bar_types

            shapes = []
            for s in DB.FilteredElementCollector(doc).OfClass(DB.Structure.RebarShape):
                shapes.append({"id": int(s.Id.IntegerValue), "name": s.Name})
            rebar_out["shapes"] = shapes

            hooks = []
            for h in DB.FilteredElementCollector(doc).OfClass(DB.Structure.RebarHookType):
                hooks.append({"id": int(h.Id.IntegerValue), "name": h.Name})
            rebar_out["hook_types"] = hooks

            covers = []
            for c in DB.FilteredElementCollector(doc).OfClass(DB.Structure.RebarCoverType):
                covers.append({"id": int(c.Id.IntegerValue), "name": c.Name})
            rebar_out["cover_types"] = covers

            out["rebar"] = rebar_out
            return ok(out)
        except Exception as ex:
            return err(ex)
