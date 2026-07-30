from __future__ import annotations

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]

CANONICAL_PICOGEN_ROOT = REPO_ROOT / "third_party" / "picogen2"
CANONICAL_HOMR_ROOT = REPO_ROOT / "third_party" / "homr"
CANONICAL_RAW_ASSET_ROOT = REPO_ROOT / "assets" / "raw"


def _resolve_first_existing(candidates: list[Path | None], label: str) -> Path:
    for candidate in candidates:
        if candidate is not None and candidate.exists():
            return candidate.resolve()
    attempted = ", ".join(str(candidate) for candidate in candidates if candidate is not None)
    raise FileNotFoundError(f"Could not resolve {label}. Tried: {attempted}")


def resolve_picogen_root(explicit_root: Path | None = None) -> Path:
    return _resolve_first_existing(
        [explicit_root, CANONICAL_PICOGEN_ROOT],
        "PiCoGen root",
    )


def resolve_homr_root(explicit_root: Path | None = None) -> Path:
    return _resolve_first_existing(
        [explicit_root, CANONICAL_HOMR_ROOT],
        "HOMR root",
    )
