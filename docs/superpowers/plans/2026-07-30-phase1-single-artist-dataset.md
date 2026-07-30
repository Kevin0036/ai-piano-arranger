# Phase 1 Single-Artist Dataset Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a personal-scale Phase 1 dataset for one JPOP singer with 20-30 songs, preserving source audio, score-native assets, clean piano renders, and QC metadata well enough to start Phase 2 encoder benchmarking without recollecting the corpus.

**Architecture:** Phase 1 is a bundle-first data project, not a model-training sprint. The dataset should treat original song audio, arrangement score assets, and rendered piano audio as first-class views inside `ArrangementBundle`, with optional MIDI only as a derived extra. Collection is manual-first and quality-first, with light automation only where it reduces repeated labor for a personal user.

**Tech Stack:** Markdown, CSV, YAML, Python 3.10, `ffmpeg`, MuseScore CLI, Poppler/ImageMagick-style PDF page export tools, optional `music21` / `pretty_midi` for validation helpers

---

## Scope Lock

### Personal-scale target

- Recommended target: `24` songs
- Hard minimum to exit Phase 1: `20` songs
- Stretch ceiling: `30` songs
- Recommended artist scope: `one JPOP singer`, not a mixed-artist playlist
- Recommended mean duration: around `180` seconds per song
- Expected total source-audio duration: `60-90 minutes`

### What this dataset size is enough for

With `MERT`, `MuQ`, or `MusicFM` as pretrained encoders, `20-30` songs is enough for:

- singer-specific corpus bootstrapping
- representation extraction and indexing
- source-to-arrangement retrieval experiments
- early alignment experiments
- small-scale conditioning or adapter experiments

This dataset size is **not** enough to claim:

- robust universal style transfer
- saturated personalization quality
- full generalization across arrangers, genres, and difficulty bands

So the Phase 1 success criterion is: **visible signal and clean infrastructure**, not “final model quality”.

### Phase 1 deliverables

By the end of Phase 1, the repo should contain:

1. a stable `ArrangementBundle` folder convention
2. a manifest for one singer corpus
3. per-song metadata and QC reports
4. clean rendered piano audio for the active set
5. at least one validated core dataset split ready for Phase 2

## File Structure Map

### New files to create during execution

- `dataset/README.md`
- `dataset/manifests/phase1_jpop_single_artist.csv`
- `dataset/templates/metadata.yaml`
- `dataset/templates/qc_report.yaml`
- `dataset/reports/phase1_summary.md`
- `schemas/arrangement_bundle.schema.yaml`
- `scripts/phase1/init_bundle.py`
- `scripts/phase1/render_score.sh`
- `scripts/phase1/export_score_pages.sh`
- `scripts/phase1/validate_bundle.py`
- `scripts/phase1/build_phase1_report.py`
- `tests/phase1/test_validate_bundle.py`

### Existing files to modify during execution

- `Goal.md`
- `docs/architecture.md`

### Dataset directories to create during execution

- `dataset/bundles/song_001/`
- `dataset/bundles/song_002/`
- `dataset/bundles/song_003/`
- `dataset/bundles/song_004/`
- `dataset/bundles/song_005/`
- `dataset/bundles/song_006/`
- `dataset/bundles/song_007/`
- `dataset/bundles/song_008/`
- `dataset/bundles/song_009/`
- `dataset/bundles/song_010/`
- `dataset/bundles/song_011/`
- `dataset/bundles/song_012/`
- `dataset/bundles/song_013/`
- `dataset/bundles/song_014/`
- `dataset/bundles/song_015/`
- `dataset/bundles/song_016/`
- `dataset/bundles/song_017/`
- `dataset/bundles/song_018/`
- `dataset/bundles/song_019/`
- `dataset/bundles/song_020/`
- `dataset/bundles/song_021/`
- `dataset/bundles/song_022/`
- `dataset/bundles/song_023/`
- `dataset/bundles/song_024/`

`song_025` to `song_030` are stretch slots only if the core `24` are already valid.

## Quality Tiers

### Gold

Required:

- source song audio is complete and version-matched
- arrangement score PDF exists and is readable
- clean piano render exists
- page images exported
- metadata complete
- QC report complete

Optional but preferred:

- editable score source (`.musicxml`, `.mscz`, or equivalent)
- derived MIDI

### Silver

Required:

- source song audio exists
- arrangement score PDF exists
- clean piano render exists
- metadata complete

