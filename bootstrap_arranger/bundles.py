from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path

import torch
from torch.utils.data import Dataset

from .audio import AudioFeatureCache


@dataclass
class BundleRecord:
    song_id: str
    singer: str
    track_title: str
    bundle_dir: Path
    source_audio_path: Path
    render_audio_path: Path
    score_pdf_path: Path | None
    target_tier: str
    status: str


def load_bundle_records(
    manifest_path: Path,
    bundle_root: Path,
    bundle_ids: list[str] | None = None,
) -> list[BundleRecord]:
    wanted_ids = set(bundle_ids) if bundle_ids else None
    records: list[BundleRecord] = []
    with manifest_path.open(encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            song_id = row["song_id"].strip()
            if not song_id:
                continue
            if wanted_ids is not None and song_id not in wanted_ids:
                continue
            bundle_dir = bundle_root / song_id
            source_audio = bundle_dir / "source" / "song_audio.mp3"
            render_audio = bundle_dir / "arrangement" / "render" / "piano_clean.wav"
            if not bundle_dir.exists() or not source_audio.exists() or not render_audio.exists():
                continue
            score_pdf = bundle_dir / "arrangement" / "score" / "source.pdf"
            records.append(
                BundleRecord(
                    song_id=song_id,
                    singer=row["singer"].strip(),
                    track_title=row["track_title"].strip(),
                    bundle_dir=bundle_dir,
                    source_audio_path=source_audio,
                    render_audio_path=render_audio,
                    score_pdf_path=score_pdf if score_pdf.exists() else None,
                    target_tier=row["target_tier"].strip(),
                    status=row["status"].strip(),
                )
            )
    return records


class BootstrapBundleDataset(Dataset):
    def __init__(
        self,
        records: list[BundleRecord],
        feature_tag: str,
        alignment_filename: str = "audio_to_render.bootstrap.json",
    ):
        self.records = records
        self.feature_tag = feature_tag
        self.alignment_filename = alignment_filename

    def __len__(self) -> int:
        return len(self.records)

    def __getitem__(self, index: int) -> dict[str, object]:
        record = self.records[index]
        features_dir = record.bundle_dir / "features"
        source_cache = AudioFeatureCache.from_file(features_dir / f"source_{self.feature_tag}.pt")
        render_cache = AudioFeatureCache.from_file(features_dir / f"render_{self.feature_tag}.pt")
        align_path = record.bundle_dir / "arrangement" / "align" / self.alignment_filename
        alignment = json.loads(align_path.read_text(encoding="utf-8"))
        token_path = record.bundle_dir / "arrangement" / "symbolic" / "picogen_tokens.json"
        token_ids = None
        if token_path.exists():
            token_ids = torch.tensor(json.loads(token_path.read_text(encoding="utf-8")), dtype=torch.long)
        return {
            "record": record,
            "source_features": source_cache.pooled_features,
            "render_features": render_cache.pooled_features,
            "alignment": alignment,
            "target_token_ids": token_ids,
        }
