# -*- coding: utf-8 -*-
import json

from pyrevit import DB

from revit_mcp.utils import (
    Tx,
    err,
    log_api_call,
    ok,
)


def register_routes(api):
    @api.route("/families/", methods=["GET"])
    def list_families(doc):
        log_api_call("GET", "/families/")
        try:
            families = []
            collector = DB.FilteredElementCollector(doc).OfClass(DB.Family)
            for fam in collector:
                # Get family category
                cat_name = fam.FamilyCategory.Name if fam.FamilyCategory else "Unknown"
                
                # Count symbols/types in this family
                symbol_ids = fam.GetFamilySymbolIds()
                symbol_count = symbol_ids.Count if symbol_ids else 0
                
                families.append({
                    "id": int(fam.Id.IntegerValue),
                    "name": fam.Name,
                    "category": cat_name,
                    "symbolCount": symbol_count
                })
            
            return ok({"families": families, "count": len(families)})
        except Exception as ex:
            return err(ex)

    @api.route("/families/<int:family_id>/symbols/", methods=["GET"])
    def get_family_symbols(doc, family_id):
        log_api_call("GET", "/families/%d/symbols/" % family_id)
        try:
            fam = doc.GetElement(DB.ElementId(family_id))
            if fam is None or not isinstance(fam, DB.Family):
                return err("Family not found or invalid ID", 404)
            
            symbols = []
            symbol_ids = fam.GetFamilySymbolIds()
            for sym_id in symbol_ids:
                sym = doc.GetElement(sym_id)
                if sym and isinstance(sym, DB.FamilySymbol):
                    symbols.append({
                        "id": int(sym.Id.IntegerValue),
                        "name": sym.Name,
                        "familyName": sym.FamilyName if hasattr(sym, "FamilyName") else fam.Name,
                        "isActive": sym.IsActive
                    })
            
            return ok({
                "familyId": family_id,
                "familyName": fam.Name,
                "symbols": symbols
            })
        except Exception as ex:
            return err(ex)

    @api.route("/families/search_libraries/", methods=["POST"])
    def search_family_in_libraries(doc, request):
        data = request.data if isinstance(request.data, dict) else json.loads(request.data or "{}")
        log_api_call("POST", "/families/search_libraries/", data)
        try:
            import glob
            import os
            
            family_name = data.get("familyName")
            relative_path = data.get("relativePath", "")  # e.g., "Brazil/Structural Columns"
            
            if not family_name:
                return err("familyName is required", 400)
            
            # Standard Revit library base paths
            library_bases = [
                r"C:/ProgramData/Autodesk/RVT 2026/Libraries",
                r"C:/ProgramData/Autodesk/RVT 2025/Libraries",
                r"C:/ProgramData/Autodesk/RVT 2024/Libraries",
                r"C:/ProgramData/Autodesk/RVT 2023/Libraries",
                r"C:/ProgramData/Autodesk/RVT 2022/Libraries",
            ]
            
            found_files = []
            
            for base_path in library_bases:
                if not os.path.exists(base_path):
                    continue
                
                # Build search path
                search_dir = os.path.join(base_path, relative_path) if relative_path else base_path
                
                if not os.path.exists(search_dir):
                    continue
                
                # Search for the family file (case-insensitive)
                pattern = os.path.join(search_dir, "**", "%s.rfa" % family_name)
                matches = glob.glob(pattern, recursive=True)
                
                for match in matches:
                    found_files.append({
                        "path": match,
                        "version": base_path.split("RVT ")[1].split("/")[0] if "RVT " in base_path else "Unknown",
                        "exists": os.path.exists(match)
                    })
            
            if not found_files:
                return ok({
                    "found": False,
                    "searchedPaths": library_bases,
                    "relativePath": relative_path,
                    "familyName": family_name,
                    "files": []
                })
            
            return ok({
                "found": True,
                "familyName": family_name,
                "files": found_files,
                "count": len(found_files)
            })
        except Exception as ex:
            return err(ex)

    @api.route("/families/load/", methods=["POST"])
    def load_family(doc, request):
        data = request.data if isinstance(request.data, dict) else json.loads(request.data or "{}")
        log_api_call("POST", "/families/load/", data)
        try:
            file_path = data.get("filePath")
            if not file_path:
                return err("filePath is required", 400)
            
            # Check if file exists
            import os
            if not os.path.exists(file_path):
                return err("Family file not found: %s" % file_path, 404)
            
            with Tx(doc, "MCP: Load Family"):
                # LoadFamily returns a tuple: (bool success, Family family)
                success, family = doc.LoadFamily(file_path)
                
                if not success or family is None:
                    return err("Failed to load family from: %s" % file_path, 500)
                
                # Get the loaded family's symbols
                symbol_ids = family.GetFamilySymbolIds()
                symbols = []
                for sym_id in symbol_ids:
                    sym = doc.GetElement(sym_id)
                    if sym:
                        symbols.append({
                            "id": int(sym.Id.IntegerValue),
                            "name": sym.Name,
                            "isActive": sym.IsActive
                        })
                
            return ok({
                "ok": True,
                "familyId": int(family.Id.IntegerValue),
                "familyName": family.Name,
                "symbols": symbols
            })
        except Exception as ex:
            return err(ex)

    @api.route("/families/symbols/<int:symbol_id>/activate/", methods=["POST"])
    def activate_family_symbol(doc, symbol_id):
        log_api_call("POST", "/families/symbols/%d/activate/" % symbol_id)
        try:
            sym = doc.GetElement(DB.ElementId(symbol_id))
            if sym is None or not isinstance(sym, DB.FamilySymbol):
                return err("FamilySymbol not found or invalid ID", 404)
            
            if sym.IsActive:
                return ok({
                    "ok": True,
                    "message": "Symbol was already active",
                    "symbolId": symbol_id,
                    "symbolName": sym.Name
                })
            
            with Tx(doc, "MCP: Activate Family Symbol"):
                sym.Activate()
                doc.Regenerate()
            
            return ok({
                "ok": True,
                "symbolId": symbol_id,
                "symbolName": sym.Name,
                "isActive": sym.IsActive
            })
        except Exception as ex:
            return err(ex)

    @api.route("/families/search/", methods=["POST"])
    def search_families(doc, request):
        data = request.data if isinstance(request.data, dict) else json.loads(request.data or "{}")
        log_api_call("POST", "/families/search/", data)
        try:
            query = data.get("query", "").lower()
            category_filter = data.get("category")
            
            families = []
            collector = DB.FilteredElementCollector(doc).OfClass(DB.Family)
            
            for fam in collector:
                cat_name = fam.FamilyCategory.Name if fam.FamilyCategory else "Unknown"
                
                # Apply filters
                if category_filter and cat_name.lower() != category_filter.lower():
                    continue
                
                if query and query not in fam.Name.lower() and query not in cat_name.lower():
                    continue
                
                symbol_ids = fam.GetFamilySymbolIds()
                families.append({
                    "id": int(fam.Id.IntegerValue),
                    "name": fam.Name,
                    "category": cat_name,
                    "symbolCount": symbol_ids.Count if symbol_ids else 0
                })
            
            return ok({
                "families": families,
                "count": len(families),
                "query": query,
                "categoryFilter": category_filter
            })
        except Exception as ex:
            return err(ex)

