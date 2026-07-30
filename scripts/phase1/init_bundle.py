#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import os
from pathlib import Path
import subprocess

REPO_ROOT = Path(__file__).resolve().parents[2]
MANIFEST_PATH = REPO_ROOT / 'dataset' / 'manifests' / 'phase1_jpop_single_artist.csv'


def write_yaml(path: Path, pairs: list[tuple[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [f'{key}: {value}' for key, value in pairs]
    path.write_text("\n".join(lines) + "\n", encoding='utf-8')


def ensure_link(target: Path, link_path: Path) -> None:
    link_path.parent.mkdir(parents=True, exist_ok=True)
    if link_path.exists() or link_path.is_symlink():
        link_path.unlink()
    relative_target = os.path.relpath(target, start=link_path.parent)
    link_path.symlink_to(relative_target)


def export_pages(source_pdf: Path, pages_dir: Path) -> None:
    pages_dir.mkdir(parents=True, exist_ok=True)
    for existing in pages_dir.glob('page-*.png'):
        existing.unlink()
    subprocess.run([
        'pdftoppm', '-png', str(source_pdf), str(pages_dir / 'page')
    ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def render_to_wav(render_audio: Path, wav_path: Path) -> None:
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run([
        'ffmpeg', '-y', '-loglevel', 'error', '-i', str(render_audio), str(wav_path)
    ], check=True)


def load_manifest_row(song_id: str) -> dict[str, str]:
    with MANIFEST_PATH.open(encoding='utf-8', newline='') as handle:
        for row in csv.DictReader(handle):
            if row['song_id'] == song_id:
                return row
    raise KeyError(f'{song_id} not found in manifest')


def main() -> int:
    parser = argparse.ArgumentParser(description='Initialize a Phase 1 ArrangementBundle from the manifest.')
    parser.add_argument('--song-id', required=True, help='Manifest song_id, for example song_001')
    parser.add_argument('--allow-missing-render', action='store_true', help='Create bundle even if render audio is missing')
    args = parser.parse_args()

    row = load_manifest_row(args.song_id)
    source_audio = REPO_ROOT / row['source_audio_path'] if row['source_audio_path'] else None
    score_pdf = REPO_ROOT / row['score_pdf_path'] if row['score_pdf_path'] else None
    render_audio = REPO_ROOT / row['render_audio_path'] if row['render_audio_path'] else None

    if source_audio is None or not source_audio.exists():
        raise SystemExit(f'missing source audio for {args.song_id}')
    if score_pdf is None or not score_pdf.exists():
        raise SystemExit(f'missing score pdf for {args.song_id}')
    if (render_audio is None or not render_audio.exists()) and not args.allow_missing_render:
        raise SystemExit(f'missing render audio for {args.song_id}; rerun with --allow-missing-render if intended')

    bundle_dir = REPO_ROOT / 'dataset' / 'bundles' / args.song_id
    ensure_link(source_audio, bundle_dir / 'source' / 'song_audio.mp3')
    ensure_link(score_pdf, bundle_dir / 'arrangement' / 'score' / 'source.pdf')

    if render_audio is not None and render_audio.exists():
        render_to_wav(render_audio, bundle_dir / 'arrangement' / 'render' / 'piano_clean.wav')

    export_pages(score_pdf, bundle_dir / 'arrangement' / 'score' / 'pages')

    metadata_pairs = [
        ('song_id', row['song_id']),
        ('singer', row['singer']),
        ('track_title', row['track_title']),
        ('arranger', row['arranger'] or 'unknown'),
        ('source_duration_sec', row['source_duration_sec'] or '0'),
        ('source_release', '""'),
        ('arrangement_source', f'"{row["score_pdf_path"]}"'),
        ('version_match', row['version_match'] or 'unknown'),
        ('target_tier', row['target_tier'] or 'Gold'),
        ('transpose_semitones', '0'),
        ('tempo_notes', '""'),
        ('notes', f'"{row["notes"]}"' if row['notes'] else '"bootstrap bundle"'),
    ]
    write_yaml(bundle_dir / 'source' / 'metadata.yaml', metadata_pairs)

    qc_pairs = [
        ('qc_grade', row['qc_grade'] or 'unknown'),
        ('status', row['status'] or 'candidate'),
        ('source_audio_exists', 'yes'),
        ('score_pdf_exists', 'yes'),
        ('render_audio_exists', 'yes' if render_audio is not None and render_audio.exists() else 'no'),
        ('score_pages_exported', 'yes'),
        ('version_match', row['version_match'] or 'unknown'),
        ('checked_on', '2026-07-30'),
        ('notes', f'"{row["notes"]}"' if row['notes'] else '"initialized from local bootstrap assets"'),
    ]
    write_yaml(bundle_dir / 'qc' / 'quality_report.yaml', qc_pairs)
    print(f'initialized {bundle_dir.relative_to(REPO_ROOT)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
