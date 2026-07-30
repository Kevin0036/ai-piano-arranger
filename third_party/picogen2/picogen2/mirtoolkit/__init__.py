"""Music Information Retrieval toolkit for PiCoGen2.

This module requires optional dependencies. Install with:
    pip install picogen2[full]

Available submodules (lazily loaded):
- beat_this: Beat detection using CPJKU's beat_this
- sheetsage: Lead sheet transcription using SheetSage
- transcription: Piano transcription using ByteDance's model
"""

import importlib
import sys

__all__ = [
    "beat_this",
    "sheetsage",
    "transcription",
]

_SUBMODULES = {"beat_this", "sheetsage", "transcription"}


def __getattr__(name):
    """Lazy loading for submodules with optional dependencies."""
    if name in _SUBMODULES:
        module = importlib.import_module(f".{name}", __name__)
        # Cache in sys.modules to prevent re-importing
        globals()[name] = module
        return module
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
