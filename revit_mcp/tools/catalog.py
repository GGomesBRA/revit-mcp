# -*- coding: utf-8 -*-
def register(mcp, base_url, http_get, http_post):
    @mcp.tool()
    async def get_levels(ctx=None):
        """Query all available levels in the active Revit document.
        
        Returns a list of levels with their id, name, and elevation.
        Use this to find valid level names before placing elements like columns, walls, etc.
        
        Example return:
        {
            "levels": [
                {"id": 123, "name": "Level 1", "elev": 0.0},
                {"id": 124, "name": "Level 2", "elev": 12.0}
            ]
        }
        """
        return await http_get(base_url + "/levels/")

    @mcp.tool()
    async def get_element_types(ctx=None):
        """Query all available element types in the active Revit document.
        
        Returns types for walls, columns, beams, doors, windows, and rebar.
        Use this to find valid type names before creating elements.
        
        Example return:
        {
            "walls": [{"id": 123, "family": "Basic Wall", "name": "Generic - 8\""}],
            "columns": [{"id": 456, "family": "M_Concrete-Round", "name": "300mm"}],
            "beams": [...],
            "doors": [...],
            "windows": [...],
            "rebar": {
                "bar_types": [{"id": 789, "name": "Ø12 CA50"}],
                "shapes": [{"id": 101, "name": "Stirrup"}],
                "hook_types": [...],
                "cover_types": [...]
            }
        }
        """
        return await http_get(base_url + "/types/")

