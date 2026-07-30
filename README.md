# AI Piano Arranger

This repo is the Phase 1 bootstrap workspace for a personal JPOP piano
arrangement system.

## Start Here

- `Goal.md`: active direction and project constraints
- `research.md`: recent research and open-source references
- `docs/architecture.md`: current system design
- `docs/phase1-bootstrap-runbook.md`: how to run the current pipeline

## Top-Level Map

- `assets/raw/`: user-collected source songs, sheet PDFs, and clean piano renders
- `dataset/`: normalized bundles, manifests, reports, and templates
- `bootstrap_arranger/`: repo-owned training and data pipeline code
- `scripts/phase1/`: command-line entrypoints for data prep and training
- `configs/phase1/`: smoke and overfit configs
- `models/`: local model weights
- `checkpoints/phase1/`: local experiment outputs
- `third_party/`: external dependencies kept in-tree (`picogen2`, `homr`)
- `docs/`: architecture, runbooks, and archived earlier plans
- `tests/`: focused regression tests for the Phase 1 stack

## Working Rule

Root-level clutter is intentionally kept small. New material should usually go
into one of the directories above instead of creating new top-level folders.
