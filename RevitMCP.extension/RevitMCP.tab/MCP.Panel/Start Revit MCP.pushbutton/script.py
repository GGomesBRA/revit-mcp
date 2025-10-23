#! python3
from __future__ import annotations

# --- keep your sys.path entries exactly as requested ---
import sys

sys.path.append(r"C:\\Users\\m170488")
sys.path.append(r"C:\\Users\\m170488\\AppData\\Local\\Programs\\Python\\Python312\\python312.zip")
sys.path.append(r"C:\\Users\\m170488\\AppData\\Local\\Programs\\Python\\Python312\\DLLs")
sys.path.append(r"C:\\Users\\m170488\\AppData\\Local\\Programs\\Python\\Python312\\Lib")
sys.path.append(r"C:\\Users\\m170488\\AppData\\Local\\Programs\\Python\\Python312")
sys.path.append(r"C:\\Users\\m170488\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages")
sys.path.append(r"C:\\Users\\m170488\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\win32")
sys.path.append(r"C:\\Users\\m170488\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\win32\\lib")
sys.path.append(r"C:\\Users\\m170488\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\Pythonwin")

# HTTP server bits
import asyncio
import logging
import logging.config
import os
import queue
import socket
import threading
import time
from typing import Any, Dict, Tuple

import Revit.DB as DB
import uvicorn

# MCP
from fastmcp import FastMCP  # keep this import

# pyRevit output
from pyrevit import EXEC_PARAMS, script
from Revit.UI import ExternalEvent, IExternalEventHandler
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse

output = script.get_output()

# ---------------- Logging setup ----------------
LOG_DIR = r"C:\Users\m170488\AppData\Roaming\pyRevit\Extensions\revit_routes.log"
os.makedirs(LOG_DIR, exist_ok=True)
APP_LOG = os.path.join(LOG_DIR, "revit_mcp_app.log")
UVICORN_LOG = os.path.join(LOG_DIR, "revit_mcp_uvicorn.log")

# Prevent uvicorn’s formatter from touching TTY (pyRevit’s ScriptIO has no isatty)
LOG_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "uvicorn_default": {
            "class": "logging.Formatter",
            "fmt": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "access": {
            "class": "logging.Formatter",
            "fmt": "%(asctime)s [ACCESS] %(client_addr)s - \"%(request_line)s\" %(status_code)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "app": {
            "class": "logging.Formatter",
            "fmt": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "uvicorn_file": {
            "class": "logging.FileHandler",
            "filename": UVICORN_LOG,
            "level": "DEBUG",
            "formatter": "uvicorn_default",
            "encoding": "utf-8",
        },
        "uvicorn_access_file": {
            "class": "logging.FileHandler",
            "filename": UVICORN_LOG,
            "level": "INFO",
            "formatter": "access",
            "encoding": "utf-8",
        },
        "app_file": {
            "class": "logging.FileHandler",
            "filename": APP_LOG,
            "level": "DEBUG",
            "formatter": "app",
            "encoding": "utf-8",
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["uvicorn_file"], "level": "DEBUG", "propagate": False},
        "uvicorn.error": {"handlers": ["uvicorn_file"], "level": "DEBUG", "propagate": False},
        "uvicorn.access": {"handlers": ["uvicorn_access_file"], "level": "INFO", "propagate": False},
        "revit_mcp": {"handlers": ["app_file"], "level": "DEBUG", "propagate": False},
        "mcp.server": {"handlers": ["app_file"], "level": "DEBUG", "propagate": False},
    },
}

logging.config.dictConfig(LOG_CONFIG)
log = logging.getLogger("revit_mcp")
log.debug("Log file: %s", UVICORN_LOG)
output.print_md(f"\n\n**Log file:** `{UVICORN_LOG}`\n")

# ---------------- Revit sanity / ExternalEvent ----------------
class _T(IExternalEventHandler):
    __namespace__ = EXEC_PARAMS.exec_id
    def Execute(self, app):
        pass
    def GetName(self):
        return "test"

