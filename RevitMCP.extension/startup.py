# -*- coding: utf-8 -*-
# RevitMCP.extension/startup.py  (IronPython/pyRevit Routes compatible)

import logging

from pyrevit import routes

# from Revit.DB import Document, ElementId
# from PyRevitLabs.PyRevit import PyRevitAttachment
# from PyRevit
# Import and register all route modules
from revit_mcp.catalog import register_routes as _cat
from revit_mcp.elements import register_routes as _ele
from revit_mcp.families import register_routes as _fam
from revit_mcp.geometry import register_routes as _geom
from revit_mcp.routes_core import register_routes as _core

# --------- logging (file) ----------
logger = logging.getLogger("revit_mcp.routes")
logger.setLevel(logging.ERROR)  # Only log errors
try:
    fh = logging.FileHandler(r"C:\Users\m170488\AppData\Roaming\pyRevit\Extensions\revit_routes.log")
    fh.setLevel(logging.ERROR)
    fh.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s]: %(message)s"))
    logger.addHandler(fh)
    logger.propagate = False
except Exception:
    pass  # If logging setup fails, direct file writes will still work

# --------- API root: http://<host>:48884/revit_mcp/... ----------
api = routes.API("revit_mcp")

try:
    _core(api)
    _geom(api)
    _ele(api)
    _cat(api)
    _fam(api)
except Exception as e:
    logger.error("Failed to register Revit MCP routes: %s" % str(e))
    raise