Missing one of:

- page images
- editable score
- full QC confidence

Silver bundles may stay in the active set if they are musically valid.

### Hold

Any of the following:

- arrangement version cannot be matched to the source song
- score PDF is incomplete or unreadable
- render audio is not actually derived from the same score
- metadata provenance is unclear

Hold bundles are excluded from Phase 2.

## Task 1: Freeze Phase 1 Scope And Manifest Format

**Files:**
- Create: `dataset/README.md`
- Create: `dataset/manifests/phase1_jpop_single_artist.csv`
- Modify: `Goal.md`

- [ ] **Step 1: Write the Phase 1 scope note in `dataset/README.md`**

```md
# Phase 1 Dataset

This dataset is the personal-scale bootstrap corpus for one JPOP singer.

- Target songs: 24
- Minimum songs to exit Phase 1: 20
- Stretch ceiling: 30
- Core assets per song: source audio, score PDF, clean piano render, metadata, QC
- Optional enrichment: editable score, derived MIDI
```

- [ ] **Step 2: Create the manifest header**

Write this header to `dataset/manifests/phase1_jpop_single_artist.csv`:

```csv
song_id,singer,track_title,source_audio_path,score_pdf_path,editable_score_path,render_audio_path,optional_midi_path,arranger,source_duration_sec,score_pages,target_tier,status,version_match,qc_grade,notes
```

- [ ] **Step 3: Add the first 30 rows with empty file paths but fixed song IDs**

Use rows `song_001` through `song_030`, one row per candidate track.  
Initial values:

```csv
song_001,,,,,,,,,,Gold,candidate,unknown,unknown,
song_002,,,,,,,,,,Gold,candidate,unknown,unknown,
song_003,,,,,,,,,,Gold,candidate,unknown,unknown,
```

- [ ] **Step 4: Verify the scope change is reflected in the main plan**

Run:

```bash
rg -n "20-30|24" Goal.md dataset/README.md dataset/manifests/phase1_jpop_single_artist.csv
```

Expected:
- `Goal.md` mentions the `20-30` song range and the `24` song recommendation
- `dataset/README.md` and the manifest reflect the same counts

- [ ] **Step 5: Commit**

```bash
git add Goal.md dataset/README.md dataset/manifests/phase1_jpop_single_artist.csv
git commit -m "docs: lock phase1 single-artist dataset scope"
```

## Task 2: Define The Canonical Bundle Schema And QC Templates

**Files:**
- Create: `schemas/arrangement_bundle.schema.yaml`
- Create: `dataset/templates/metadata.yaml`
- Create: `dataset/templates/qc_report.yaml`
- Modify: `dataset/README.md`

- [ ] **Step 1: Write the bundle schema**

Create `schemas/arrangement_bundle.schema.yaml`:

```yaml
bundle_version: 1
required_paths:
  - source/song_audio.mp3
  - source/metadata.yaml
  - arrangement/score/source.pdf
  - arrangement/render/piano_clean.wav
  - qc/quality_report.yaml
required_metadata:
  - song_id
  - singer
  - track_title
  - arranger
  - source_duration_sec
  - version_match
  - target_tier
optional_paths:
  - arrangement/score/master.musicxml
  - arrangement/score/pages
  - arrangement/symbolic/optional.mid
```

- [ ] **Step 2: Write the metadata template**

Create `dataset/templates/metadata.yaml`:

```yaml
song_id: song_001
singer: ""
track_title: ""
arranger: ""
source_duration_sec: 0
source_release: ""
arrangement_source: ""
version_match: unknown
target_tier: Gold
transpose_semitones: 0
tempo_notes: ""
notes: ""
```

- [ ] **Step 3: Write the QC template**

Create `dataset/templates/qc_report.yaml`:

```yaml
song_id: song_001
asset_check:
  source_audio: pending
  score_pdf: pending
  piano_render: pending
  page_images: pending
  optional_midi: missing
alignment_check:
  intro_match: pending
  middle_match: pending
  ending_match: pending
grade: unknown
blockers: []
reviewer_notes: ""
```

- [ ] **Step 4: Add the bundle rules to `dataset/README.md`**

Append:

```md
## Bundle Acceptance

- Gold requires source audio, readable score PDF, clean piano render, page export, metadata, and QC.
- Silver may miss editable score or page export, but not source audio, score PDF, or render audio.
- Hold is excluded from training and benchmark work.
```

