# Architecture（2026-07-30）

> 旧版架构文档已归档到 `docs/archive/2026-07-30-reset/architecture-pre-reset.md`。  
> 当前架构以 `ArrangementBundle` 和多视角对齐为中心，不再以 `SheetSage + MIDI-only` 为前提。

## 1. System Overview

新的系统不再把“原曲音频输入、MIDI 输出”视作唯一主轴，而是把每个改编样本组织成一个多视角 bundle，然后在 bundle 内外建立对齐和条件。

```text
                  Source Side
          ┌─────────────────────────┐
          │   original song audio   │
          └────────────┬────────────┘
                       │
             source encoder benchmark
          (MERT / MuQ / MusicFM / ...)
                       │
                       ▼
               source representation
                       │
                       ▼
                 conditioning builder
                       ▲
                       │
        ┌──────────────┼─────────────────┐
        │              │                 │
        │              │                 │
        ▼              ▼                 ▼
  score representation  render-audio rep  optional symbolic rep
 (MusicXML / score tok) (clean piano wav) (MIDI / event tokens)
        ▲              ▲                 ▲
        │              │                 │
        └──────────────┴─────────────────┘
                    ArrangementBundle
                       │
                       ▼
               cross-view alignment
                       │
                       ▼
                baseline generator
             (short-term: PiCoGen2)
                       │
                       ▼
                arrangement package
      (score / render audio / optional MIDI / metadata)
```

## 2. Canonical Sample Unit

### `ArrangementBundle`

当前系统中的标准数据单元定义为：

```text
bundle/
  source/
    song_audio.mp3
    metadata.yaml
  arrangement/
    score/
      master.musicxml
      source.pdf
      pages/
    render/
      piano_clean.wav
    symbolic/
      optional.mid
    align/
      audio_to_render.json
      score_to_render.json
  qc/
    quality_report.yaml
```

### Bootstrap note

For the current repo bootstrap, canonical raw assets live under `assets/raw/` (`songs/`, `sheets/`, `piano_mp3/`).
Phase 1 reference bundles under `dataset/bundles/` are allowed to symlink back to the source song and score assets while normalizing the arrangement render into bundle-local `piano_clean.wav`.

### Canonical priority

1. `score-native` assets are first-class truth when available.
2. `render-audio` is the main perceptual bridge between notation and listening.
3. `symbolic-derived` assets are useful but not authoritative by default.

## 3. Core Architectural Decisions

### 3.1 Score-native first

MusicXML, source PDF, and page images remain preserved throughout the pipeline.  
The system should avoid collapsing all supervision into MIDI at ingestion time.

### 3.2 Render audio is a bridge, not a byproduct

The clean piano render generated from the score is valuable because it:

- makes audio-domain alignment easier
- creates a controllable acoustic proxy of the arrangement
- lets source-audio encoders and arrangement-audio encoders meet in a comparable space

### 3.3 OMR / AMT are helper modules only

OMR, AMT, and audio-to-MIDI tools may populate missing views or support validation, but they are not the canonical representation layer.

### 3.4 Generator replacement is deferred

The first reset milestone does not require inventing a new generator immediately.  
`PiCoGen2` remains the short-term baseline so the team can isolate whether the real gains come from better representations and conditioning.

## 4. Main Layers

### 4.1 Source Audio Encoder Layer

Responsibility:
- encode the original song
- provide structural, rhythmic, semantic, and stylistic representations

Current benchmark candidates:
- `MERT`
- `MuQ`
- `MusicFM`

Output:
- frame/segment embeddings
- optional pooled section-level descriptors
- optional retrieval/indexing vectors

### 4.2 Score Representation Layer

Responsibility:
- parse native score assets
- expose notation-aware features without flattening them too early

Possible representations:
- MusicXML object graph
- score tokens
- page/layout anchors
- staff/voice/measure metadata

Output:
- notation-level tokens
- structural annotations
- render anchors for alignment

### 4.3 Render Audio Representation Layer

Responsibility:
- encode the clean piano render as an acoustic view of the arrangement

Why this matters:
- it is much closer to the source audio modality than raw notation
- it avoids some of the ambiguity of direct source-audio to score alignment

Output:
- acoustic embeddings
- onset/beat/section descriptors
- alignment anchors

### 4.4 Optional Symbolic Layer

Responsibility:
- provide event-based representations needed for legacy training paths or compatible generators

Examples:
- Standard MIDI
- note event sequences
- tokenizer events for `PiCoGen2`

Constraint:
- this layer is derived and replaceable; it is no longer the sole center of the architecture

### 4.5 Cross-View Alignment Layer

Responsibility:
- align source audio with arrangement render
- align arrangement render with arrangement score
- map sections, motifs, and harmonic regions across representations

Outputs may include:
- timestamp mappings
- section correspondences
- note-to-frame or measure-to-frame anchors
- confidence and QC metadata

This is the layer that makes the three user-collectible resources jointly useful instead of merely co-existing on disk.

### 4.6 Conditioning Builder

Responsibility:
- construct model-ready conditions from all available views

Condition families:
- content condition from the source song
- style condition from arrangement clusters or arranger identity
- controllability condition for difficulty, density, mood, playability
- preference condition from user feedback signals

Key design goal:
- keep this interface stable even if the downstream generator changes

### 4.7 Generator Layer

Short-term role:
- validate that the new conditioning pipeline can drive usable arrangement generation

Short-term baseline:
- `PiCoGen2` with a compatibility adapter if needed

Medium-term options:
- a better event generator
- a score-aware generator
- a retrieval-augmented editing workflow

### 4.8 Preference / Ranking Layer

Responsibility:
- learn from user choices without forcing every preference signal into the base generator weights

Candidate mechanisms:
- reranking
- lightweight adapters
- reward/preference modeling

This layer remains explicitly open until the new data core is stable.

## 5. Output Contract

The architectural output is no longer “just MIDI”.

The desired arrangement package can include:
- score artifacts
- rendered piano audio
- symbolic event export
- metadata and confidence traces

That output contract better matches how users actually consume and edit arrangements.

## 6. Evaluation Surface

The new architecture should be evaluated across four surfaces:

1. Representation quality
   - structure capture
   - style separability
   - cross-song retrieval usefulness
2. Alignment quality
   - source-to-render alignment
   - render-to-score alignment
   - QC confidence stability
3. Generation quality
   - musicality
   - playability
   - notation quality
4. Personalisation quality
   - style controllability
   - preference satisfaction
   - consistency over repeated use

## 7. Archived Assumptions

The following assumptions from the pre-reset architecture are no longer active:

1. `SheetSage + Jukebox` is the core understanding frontend.
2. Standard MIDI is the sole canonical output and supervision target.
3. `(audio, midi)` pairs are the complete data definition.
4. The main path forward is to distill new features back into the old SheetSage interface.

## 8. Pending Decisions

The architecture is active, but three decisions are intentionally left open until the next benchmark round:

1. Which source encoder becomes the mainline default
2. Which score representation becomes canonical inside the pipeline
3. Whether personalization first lands in conditioning, reranking, or lightweight adaptation