ev = ExternalEvent.Create(_T())
output.print_md("\n\n**OK: ExternalEvent de teste criado**\n")

# ---------------- Job queue consumed on Revit main thread ----------------
_jobs: "queue.Queue[Tuple[str, Dict[str, Any], Dict[str, Any]]]" = queue.Queue()

class _MCPEventHandler(IExternalEventHandler):
    __namespace__ = EXEC_PARAMS.exec_id
    def GetName(self):
        return "Revit MCP External Event"

    def Execute(self, uiapp):
        try:
            while not _jobs.empty():
                op, args, result = _jobs.get_nowait()
                uidoc = uiapp.ActiveUIDocument
                doc = uidoc.Document

                if op == "draw_detail_line":
                    v = uidoc.ActiveView
                    p1 = DB.XYZ(float(args["x1"]), float(args["y1"]), float(args.get("z1", 0.0)))
                    p2 = DB.XYZ(float(args["x2"]), float(args["y2"]), float(args.get("z2", 0.0)))
                    crv = DB.Line.CreateBound(p1, p2)
                    t = DB.Transaction(doc, "MCP: Detail Line")
                    t.Start()
                    try:
                        el = doc.Create.NewDetailCurve(v, crv)
                        result.update(ok=True, elementId=int(el.Id.IntegerValue))
                    finally:
                        t.Commit()

                elif op == "draw_model_line":
                    v = uidoc.ActiveView
                    p1 = DB.XYZ(float(args["x1"]), float(args["y1"]), float(args["z1"]))
                    p2 = DB.XYZ(float(args["x2"]), float(args["y2"]), float(args["z2"]))
                    crv = DB.Line.CreateBound(p1, p2)
                    sp = v.SketchPlane
                    if sp is None:
                        plane = DB.Plane.CreateByNormalAndOrigin(v.ViewDirection, v.Origin)
                        t = DB.Transaction(doc, "MCP: Temp SP")
                        t.Start()
                        try:
                            sp = DB.SketchPlane.Create(doc, plane)
                            v.SketchPlane = sp
                        finally:
                            t.Commit()
                    t2 = DB.Transaction(doc, "MCP: Model Line")
                    t2.Start()
                    try:
                        el = doc.Create.NewModelCurve(crv, sp)
                        result.update(ok=True, elementId=int(el.Id.IntegerValue))
                    finally:
                        t2.Commit()
                else:
                    result.update(ok=False, error="unknown op: " + op)

        except Exception as ex:
            output.print_md(f"**MCP handler error:** `{ex!r}`")
            log.exception("Error in _MCPEventHandler Execute")

_handler = _MCPEventHandler()
_event = ExternalEvent.Create(_handler)

def _call_revit(op: str, **kwargs) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    _jobs.put((op, kwargs, result))
    _event.Raise()
    for _ in range(400):  # ~20s @ 50ms
        if result:
            return result
        time.sleep(0.05)
    return {"ok": False, "error": "timeout"}

# ---------------- MCP server + tools ----------------
mcp = FastMCP(
    name="Revit-MCP",
    stateless_http=True,
    # json_response=True,  # uncomment to force JSON (no SSE) during debugging
)

@mcp.tool()
def draw_detail_line(x1: float, y1: float, x2: float, y2: float, z1: float = 0.0, z2: float = 0.0) -> dict:
    """Draw a detail line in the active view."""
    return _call_revit("draw_detail_line", x1=x1, y1=y1, z1=z1, x2=x2, y2=y2, z2=z2)

@mcp.tool()
def draw_model_line(x1: float, y1: float, z1: float, x2: float, y2: float, z2: float) -> dict:
    """Draw a model line (3D space)."""
    return _call_revit("draw_model_line", x1=x1, y1=y1, z1=z1, x2=x2, y2=y2, z2=z2)

# Build ASGI app hierarchy: mount MCP app at /mcp, add health + access logging middleware
mcp_app = mcp.http_app()  # FastMCP ASGI app
root_app = Starlette()

