# AI Piano Arrangement

Build a personalised AI piano arrangement assistant that learns from user preferences, based on PiCoGen2 as the foundation model.

## Language

**Piano Arrangement**:
A creative reinterpretation of a song written for solo piano, preserving melody and harmony while adapting texture, voicing, and difficulty to the instrument.
_Avoid_: Transcription, piano reduction

**Foundation Model**:
The base model (PiCoGen2) that takes audio input and produces a Standard MIDI piano arrangement. It is frozen during style training and provides general piano arrangement capability.
_Avoid_: Base model, backbone, pre-trained model (too generic)

**Adapter**:
A lightweight, separately trained module that modifies the Foundation Model's output toward a specific style, domain, or user preference. Only Adapter parameters are updated during training; the Foundation Model stays frozen.
_Avoid_: Fine-tuned model, LoRA (too specific — Adapter is the concept, LoRA is one implementation)

**Style**:
The distinctive creative habits of a specific piano arranger (e.g., Animenz's virtuosic textures, White Notes's melodic clarity). An Adapter trained on ~20 paired samples from one arranger captures their Style.
_Avoid_: Genre, vibe

**Domain**:
A category of music with shared arrangement conventions (e.g., JPOP, Anime Song, Vocaloid, Game Music). The first learning layer — what "typical" arrangements sound like for this type of music.

**Preference**:
An individual user's taste in piano arrangements. The highest learning layer — learned implicitly from which versions the user prefers over time. Every user has their own Preference even for the same Style.

**Standard MIDI**:
The unified output format of the entire pipeline. Contains all performance information (pitch, duration, velocity, timing, pedal, tempo). Downstream formats (MusicXML, PDF, audio) are derived from it.
_Avoid_: MIDI file, piano MIDI (ambiguous)

**Paired Data**:
A training sample consisting of (original audio, target piano MIDI). The audio is the Foundation Model's input; the MIDI is the desired output. ~20 high-quality pairs are expected to train a usable Adapter.
_Avoid_: Dataset, training set (too broad)

**Incremental Learning**:
The principle that the system accumulates new styles without retraining from scratch or forgetting previously learned capabilities. Adapter-based training is the current mechanism; the principle outlives any specific implementation.

**Texture**:
The patterns and voicing used in piano writing — left-hand accompaniment figuration, right-hand chord spacing, octave doublings, arpeggiation, register shifts. Style differences often manifest as texture differences.

**Arranger**:
A human who creates piano arrangements. The project studies arrangers' work to learn Style, but does not aim to replicate specific living arrangers — it learns the *pattern* of their creative decisions.

**Post-processing**:
The automatic conversion from Standard MIDI to end-user formats (MusicXML via MuseScore, PDF, audio rendering). This is outside the model's learning loop — a deterministic pipeline.
_Avoid_: Export, render

**Windows Fork**:
The project uses [chenkigba/PiCoGen v2](https://github.com/chenkigba/PiCoGen/tree/v2) — a Windows-compatible fork of PiCoGen2 that replaces Linux-specific tools (wget, mpi4py) with cross-platform Python equivalents. Run natively on Windows without WSL or Docker.
