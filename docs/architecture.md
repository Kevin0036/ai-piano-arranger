# Architecture

## System Overview

The system extends PiCoGen2 (Foundation Model) with lightweight Adapters that modify generated output toward a specific Style, Domain, or user Preference. The Foundation Model stays frozen; only Adapter parameters are trained.

```
               Foundation Model (PiCoGen2)

Audio ─────────────────────────────► Standard MIDI
                                         │
                                    [Adapter]
                                         │
                    ┌────────────────────┼────────────────────┐
                    │                    │                    │
               Domain              Style              Preference
               Adapter             Adapter             Adapter
                    │                    │                    │
                    └────────────────────┼────────────────────┘
                                         ▼
                              Personalised Standard MIDI
                                         │
                                   [Post-processing]
                                         ▼
                              MusicXML / PDF / Audio
```

## Pipeline

```
Audio ──► Beat Detection ──► SheetSage Feature Extraction ──► PiCoGen Decoder ──► Event Sequence ──► Standard MIDI
           (beat_this)          (melody + harmony embs)          (+ Adapter)           (tokenizer)          (MIDI file)
```

### Components

| Step | Component | Output | Notes |
|------|-----------|--------|-------|
| 1 | `beat_this` | Beat/downbeat timestamps | Required by SheetSage |
| 2 | `sheetsage` | Melody & harmony embeddings | Feature extractor, frozen |
| 3 | `picogen2.PiCoGenDecoder` | Token event sequence | Decoder, frozen during inference; Adapter attached here |
| 4 | `picogen2.Tokenizer` | Standard MIDI | Converts event tokens to MIDI file |
| 5 | Post-processing | MusicXML / PDF / Audio | MuseScore for notation, fluid synth for audio |

## Three Learning Layers

### Layer 1 — Domain
What "typical" arrangements sound like for a music category.
- *Data*: ~20 paired samples from the same Domain (e.g., JPOP)
- *Training target*: Domain-specific Adapter
- *Switch cost*: Load different Domain Adapter

### Layer 2 — Style
What a specific arranger's creative habits look like.
- *Data*: ~20 paired samples from one arranger (e.g., Animenz)
- *Training target*: Style-specific Adapter
- *Switch cost*: Load different Style Adapter

### Layer 3 — Preference
What a specific user tends to like.
- *Data*: Implicit from user's selection history (preferred version A over B)
- *Training target*: Personal Preference Adapter
- *Learning mode*: Continuous, accumulates over time

```
General Music ──► JPOP ──► Animenz ──► Kevin's preferred Animenz style
                                          (increasing specificity)
```

## Data Format

### Paired Training Sample

```
Input:  original audio file (any common format: mp3, wav, flac)
Target: Standard MIDI file (.mid)
```

### Directory Structure

```
data/
└── {adapter-name}/
    ├── sample_001/
    │   ├── audio.mp3
    │   └── piano.mid
    ├── sample_002/
    │   ├── audio.mp3
    │   └── piano.mid
    └── ...
```

## Training Flow

```
Original Audio
      │
      ▼
Foundation Model (frozen)
      │
      ├── beats + downbeats (beat_this)
      ├── melody/harmony embeddings (sheetsage)
      └── token events (decoder)
              │
              ▼
      Compare with Target MIDI events
              │
              ▼
      Compute Loss → Update Adapter only
```

- Foundation Model remains **frozen** throughout
- Only Adapter parameters are updated
- Prevents catastrophic forgetting of general arrangement capability

## Inference Flow

```
Audio ──► Foundation Model + Adapter ──► Personalised Standard MIDI
```

- Switch Adapter = switch Style, no other changes
- Storage per Adapter is minimal (only delta parameters)
- Adapters are shareable between users

## Development Roadmap

### Phase 1 — Familiarise with PiCoGen2 (current)
- [ ] Set up Conda environment (`conda create -n picogen2 python=3.10`)
- [ ] Install dependencies (`pip install -r requirements.txt`)
- [ ] Run `python demo.py` with a test audio file
- [ ] Understand input/output format through Python API
- [ ] Read training code (`train.py`, `preprocess.py`, `dataset.py`)

### Phase 2 — Build Personal Dataset
- [ ] Choose target arranger (e.g., Animenz)
- [ ] Collect ~20 paired samples (original audio + piano MIDI)
- [ ] Build data preprocessing tools
- [ ] Validate data format compatibility with PiCoGen2

### Phase 3 — Train First Adapter
- [ ] Implement Adapter training loop
- [ ] Experiment with hyperparameters
- [ ] Compare generated output before/after Adapter
- [ ] Verify style transfer is audible and consistent

### Phase 4 — Establish Full Workflow
- [ ] Automated data pipeline
- [ ] One-click training
- [ ] Automated Adapter loading and inference
- [ ] Automated MIDI → PDF/audio export

### Phase 5 — UI & UX
- [ ] GUI for training and inference
- [ ] Adapter management
- [ ] Parameter configuration
- [ ] Logging and monitoring

### Phase 6 — Continuous Improvement
- [ ] More music Domains
- [ ] Adapter composition / stacking
- [ ] Better training methods
- [ ] Performance optimisation
