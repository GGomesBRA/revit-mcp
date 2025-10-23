# -*- coding: utf-8 -*-
import logging
import traceback
from datetime import datetime

from pyrevit import DB, revit, routes

LOG_FILE = r"C:\Users\m170488\AppData\Roaming\pyRevit\Extensions\revit_routes.log"

logger = logging.getLogger("revit_mcp.routes")

# IronPython 2.7 compatibility
try:
    unicode  # type: ignore
except NameError:
    # Python 3
    unicode = str  # type: ignore

# Check if we have .NET System.String
try:
    import System  # type: ignore
    DotNetString = System.String  # type: ignore
except Exception:
    DotNetString = None


def _write_to_log(message):
    """Direct file write - most reliable way to log in IronPython."""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        with open(LOG_FILE, "a") as f:
            f.write("[%s] %s\n" % (timestamp, message))
            f.flush()
    except Exception:
        pass  # Nothing we can do if logging fails


def _sanitize_for_json(obj):
    """Recursively sanitize data to be JSON-safe (UTF-8 encoded strings for pyRevit)."""
    # _write_to_log("Sanitizing data: %s" % str(obj))
    try:
        # Simple types - return as-is
        if obj is None or isinstance(obj, (bool, int, float)):
            return obj
        
        # Handle strings - convert to UTF-8 encoded str (bytes in IronPython)
        if isinstance(obj, (str, unicode)):  # type: ignore
            try:
                # If it's unicode, encode to UTF-8 bytes
                if isinstance(obj, unicode):  # type: ignore
                    return obj.encode('utf-8')
                # If it's already str (bytes), return as-is
                return obj
            except Exception:
                # Fallback: return as-is
                return obj
        
        # Handle .NET strings - convert to UTF-8 encoded str
        if DotNetString and isinstance(obj, DotNetString):
            try:
                u = unicode(obj)  # type: ignore
                return u.encode('utf-8')
            except Exception:
                return obj
        
        # Handle collections recursively
        if isinstance(obj, dict):
            return {_sanitize_for_json(k): _sanitize_for_json(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [_sanitize_for_json(item) for item in obj]
        
        # For anything else, try to convert to UTF-8 string
        try:
            u = unicode(obj)  # type: ignore
            return u.encode('utf-8')
        except Exception:
            return obj
    except Exception as e:
        _write_to_log("ERROR in _sanitize_for_json: %s" % str(e))
        # Return object as-is on error
        return obj


def ok(data):
    """Return successful response with UTF-8 safe data."""
    _write_to_log("ok() [called with data: %s]" % str(data))
    try:
        # Always sanitize to handle Unicode properly
        safe_data = _sanitize_for_json(data)
        _write_to_log("ok() [after sanitization: %s]" % str(safe_data))
        return routes.make_response(data=safe_data, status=200)
    except Exception as e:
        _write_to_log("ERROR in ok(): %s" % str(e))
        import traceback
        _write_to_log("Traceback: %s" % traceback.format_exc())
        return err(e)


def log_api_call(method, endpoint, payload=None):
    """Log API calls."""
    msg = "API CALL %s %s" % (method, endpoint)
    _write_to_log(msg)


def err(message, status=500):
    """Log error and return error response.
    
    This is the core error logging function. It will:
    1. Write the full error with traceback to the log file
    2. Return a safe error response to the client
    """
    # Build error message with traceback if it's an exception
    error_msg = "ERROR: %s" % str(message)
    
    if isinstance(message, Exception):
        try:
            tb = traceback.format_exc()
            error_msg = "ERROR (Exception): %s\nTraceback:\n%s" % (str(message), tb)
        except Exception:
            error_msg = "ERROR (Exception): %s" % str(message)
    
    # Always write to log file
    _write_to_log(error_msg)
    
    # Try to also use the logger (but don't fail if it doesn't work)
    try:
        if isinstance(message, Exception):
            logger.exception("Unhandled exception: %s", message)
        else:
            logger.error("API error: %s", message)
    except Exception:
        pass
    
    # Return simple, safe error response
    payload = {"ok": False, "error": str(message)}
    return routes.make_response(data=payload, status=status)

class Tx(object):
    def __init__(self, doc, name):
        self.doc = doc
        self.name = name
        self._t = None
    def __enter__(self):
        self._t = DB.Transaction(self.doc, self.name)
        self._t.Start()
        return self._t
    def __exit__(self, exc_type, exc, tb):
        if exc_type is None:
            self._t.Commit()
        else:
            if self._t.HasStarted() and not self._t.HasEnded():
                self._t.RollBack()

def find_level_by_name(doc, name):
    it = DB.FilteredElementCollector(doc).OfClass(DB.Level)
    # Ensure name is unicode for proper comparison with .NET strings
    if isinstance(name, str):
        try:
            name = name.decode('utf-8')
        except Exception:
            pass  # Already decoded or not UTF-8
    for lvl in it:
        # Compare as unicode
        lvl_name = lvl.Name
        if isinstance(lvl_name, str):
            try:
                lvl_name = lvl_name.decode('utf-8')
            except Exception:
                pass
        if lvl_name == name:
            return lvl
    return None

def find_type_by_name(doc, bic, typename):
    it = DB.FilteredElementCollector(doc)\
        .OfCategory(bic)\
        .WhereElementIsElementType()
    # Ensure typename is unicode for proper comparison
    if isinstance(typename, str):
        try:
            typename = typename.decode('utf-8')
        except Exception:
            pass
    for t in it:
        fam_name = t.FamilyName
        type_name = t.Name
        # Decode if needed
        if isinstance(fam_name, str):
            try:
                fam_name = fam_name.decode('utf-8')
            except Exception:
                pass
        if isinstance(type_name, str):
            try:
                type_name = type_name.decode('utf-8')
            except Exception:
                pass
        if fam_name == typename or type_name == typename:
            return t
    return None

def find_rebar_bar_type_by_name(doc, name):
    if isinstance(name, str):
        try:
            name = name.decode('utf-8')
        except Exception:
            pass
    it = DB.FilteredElementCollector(doc).OfClass(DB.Structure.RebarBarType)
    for t in it:
        nm = t.Name
        if isinstance(nm, str):
            try:
                nm = nm.decode('utf-8')
            except Exception:
                pass
        if nm == name:
            return t
    return None

def find_rebar_shape_by_name(doc, name):
    if isinstance(name, str):
        try:
            name = name.decode('utf-8')
        except Exception:
            pass
    it = DB.FilteredElementCollector(doc).OfClass(DB.Structure.RebarShape)
    for s in it:
        nm = s.Name
        if isinstance(nm, str):
            try:
                nm = nm.decode('utf-8')
            except Exception:
                pass
        if nm == name:
            return s
    return None

def ensure_plane_for_line(p1, p2):
    line_dir = p2 - p1
    seed = DB.XYZ.BasisZ
    if (line_dir.CrossProduct(seed)).GetLength() < 1e-9:
        seed = DB.XYZ.BasisX
    p3 = DB.XYZ(p1.X + seed.X, p1.Y + seed.Y, p1.Z + seed.Z)
    return DB.Plane.CreateByThreePoints(p1, p2, p3)

def active_uidoc():
    return revit.uidoc

def active_doc():
    return revit.doc

def view_allows_detail_curves(view):
    if view is None:
        return False
    try:
        vt = view.ViewType
        disallowed = (
            DB.ViewType.ThreeD,
            DB.ViewType.DrawingSheet,
            DB.ViewType.Schedule,
            DB.ViewType.ProjectBrowser,
            DB.ViewType.Internal,
            DB.ViewType.Legend,
        )
        if vt in disallowed:
            return False
        # Disallow perspective 3D views explicitly
        if isinstance(view, DB.View3D) and getattr(view, "IsPerspective", False):
            return False
        # Disallow view templates
        if getattr(view, "IsTemplate", False):
            return False
        return True
    except Exception:
        return False

def get_detail_view_validation(view):
    if view is None:
        return {"canDrawDetailLine": False, "reason": "No active view", "viewType": None}
    vt_str = str(getattr(view, "ViewType", None))
    allowed = view_allows_detail_curves(view)
    if allowed:
        return {"canDrawDetailLine": True, "reason": None, "viewType": vt_str}
    reason = "Active view does not support detail lines (type: %s)" % vt_str
    try:
        if getattr(view, "IsTemplate", False):
            reason = "Active view is a template"
        elif isinstance(view, DB.View3D) and getattr(view, "IsPerspective", False):
            reason = "Perspective 3D views do not support detail lines"
        elif getattr(view, "ViewType", None) == DB.ViewType.DrawingSheet:
            reason = "Sheets do not support detail lines"
        elif getattr(view, "ViewType", None) == DB.ViewType.Schedule:
            reason = "Schedules do not support detail lines"
        elif getattr(view, "ViewType", None) == DB.ViewType.ThreeD:
            reason = "3D views do not support detail lines"
        elif getattr(view, "ViewType", None) == DB.ViewType.Legend:
            reason = "Legends do not support detail lines"
    except Exception:
        pass
    return {"canDrawDetailLine": False, "reason": reason, "viewType": vt_str}

def _deprecated_log_request(func):
    # Kept to avoid accidental import breaks; prefer the top decorator above
    return func
