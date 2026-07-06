"""Data processing modules for PiCoGen2.

Core modules:
- download: Download utilities (ytdlp_download, download_pop2piano)

Optional modules (require `pip install picogen2[full]`):
- preprocess: Data preprocessing (requires mirtoolkit)
- dataset: PyTorch dataset (requires librosa)
- align: Audio alignment (requires synctoolbox, pretty_midi)
"""

from .download import pop2piano as download_pop2piano
from .download import ytdlp_download

# Task constants (no optional dependencies)
TASK_TRANS = "transcribe"
TASK_BEAT = "beat"
TASK_SHEETSAGE = "sheetsage"
TASK_ALIGN = "align"

__all__ = [
    # download
    "download_pop2piano",
    "ytdlp_download",
    # task constants
    "TASK_TRANS",
    "TASK_BEAT",
    "TASK_SHEETSAGE",
    "TASK_ALIGN",
]


def __getattr__(name):
    """Lazy loading for modules with optional dependencies."""
    if name == "preprocess_pop2piano":
        from .preprocess import pop2piano
        return pop2piano
    if name == "save_delayed_song":
        from .align import save_delayed_song
        return save_delayed_song
    if name == "PiCoGenDataset":
        from .dataset import PiCoGenDataset
        return PiCoGenDataset
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
