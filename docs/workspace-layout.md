# Workspace Layout

## Canonical Top-Level Layout

- `README.md`: root entrypoint and quick map of the repo
- `Goal.md`: active product and technical direction
- `research.md`: recent external research and open-source references
- `assets/raw/`
  - `songs/`: original JPOP source audio collected by the user
  - `sheets/`: arrangement score PDFs collected by the user
  - `piano_mp3/`: clean piano arrangement renders collected by the user
- `dataset/bundles/`: normalized training bundles derived from the raw asset pool
- `models/`: local model weights such as MERT
- `third_party/`
  - `picogen2/`: frozen generator baseline
  - `homr/`: OMR stack for score-to-symbolic conversion
- `bootstrap_arranger/`: Phase 1 bootstrap training code owned by this repo
- `scripts/phase1/`: data prep, feature extraction, OMR, and training entrypoints
- `configs/phase1/`: runtime configs for smoke runs and overfit runs
- `checkpoints/phase1/`: locally produced outputs and model checkpoints

## Cleanup Notes

- Legacy top-level compatibility symlinks have been removed.
- All new code, manifests, and docs should use the canonical paths under `assets/raw/` and `third_party/`.
- Historical design material lives under `docs/archive/`.
