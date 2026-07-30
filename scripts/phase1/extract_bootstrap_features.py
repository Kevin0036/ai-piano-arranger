#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from bootstrap_arranger.alignment import align_pooled_features
from bootstrap_arranger.audio import AudioFeatureExtractorConfig, create_audio_feature_extractor
from bootstrap_arranger.bundles import load_bundle_records


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract bootstrap audio features for Phase 1 bundles.")
    parser.add_argument("--config", required=True, help="Path to the phase1 bootstrap YAML config.")
    args = parser.parse_args()

    config_path = Path(args.config).resolve()
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))

    extractor_config = AudioFeatureExtractorConfig(
        backend=config["audio_encoder"]["backend"],
        model_name_or_path=config["audio_encoder"]["model_name_or_path"],
        sample_rate=int(config["audio_encoder"].get("sample_rate", 24000)),
        pool_seconds=float(config["audio_encoder"].get("pool_seconds", 0.5)),
        max_steps=int(config["audio_encoder"].get("max_steps", 512)),
        inference_chunk_seconds=float(config["audio_encoder"].get("inference_chunk_seconds", 20.0)),
        local_files_only=bool(config["audio_encoder"].get("local_files_only", False)),
        trust_remote_code=bool(config["audio_encoder"].get("trust_remote_code", False)),
        device=str(config["audio_encoder"].get("device", "cpu")),
    )

    bundle_ids = list(config["dataset"]["bundle_ids"])
    manifest_path = Path(config["dataset"]["manifest_path"])
    bundle_root = Path(config["dataset"]["bundle_root"])
    feature_tag = str(config["dataset"]["feature_tag"])

    extractor = create_audio_feature_extractor(extractor_config)
    records = load_bundle_records(manifest_path, bundle_root, bundle_ids)
    for record in records:
        features_dir = record.bundle_dir / "features"
        align_dir = record.bundle_dir / "arrangement" / "align"
        features_dir.mkdir(parents=True, exist_ok=True)
        align_dir.mkdir(parents=True, exist_ok=True)

        source_cache = extractor.encode_file(record.source_audio_path)
        render_cache = extractor.encode_file(record.render_audio_path)

        source_path = features_dir / f"source_{feature_tag}.pt"
        render_path = features_dir / f"render_{feature_tag}.pt"
        import torch

        torch.save(source_cache.to_serializable(), source_path)
        torch.save(render_cache.to_serializable(), render_path)

        alignment = align_pooled_features(source_cache.pooled_features, render_cache.pooled_features)
        alignment_path = align_dir / str(config["dataset"].get("alignment_filename", "audio_to_render.bootstrap.json"))
        alignment_path.write_text(json.dumps(alignment, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"extracted {record.song_id}: {record.track_title}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
