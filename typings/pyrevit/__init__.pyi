from typing import Any

from Revit import DB as DB
from Revit import UI as UI

from . import Analysis as Analysis
from . import Architecture as Architecture
from . import Electrical as Electrical
from . import ExtensibleStorage as ExtensibleStorage
from . import Mechanical as Mechanical
from . import Plumbing as Plumbing
from . import Structure as Structure
from . import Visual as Visual

# reexporta pyrevit.routes como submódulo
from . import routes as routes

class _RevitCtx:
    doc: DB.Document
    uidoc: UI.UIDocument
revit: _RevitCtx

# módulos utilitários mais comuns (placeholders – só p/ IntelliSense)
HOST_APP: Any
script: Any
forms: Any
framework: Any


__all__ = ["DB", "UI", "revit", "routes", "HOST_APP", "script", "forms", "framework", "Structure", "Architecture", "Analysis",
        "Mechanical", "Electrical",  "Plumbing", "Visual", "ExtensibleStorage"
    ]
