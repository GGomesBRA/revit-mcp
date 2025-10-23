# -*- coding: utf-8 -*-
from datetime import datetime

from revit_mcp.utils import err, log_api_call, ok


def register_routes(api):
    @api.route("/status/", methods=["GET"])
    def status(doc):
        log_api_call("GET", "/status/")
        try:
            data = {
                "status": "active",
                "revit_available": bool(doc is not None),
                "document_title": getattr(doc, "Title", None),
                "api_name": "revit_mcp",
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            }
            return ok(data)
        except Exception as ex:
            return err(ex)