- [ ] **Step 5: Commit**

```bash
git add schemas/arrangement_bundle.schema.yaml dataset/templates/metadata.yaml dataset/templates/qc_report.yaml dataset/README.md
git commit -m "docs: define arrangement bundle schema and qc templates"
```

## Task 3: Build Lightweight Phase 1 Tooling

**Files:**
- Create: `scripts/phase1/init_bundle.py`
- Create: `scripts/phase1/render_score.sh`
- Create: `scripts/phase1/export_score_pages.sh`
- Create: `scripts/phase1/validate_bundle.py`
- Create: `tests/phase1/test_validate_bundle.py`

- [ ] **Step 1: Write the failing validator test**

Create `tests/phase1/test_validate_bundle.py`:

```python
from pathlib import Path

from scripts.phase1.validate_bundle import validate_bundle


def test_validate_bundle_requires_source_pdf_render_and_qc(tmp_path: Path):
    bundle = tmp_path / "song_001"
    (bundle / "source").mkdir(parents=True)
    (bundle / "arrangement" / "score").mkdir(parents=True)
    (bundle / "arrangement" / "render").mkdir(parents=True)
    (bundle / "qc").mkdir(parents=True)

    result = validate_bundle(bundle)

    assert result.ok is False
    assert "source/song_audio.mp3" in result.missing_paths
    assert "source/metadata.yaml" in result.missing_paths
    assert "arrangement/score/source.pdf" in result.missing_paths
    assert "arrangement/render/piano_clean.wav" in result.missing_paths
    assert "qc/quality_report.yaml" in result.missing_paths
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
pytest tests/phase1/test_validate_bundle.py -v
```

Expected:
- import error or missing module failure for `scripts.phase1.validate_bundle`

- [ ] **Step 3: Write minimal bundle initialization and validation logic**

Create `scripts/phase1/validate_bundle.py` around this shape:

```python
from dataclasses import dataclass
from pathlib import Path


REQUIRED_PATHS = [
    "source/song_audio.mp3",
    "source/metadata.yaml",
    "arrangement/score/source.pdf",
    "arrangement/render/piano_clean.wav",
    "qc/quality_report.yaml",
]


@dataclass
class ValidationResult:
    ok: bool
    missing_paths: list[str]


def validate_bundle(bundle_root: Path) -> ValidationResult:
    missing = [path for path in REQUIRED_PATHS if not (bundle_root / path).exists()]
    return ValidationResult(ok=not missing, missing_paths=missing)
```

Create `scripts/phase1/init_bundle.py` with a CLI that creates:

```text
source/
arrangement/score/
arrangement/render/
arrangement/symbolic/
qc/
```

- [ ] **Step 4: Add simple shell helpers**

Create `scripts/phase1/render_score.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
musescore "$1" -o "$2"
```

Create `scripts/phase1/export_score_pages.sh`:

```bash
#!/usr/bin/env bash
set -euo pipefail
pdftoppm -png "$1" "$2/page"
```

- [ ] **Step 5: Re-run the validator test**

Run:

```bash
pytest tests/phase1/test_validate_bundle.py -v
```

Expected:
- `PASS`

- [ ] **Step 6: Commit**

```bash
git add scripts/phase1/init_bundle.py scripts/phase1/render_score.sh scripts/phase1/export_score_pages.sh scripts/phase1/validate_bundle.py tests/phase1/test_validate_bundle.py
git commit -m "feat: add phase1 bundle bootstrap tooling"
```

## Task 4: Triage 30 Candidate Songs And Lock The Active 24

**Files:**
- Modify: `dataset/manifests/phase1_jpop_single_artist.csv`
- Create: `dataset/reports/phase1_candidate_review.md`

- [ ] **Step 1: Gather 30 candidate songs before filtering**

Fill `song_001` through `song_030` in the manifest with:
- singer
- track title
- arranger if known
- source duration
- current asset availability

- [ ] **Step 2: Apply the filtering rule**

Keep a song in the active set only if:

- the source song version can be identified exactly
- a matching arrangement score PDF exists
- a piano render can be produced from that same score or is already available

Move everything else to `status=hold`.

- [ ] **Step 3: Lock the active 24**

Set:

- `status=active` for the best `24`
- `status=hold` for the remainder

Target distribution:

- `12-16` Gold candidates
- `8-12` Silver candidates
- `0-6` Hold candidates

- [ ] **Step 4: Write the rejection reasons**

