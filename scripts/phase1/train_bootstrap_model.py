#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from bootstrap_arranger.training import load_training_config, train_overfit


def main() -> int:
    parser = argparse.ArgumentParser(description="Train the Phase 1 bootstrap adapter over the current bundles.")
    parser.add_argument("--config", required=True, help="Path to the phase1 bootstrap YAML config.")
    args = parser.parse_args()

    config = load_training_config(Path(args.config).resolve())
    checkpoint_path = train_overfit(config)
    print(f"saved bootstrap adapter to {checkpoint_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
