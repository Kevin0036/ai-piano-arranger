# ADR Reset Notice（2026-07-30）

As of 2026-07-30, the previous ADR set has been archived to:

- `docs/archive/2026-07-30-reset/adr/0001-standard-midi-as-core-output.md`
- `docs/archive/2026-07-30-reset/adr/0002-adapter-instead-of-full-finetune.md`
- `docs/archive/2026-07-30-reset/adr/0003-paired-data-format.md`

The old ADRs were coherent within the old design, but they are no longer active because the project baseline changed:

1. the old stack assumed `SheetSage + Jukebox` as the center of music understanding
2. the old stack treated `Standard MIDI` as the sole canonical representation
3. the old stack defined data primarily as `(audio, midi)` pairs

The current active planning documents are:

- `Goal.md`
- `docs/project-vision.md`
- `docs/architecture.md`
- `research.md`

New ADRs should be written only after the next benchmark round settles the open decisions around:

- source encoder choice
- score-native representation choice
- preference-learning placement