Create `dataset/reports/phase1_candidate_review.md`:

```md
# Phase 1 Candidate Review

## Hold reasons

- source version mismatch
- score PDF unreadable
- arrangement appears incomplete
- render audio could not be reproduced from the score
```

- [ ] **Step 5: Commit**

```bash
git add dataset/manifests/phase1_jpop_single_artist.csv dataset/reports/phase1_candidate_review.md
git commit -m "data: lock phase1 candidate list and active set"
```

## Task 5: Build The First 3 Reference Bundles By Hand

**Files:**
- Create: `dataset/bundles/song_001/`
- Create: `dataset/bundles/song_002/`
- Create: `dataset/bundles/song_003/`
- Modify: `dataset/manifests/phase1_jpop_single_artist.csv`

- [ ] **Step 1: Initialize the three bundle folders**

Run:

```bash
python scripts/phase1/init_bundle.py dataset/bundles/song_001
python scripts/phase1/init_bundle.py dataset/bundles/song_002
python scripts/phase1/init_bundle.py dataset/bundles/song_003
```

Expected:
- each bundle contains `source/`, `arrangement/score/`, `arrangement/render/`, `arrangement/symbolic/`, and `qc/`

- [ ] **Step 2: Populate the minimum required assets**

For each of `song_001` to `song_003`, add:

- `source/song_audio.mp3`
- `source/metadata.yaml`
- `arrangement/score/source.pdf`
- `arrangement/render/piano_clean.wav`
- `qc/quality_report.yaml`

- [ ] **Step 3: Export score pages**

Run:

```bash
mkdir -p dataset/bundles/song_001/arrangement/score/pages
mkdir -p dataset/bundles/song_002/arrangement/score/pages
mkdir -p dataset/bundles/song_003/arrangement/score/pages
scripts/phase1/export_score_pages.sh dataset/bundles/song_001/arrangement/score/source.pdf dataset/bundles/song_001/arrangement/score/pages
scripts/phase1/export_score_pages.sh dataset/bundles/song_002/arrangement/score/source.pdf dataset/bundles/song_002/arrangement/score/pages
scripts/phase1/export_score_pages.sh dataset/bundles/song_003/arrangement/score/source.pdf dataset/bundles/song_003/arrangement/score/pages
```

- [ ] **Step 4: Validate and grade the first three**

Run:

```bash
python scripts/phase1/validate_bundle.py dataset/bundles/song_001
python scripts/phase1/validate_bundle.py dataset/bundles/song_002
python scripts/phase1/validate_bundle.py dataset/bundles/song_003
```

Expected:
- all three return `ok=True`

Then set their manifest rows to:
- `status=validated`
- `version_match=yes`
- `qc_grade=Gold` or `qc_grade=Silver`

- [ ] **Step 5: Time the manual workload**

Record in `dataset/reports/phase1_candidate_review.md`:

- minutes spent per song
- what blocked speed
- whether the current asset standard is still realistic for a single user

If the median setup time is above `45 minutes` per song, reduce the active target from `24` to `20`.

- [ ] **Step 6: Commit**

```bash
git add dataset/bundles/song_001 dataset/bundles/song_002 dataset/bundles/song_003 dataset/manifests/phase1_jpop_single_artist.csv dataset/reports/phase1_candidate_review.md
git commit -m "data: build first three reference arrangement bundles"
```

## Task 6: Expand From 3 To 10 Validated Bundles

**Files:**
- Create: `dataset/bundles/song_004/`
- Create: `dataset/bundles/song_005/`
- Create: `dataset/bundles/song_006/`
- Create: `dataset/bundles/song_007/`
- Create: `dataset/bundles/song_008/`
- Create: `dataset/bundles/song_009/`
- Create: `dataset/bundles/song_010/`
- Modify: `dataset/manifests/phase1_jpop_single_artist.csv`

- [ ] **Step 1: Repeat the reference workflow for seven more songs**

For each of `song_004` through `song_010`:

1. initialize the bundle
2. ingest source audio
3. ingest score PDF
4. render or attach clean piano audio
5. export score pages
6. fill metadata
7. fill QC
8. run validation

- [ ] **Step 2: Enforce the 10-song checkpoint**

At the 10-song mark, the manifest should show:

- at least `7` validated bundles
- at least `5` Gold or strong Silver bundles
- no unresolved `version_match=unknown` rows inside the validated set

