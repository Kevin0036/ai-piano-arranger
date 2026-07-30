import tempfile
from pathlib import Path

import picogen2
import picogen2.assets
from picogen2.mirtoolkit import beat_this, sheetsage


def test_picogen():
    pass


def test_api():
    audio_file = picogen2.assets.test_song()
    output_dir = tempfile.TemporaryDirectory()

    tokenizer = picogen2.Tokenizer()
    model = picogen2.PiCoGenDecoder.from_pretrained(device="cuda")

    beat_detector = beat_this.BeatThis()
    beats, downbeats = beat_detector(audio_file)
    beat_information = {"beats": beats.tolist(), "downbeats": downbeats.tolist()}
    sheetsage_model = sheetsage.SheetSage()
    sheetsage_output = sheetsage_model(audio_path=audio_file, beat_information=beat_information)

    out_events = picogen2.decode(
        model=model,
        tokenizer=tokenizer,
        beat_information=beat_information,
        melody_last_embs=sheetsage_output["melody_last_hidden_state"],
        harmony_last_embs=sheetsage_output["harmony_last_hidden_state"],
    )

    (Path(output_dir.name) / "piano.txt").write_text("\n".join(map(str, out_events)))
    tokenizer.events_to_midi(out_events).dump(Path(output_dir.name) / "piano.mid")


if __name__ == "__main__":
    test_picogen()
    test_api()
