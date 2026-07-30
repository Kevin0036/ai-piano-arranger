# Phase 1 Bootstrap Runbook

This document captures the current minimum runnable pipeline for the Phase 1
bootstrap experiment.

## Environment

- Conda env: `picogen2`
- GPU: NVIDIA RTX 3080
- CUDA validation:
  - `torch.cuda.is_available() == True`
  - `onnxruntime-gpu` exposes `CUDAExecutionProvider`

## Canonical Layout

- Raw original songs: `assets/raw/songs/`
- Raw piano sheets: `assets/raw/sheets/`
- Raw clean piano renders: `assets/raw/piano_mp3/`
- PiCoGen2 source: `third_party/picogen2/`
- HOMR source: `third_party/homr/`
- Bundle dataset: `dataset/bundles/`

## Configs

- Main Phase 1 config:
  `configs/phase1/bootstrap_mert_overfit.yaml`
- End-to-end decoder smoke config:
  `configs/phase1/bootstrap_mert_decoder_smoke.yaml`
- Pretrained decoder smoke config:
  `configs/phase1/bootstrap_mert_decoder_pretrained_smoke.yaml`

## Step 1: Extract MERT Features

```bash
env PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True \
  /home/ithan/anaconda3/bin/conda run -n picogen2 \
  python scripts/phase1/extract_bootstrap_features.py \
  --config configs/phase1/bootstrap_mert_overfit.yaml
```

Outputs per song:

- `dataset/bundles/<song_id>/features/source_mert_v1_330m.pt`
- `dataset/bundles/<song_id>/features/render_mert_v1_330m.pt`

Notes:

- MERT loading uses `trust_remote_code=True`.
- Long audio is encoded in chunks to avoid GPU OOM on the 3080.

## Step 2: Run HOMR and Build Symbolic Targets

```bash
/home/ithan/anaconda3/bin/conda run -n picogen2 \
  python scripts/phase1/run_homr_trial.py \
  --config configs/phase1/bootstrap_mert_overfit.yaml
```

Outputs per song:

- `dataset/bundles/<song_id>/arrangement/symbolic/homr_combined.musicxml`
- `dataset/bundles/<song_id>/arrangement/symbolic/homr.mid`
- `dataset/bundles/<song_id>/arrangement/symbolic/picogen_tokens.json`
- `dataset/bundles/<song_id>/arrangement/symbolic/homr_review.json`

Review helper:

- `homr_review.json` records page image paths, page-level MusicXML files,
  measure counts, token counts, and MIDI instrument counts.

## Step 3: Run Decoder Smoke Training

```bash
/home/ithan/anaconda3/bin/conda run -n picogen2 \
  python scripts/phase1/train_bootstrap_model.py \
  --config configs/phase1/bootstrap_mert_decoder_smoke.yaml
```

Current smoke mode:

- Uses real MERT features from Step 1
- Uses HOMR-generated `picogen_tokens.json` as supervision
- Enables the PiCoGen2 decoder path
- Uses random decoder initialization to verify the training stack before the
  large pretrained checkpoint is wired in

Outputs:

- `checkpoints/phase1/bootstrap_mert_decoder_smoke/bootstrap_adapter.pt`
- `checkpoints/phase1/bootstrap_mert_decoder_smoke/history.json`

## Current Verified Result

The 3-song bootstrap sample has already completed the full minimum path:

1. MERT feature extraction
2. HOMR MusicXML and MIDI conversion
3. PiCoGen2 decoder smoke training

The first smoke run produced:

```json
[
  {
    "epoch": 1.0,
    "loss": 6.8832831382751465,
    "decoder_loss": 6.421493212381999
  }
]
```

## Next Step

After the official PiCoGen2 checkpoint finishes downloading, switch the decoder
config from random init to pretrained weights and run:

```bash
/home/ithan/anaconda3/bin/conda run -n picogen2 \
  python scripts/phase1/train_bootstrap_model.py \
  --config configs/phase1/bootstrap_mert_decoder_pretrained_smoke.yaml
```