@root_app.middleware("http")
async def access_log_mw(request: Request, call_next):
    # log a few headers useful for MCP debugging
    log.debug(
        "REQ %s %s | Remote=%s | Accept=%s | Content-Type=%s | Mcp-Session-Id=%s",
        request.method, request.url.path,
        request.client.host if request.client else "?",
        request.headers.get("accept"),
        request.headers.get("content-type"),
        request.headers.get("mcp-session-id"),
    )
    resp = await call_next(request)
    return resp

@root_app.route("/mcp/health", methods=["GET"])
async def health(_req: Request):
    return PlainTextResponse("OK", status_code=200)

# mount MCP at /mcp (so GET /mcp (SSE) and POST /mcp both work)
root_app.mount("/mcp", mcp_app)

# ---------------- Uvicorn runner (non-daemon thread) ----------------
HOST = "0.0.0.0"     # <— bind all IPv4 interfaces
PORT = 8802
HEALTH_CHECK_HOST = "127.0.0.1"  # always probe via loopback

def _candidate_ips() -> list[str]:
    """Return non-loopback IPv4s for display."""
    ips = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, family=socket.AF_INET, type=socket.SOCK_STREAM):
            addr = info[4][0]
            if not addr.startswith("127."):
                ips.add(addr)
    except Exception:
        pass
    # UDP connect trick to discover primary egress IP (no packets sent)
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("192.0.2.1", 80))  # TEST-NET-1, non-routable; just for local binding
        ips.add(s.getsockname()[0])
        s.close()
    except Exception:
        pass
    return sorted(ips)

def _serve_uvicorn():
    try:
        config = uvicorn.Config(
            app=root_app,
            host=HOST,
            port=PORT,
            loop="asyncio",
            lifespan="on",
            access_log=True,
            log_config=LOG_CONFIG,  # safe: file-only logging; no isatty
        )
        server = uvicorn.Server(config)
        # Don’t install SIG handlers in a worker thread
        server.install_signal_handlers = lambda: None
        asyncio.set_event_loop(asyncio.new_event_loop())
        asyncio.get_event_loop().run_until_complete(server.serve())
    except Exception as e:
        output.print_md(f"\n\n**Thread Revit-MCP-HTTP crashed:**```{e}```\n")
        log.exception("HTTP server crashed")

# Start once per Revit session
if not getattr(script, "revit_mcp_started", False):
    t = threading.Thread(target=_serve_uvicorn, name="Revit-MCP-HTTP", daemon=False)
    t.start()
    setattr(script, "revit_mcp_started", True)

    output.print_md(f"\n\n**Revit MCP server** iniciando em `http://{HOST}:{PORT}/mcp/`\n")
    output.print_md(f"\n\n**Log detalhado em:** `{UVICORN_LOG}`\n")

    # quick local health probe so you immediately see success/failure in pyRevit panel
    import urllib.request
    health_url = f"http://{HEALTH_CHECK_HOST}:{PORT}/mcp/health"
    try:
        with urllib.request.urlopen(health_url, timeout=3) as resp:
            if resp.status == 200:
                output.print_md(f"\n\n**Health probe OK (200)** em `{health_url}`\n")
            else:
                output.print_md(f"\n\nHealth probe retornou status {resp.status} em `{health_url}`\n")
    except Exception:
        output.print_md(f"\n\n**Health probe falhou** (sem resposta em `{health_url}`)\n")

    # Print candidate LAN URLs for convenience
    try:
        lan_ips = _candidate_ips()
        if lan_ips:
            lines = [f"- `http://{ip}:{PORT}/mcp/`" for ip in lan_ips]
            output.print_md("**LAN endpoints (teste pelo navegador ou MCP Inspector):**\n" + "\n".join(lines))
        else:
            output.print_md("_Não foi possível detectar IPs LAN automaticamente. Use `ipconfig` e tente `http://<seu-ip>:{}/mcp/`_".format(PORT))
    except Exception:
        pass

else:
    output.print_md("_Revit MCP já estava em execução._")
