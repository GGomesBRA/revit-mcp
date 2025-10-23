# -*- coding: utf-8 -*-
from . import catalog, elements, families, geometry


def register_all(mcp, base_url, http_get, http_post):
    catalog.register(mcp, base_url, http_get, http_post)
    geometry.register(mcp, base_url, http_get, http_post)
    elements.register(mcp, base_url, http_get,http_post)
    families.register(mcp, base_url, http_get, http_post)
