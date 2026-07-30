# ADR-0001: Standard MIDI as Core Output

PiCoGen2 outputs Standard MIDI natively. MIDI captures all performance information (pitch, duration, velocity, timing, pedal, tempo) needed to represent a piano arrangement. Downstream formats (MusicXML, PDF, audio) are deterministic conversions from MIDI. Choosing any other core format would add an unnecessary conversion layer or force the model to learn output patterns that MIDI already handles.

Status: accepted

Considered Options:
- **MusicXML** — richer notation semantics, but PiCoGen2 does not output it natively; would require a MIDI→MusicXML translation step regardless
- **Audio waveform** — loses note-level information; cannot be edited or transcribed losslessly

Consequences:
- All training targets must be in Standard MIDI format
- MuseScore (or equivalent) is a required dependency for post-processing
- Notation-quality rendering depends on the MIDI→MusicXML conversion quality, which is outside the learning loop
