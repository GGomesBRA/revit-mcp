# -*- coding: utf-8 -*-
import os

import httpx
from mcp.server.fastmcp import FastMCP
from tools import register_all

BASE = os.environ.get("REVIT_ROUTES_URL", "http://127.0.0.1:48884/revit_mcp")

async def _get(url):
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.get(url); r.raise_for_status(); return r.json()

async def _post(url, payload):
    async with httpx.AsyncClient(timeout=30) as c:
        r = await c.post(url, json=payload); r.raise_for_status(); return r.json()

m = FastMCP(name="Revit-MCP via Routes")
register_all(m, BASE, _get, _post)
if __name__ == "__main__":
    m.run(transport="stdio")