- [ ] **Step 3: Stop and review if the checkpoint fails**

If fewer than `7` of the first `10` are valid:

- shrink the active set to the strongest `20`
- downgrade weak candidates to `hold`
- do not proceed to `24+` until the pass rate is fixed

- [ ] **Step 4: Commit**

```bash
git add dataset/bundles/song_004 dataset/bundles/song_005 dataset/bundles/song_006 dataset/bundles/song_007 dataset/bundles/song_008 dataset/bundles/song_009 dataset/bundles/song_010 dataset/manifests/phase1_jpop_single_artist.csv
git commit -m "data: expand phase1 corpus to ten validated bundles"
```

## Task 7: Complete The Core Set And Write The Exit Report

**Files:**
- Create: `scripts/phase1/build_phase1_report.py`
- Create: `dataset/reports/phase1_summary.md`
- Modify: `dataset/manifests/phase1_jpop_single_artist.csv`

- [ ] **Step 1: Finish the core validated set**

Complete validation for `song_011` through `song_024`.

Core exit threshold:

- minimum `20` validated bundles
- recommended `24` validated bundles
- stretch `30` only if the first `24` are already clean

- [ ] **Step 2: Tag enriched bundles**

In the manifest, mark bundles with:

- editable score present
- optional MIDI present
- especially clean alignment confidence

Target enriched subset:

- at least `6`
- recommended `8-10`

These will be the first candidates for Phase 2 alignment and benchmark work.

- [ ] **Step 3: Generate the summary report**

Create `dataset/reports/phase1_summary.md` with:

```md
# Phase 1 Summary

## Totals
- candidate songs:
- active songs:
- validated songs:
- gold:
- silver:
- hold:

## Asset coverage
- source audio coverage:
- score PDF coverage:
- page image coverage:
- clean render coverage:
- editable score coverage:
- optional MIDI coverage:

## Time budget
- median minutes per song:
- total manual hours:

## Recommendation
- proceed to Phase 2 / do not proceed
- if proceed, preferred encoder benchmark order
```

- [ ] **Step 4: Add a tiny report builder**

Create `scripts/phase1/build_phase1_report.py` with a CLI that reads the CSV manifest and prints:

```text
validated=22 gold=11 silver=11 hold=4 editable_score=7 optional_midi=5
```

Use this output to fill `dataset/reports/phase1_summary.md`.

- [ ] **Step 5: Define the exact Phase 1 exit gate**

Phase 1 is complete only if all of the following are true:

- `validated bundles >= 20`
- `clean render coverage == validated bundles`
- `score PDF coverage == validated bundles`
- `version_match=yes` for every validated bundle
- `qc_grade` is not `unknown` for every validated bundle

- [ ] **Step 6: Commit**

```bash
git add scripts/phase1/build_phase1_report.py dataset/reports/phase1_summary.md dataset/manifests/phase1_jpop_single_artist.csv
git commit -m "data: finalize phase1 single-artist dataset and exit report"
```

## Per-Song Checklist

Use this same checklist for every song before marking it `validated`:

- [ ] correct source song version identified
- [ ] arrangement score matches that source version
- [ ] source audio copied into bundle
- [ ] score PDF copied into bundle
- [ ] clean piano render copied or exported into bundle
- [ ] page images exported
- [ ] metadata filled
- [ ] QC report filled
- [ ] validator returns success
- [ ] manifest status changed to `validated`

## Personal User Time Budget

Use this budget to keep Phase 1 realistic:

- target median effort per Gold bundle: `20-35 minutes`
- acceptable median effort per Silver bundle: `15-25 minutes`
- review and QC per song: `5-10 minutes`
- total expected corpus build time for `24` songs: roughly `12-18 hours`

If the work trends above this range, simplify the standard:

1. keep PDF + render + metadata as the minimum viable bundle
2. make editable score and MIDI optional enrichment only
3. cap Phase 1 at `20` songs instead of forcing `24-30`

## Why This Is The Recommended Phase 1 Shape

This plan assumes your judgment is directionally right: for a single singer corpus, `20` songs of roughly `3` minutes each can already produce useful signal when combined with strong pretrained encoders like `MERT`.

My adjustment is only this:

- treat `20` as the hard floor
- treat `24` as the recommended target
- treat `30` as a bonus, not a requirement

That keeps the dataset within personal-user effort limits while still giving Phase 2 enough material to answer the next real question: which encoder and alignment path deserve to become the new mainline.
