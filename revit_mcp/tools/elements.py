# -*- coding: utf-8 -*-
def register(mcp, base_url, http_get, http_post):
    @mcp.tool()
    async def create_wall_line(x1, y1, x2, y2, z=0.0, level="Level 1", wall_type=None, ctx=None):
        return await http_post(base_url + "/create_wall_line/", {
            "x1": x1, "y1": y1, "x2": x2, "y2": y2, "z": z,
            "level": level, "wall_type": wall_type
        })

    @mcp.tool()
    async def place_column(x, y, z=0.0, level="Level 1", type=None, ctx=None):
        return await http_post(base_url + "/place_column/", {
            "x": x, "y": y, "z": z, "level": level, "type": type
        })
    
    @mcp.tool()
    async def quantify_walls(ctx=None):
        """Calculate paint areas for all walls in the active Revit document.
        
        Returns information about each wall including area calculations
        and total paint area in square meters (m²).
        """
        return await http_get(base_url + "/quantify/walls/")
    
    @mcp.tool()
    async def place_rebar_cage_column(columnId: int, barType: str = None, stirrupShape: str = None, 
                                       stirrupSpacing: float = 0.2, cover: float = 0.03, ctx=None):
        """Create reinforcement cage for a concrete column with longitudinal bars and stirrups.
        
        Places 4 vertical rebar bars at corners (with cover) and stirrups distributed along height.
        
        Args:
            columnId: Element ID of the structural concrete column to detail
            barType: Name of RebarBarType (e.g., "Ø12 CA50"). Uses first available if not specified.
            stirrupShape: Name of RebarShape for stirrups (e.g., "Stirrup"). Optional.
            stirrupSpacing: Maximum spacing between stirrups in meters (default: 0.2m = 200mm)
            cover: Concrete cover in meters (default: 0.03m = 30mm)
        
        Returns:
            {"ok": True, "elementIds": [list of created rebar element IDs]}
        """
        return await http_post(base_url + "/place/rebar_cage_column/", {
            "columnId": columnId,
            "barType": barType,
            "stirrupShape": stirrupShape,
            "stirrupSpacing": stirrupSpacing,
            "cover": cover
        })