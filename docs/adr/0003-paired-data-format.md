# ADR-0003: Paired (Audio, MIDI) as Training Data Format

The Foundation Model accepts audio as input and produces MIDI as output. Training an Adapter requires the model to learn the difference between its default output and the target Style. The most direct supervision signal is therefore (audio → desired MIDI) pairs — the same format the model sees at inference time.

Other supervision formats were considered but rejected:
- **Audio→Audio pairs** — loses note-level accuracy for loss computation
- **Symbolic→Symbolic (MIDI→MIDI)** — doesn't align with the Foundation Model's audio input interface; would require retraining or an additional encoder
- **Unsupervised style transfer** — no clear learning target; hard to measure improvement

The format is simple enough that any user can construct it with an audio player and a MIDI download.

Status: accepted

Considered Options:
- **Audio→Audio pairs** — no note-level ground truth; loss computation is ambiguous
- **Symbolic→Symbolic (MIDI→MIDI)** — incompatible with Foundation Model's audio encoder
- **Text/description only** — insufficiently precise for musical details

Consequences:
- All training data requires two files per sample (audio + MIDI), increasing collection effort
- Audio quality variance across samples adds noise to training; consistent pre-processing is essential
- The same data format works for all three learning layers (Domain, Style, Preference)
