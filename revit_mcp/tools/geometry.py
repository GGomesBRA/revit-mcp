# -*- coding: utf-8 -*-

def register(mcp, base_url, http_get, http_post):
    @mcp.tool()
    async def draw_detail_line(x1, y1, x2, y2, z1=0.0, z2=0.0, ctx=None):
        payload = {"x1": x1, "y1": y1, "x2": x2, "y2": y2, "z1": z1, "z2": z2}
        return await http_post(base_url + "/draw_detail_line/", payload)

    @mcp.tool()
    async def draw_model_line(x1, y1, z1, x2, y2, z2, ctx=None):
        payload = {"x1": x1, "y1": y1, "z1": z1, "x2": x2, "y2": y2, "z2": z2}
        return await http_post(base_url + "/draw_model_line/", payload)

    @mcp.tool()
    async def draw_model_polyline(points, ctx=None):
        # points = [[x,y,z], ...]
        return await http_post(base_url + "/draw_model_polyline/", {"points": points})
