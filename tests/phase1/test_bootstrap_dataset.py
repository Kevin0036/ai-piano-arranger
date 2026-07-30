from __future__ import annotations

import csv
import json
import tempfile
import unittest
from pathlib import Path

import torch

from bootstrap_arranger.bundles import BootstrapBundleDataset, load_bundle_records


class BootstrapDatasetTest(unittest.TestCase):
    def test_dataset_loads_cached_features(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            manifest = root / "manifest.csv"
            bundle_root = root / "bundles"
            bundle_dir = bundle_root / "song_001"
            (bundle_dir / "source").mkdir(parents=True)
            (bundle_dir / "arrangement" / "render").mkdir(parents=True)
            (bundle_dir / "arrangement" / "score").mkdir(parents=True)
            (bundle_dir / "arrangement" / "align").mkdir(parents=True)
            (bundle_dir / "features").mkdir(parents=True)
            (bundle_dir / "source" / "song_audio.mp3").write_bytes(b"")
            (bundle_dir / "arrangement" / "render" / "piano_clean.wav").write_bytes(b"")
            (bundle_dir / "arrangement" / "score" / "source.pdf").write_bytes(b"")

            with manifest.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(
                    handle,
                    fieldnames=[
                        "song_id",
                        "singer",
                        "track_title",
                        "target_tier",
                        "status",
                    ],
                )
                writer.writeheader()
                writer.writerow(
                    {
                        "song_id": "song_001",
                        "singer": "ヨルシカ",
                        "track_title": "test",
                        "target_tier": "Gold",
                        "status": "reference_bundle",
                    }
                )

            torch.save(
                {
                    "pooled_features": torch.randn(4, 8),
                    "hidden_states": torch.randn(10, 8),
                    "duration_sec": 1.0,
                    "frame_rate": 10.0,
                    "backend": "mock",
                    "model_name_or_path": "mock",
                },
                bundle_dir / "features" / "source_mock.pt",
            )
            torch.save(
                {
                    "pooled_features": torch.randn(5, 8),
                    "hidden_states": torch.randn(12, 8),
                    "duration_sec": 1.2,
                    "frame_rate": 10.0,
                    "backend": "mock",
                    "model_name_or_path": "mock",
                },
                bundle_dir / "features" / "render_mock.pt",
            )
            (bundle_dir / "arrangement" / "align" / "audio_to_render.bootstrap.json").write_text(
                json.dumps({"path": [[0, 0], [1, 1], [2, 2], [3, 3]]}),
                encoding="utf-8",
            )

            records = load_bundle_records(manifest, bundle_root, ["song_001"])
            dataset = BootstrapBundleDataset(records, feature_tag="mock")
            item = dataset[0]
            self.assertEqual(item["record"].song_id, "song_001")
            self.assertEqual(tuple(item["source_features"].shape), (4, 8))
            self.assertEqual(tuple(item["render_features"].shape), (5, 8))


if __name__ == "__main__":
    unittest.main()
