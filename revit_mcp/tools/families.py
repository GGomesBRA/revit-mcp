# -*- coding: utf-8 -*-
def register(mcp, base_url, http_get, http_post):
    @mcp.tool()
    async def list_families(ctx=None):
        """Query all loaded families in the active Revit document.
        
        Returns a list of families with their id, name, category, and symbol count.
        Use this to find available families before placing elements or loading new ones.
        
        Example return:
        {
            "families": [
                {"id": 123, "name": "M_Concreto-Coluna Retangular", "category": "Structural Columns", "symbolCount": 5},
                {"id": 456, "name": "Basic Wall", "category": "Walls", "symbolCount": 10}
            ],
            "count": 2
        }
        """
        return await http_get(base_url + "/families/")

    @mcp.tool()
    async def get_family_symbols(familyId: int, ctx=None):
        """Get all symbols (types) for a specific family.
        
        Args:
            familyId: The Element ID of the family
        
        Returns information about each symbol/type in the family, including activation status.
        
        Example return:
        {
            "familyId": 123,
            "familyName": "M_Concreto-Coluna Retangular",
            "symbols": [
                {"id": 456, "name": "300x300mm", "familyName": "M_Concreto-Coluna Retangular", "isActive": true},
                {"id": 457, "name": "400x400mm", "familyName": "M_Concreto-Coluna Retangular", "isActive": false}
            ]
        }
        """
        return await http_get(base_url + "/families/%d/symbols/" % familyId)

    @mcp.tool()
    async def search_family_in_libraries(familyName: str, relativePath: str = "", ctx=None):
        """Search for a family file across all Revit library installations.
        
        Searches across RVT 2022-2026 library paths to find the specified family file.
        This is useful when you don't know the exact Revit version installed.
        
        Args:
            familyName: Name of the family file without .rfa extension
                       Example: "M_Concreto-Coluna Retangular"
            relativePath: Optional subdirectory path within Libraries folder
                         Example: "Brazil/Structural Columns"
        
        Returns list of found files with their full paths and Revit versions.
        
        Example return:
        {
            "found": true,
            "familyName": "M_Concreto-Coluna Retangular",
            "files": [
                {"path": "C:/ProgramData/.../M_Concreto-Coluna Retangular.rfa", "version": "2024", "exists": true}
            ],
            "count": 1
        }
        """
        payload = {"familyName": familyName}
        if relativePath:
            payload["relativePath"] = relativePath
        return await http_post(base_url + "/families/search_libraries/", payload)

    @mcp.tool()
    async def load_family(filePath: str, ctx=None):
        """Load a family (.rfa file) into the active Revit document.
        
        Args:
            filePath: Full path to the .rfa family file to load
                     Example: "C:/ProgramData/Autodesk/RVT 2024/Libraries/Brazil/Structural Columns/M_Concreto-Coluna Retangular.rfa"
        
        Returns information about the loaded family and its symbols/types.
        Note: Symbols may need to be activated before use with activate_family_symbol.
        
        Example return:
        {
            "ok": true,
            "familyId": 299100,
            "familyName": "M_Concreto-Coluna Retangular",
            "symbols": [
                {"id": 299101, "name": "300x300mm", "isActive": false},
                {"id": 299102, "name": "400x600mm", "isActive": false}
            ]
        }
        """
        return await http_post(base_url + "/families/load/", {"filePath": filePath})

    @mcp.tool()
    async def activate_family_symbol(symbolId: int, ctx=None):
        """Activate a family symbol (type) to make it available for placement.
        
        Args:
            symbolId: The Element ID of the family symbol to activate
        
        Family symbols must be activated before they can be used to create instances.
        This is especially important after loading new families.
        
        Example return:
        {
            "ok": true,
            "symbolId": 299101,
            "symbolName": "300x300mm",
            "isActive": true
        }
        """
        return await http_post(base_url + "/families/symbols/%d/activate/" % symbolId, {})

    @mcp.tool()
    async def search_families(query: str = "", category: str = None, ctx=None):
        """Search for families in the document by name or category.
        
        Args:
            query: Search text to match against family name or category (case-insensitive)
            category: Optional category filter (e.g., "Structural Columns", "Walls")
        
        Returns filtered list of families matching the search criteria.
        
        Example return:
        {
            "families": [
                {"id": 123, "name": "M_Concreto-Coluna Retangular", "category": "Structural Columns", "symbolCount": 5}
            ],
            "count": 1,
            "query": "concreto",
            "categoryFilter": "Structural Columns"
        }
        """
        payload = {"query": query}
        if category:
            payload["category"] = category
        return await http_post(base_url + "/families/search/", payload)

