# Phase 1 Dataset

This dataset is the personal-scale bootstrap corpus for one JPOP singer.

- Target songs: 24
- Minimum songs to exit Phase 1: 20
- Stretch ceiling: 30
- Active pilot singer: ヨルシカ
- Current normalized local candidates: 15
- Current complete tri-view songs: 3
- Core assets per song: source audio, score PDF, clean piano render, metadata, QC
- Optional enrichment: editable score, derived MIDI

## Bootstrap note

During this bootstrap stage, the immutable source assets live canonically under `assets/raw/songs/`, `assets/raw/sheets/`, and `assets/raw/piano_mp3/`.
Reference bundles under `dataset/bundles/` may symlink back to those assets while normalizing the clean piano render to `piano_clean.wav` inside each bundle.
