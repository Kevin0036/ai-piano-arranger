#!/usr/bin/env python3
from __future__ import annotations

import csv
from pathlib import Path
import sys

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
import validate_bundle as vb


def main() -> int:
    manifest_path = REPO_ROOT / 'dataset' / 'manifests' / 'phase1_jpop_single_artist.csv'
    bundle_root = REPO_ROOT / 'dataset' / 'bundles'
    report_path = REPO_ROOT / 'dataset' / 'reports' / 'phase1_summary.md'

    with manifest_path.open(encoding='utf-8', newline='') as handle:
        rows = list(csv.DictReader(handle))

    titled_rows = [row for row in rows if row['track_title'].strip()]
    source_count = sum(bool(row['source_audio_path'].strip()) for row in titled_rows)
    score_count = sum(bool(row['score_pdf_path'].strip()) for row in titled_rows)
    render_count = sum(bool(row['render_audio_path'].strip()) for row in titled_rows)
    reference_rows = [row for row in titled_rows if row['status'] == 'reference_bundle']
    active_rows = [row for row in titled_rows if row['status'] in {'reference_bundle', 'collect_render'}]

    bundles = sorted(bundle_root.glob('song_*'))
    results = [vb.validate_bundle(bundle) for bundle in bundles]
    valid_count = sum(item['valid'] for item in results)

    lines = [
        '# Phase 1 Summary',
        '',
        'Date: 2026-07-30',
        '',
        '## Manifest Coverage',
        '',
        f'- titled candidates: {len(titled_rows)}',
        f'- source audio available: {source_count}',
        f'- score pdf available: {score_count}',
        f'- clean render available: {render_count}',
        f'- active gold-track rows: {len(active_rows)}',
        f'- reference-bundle rows: {len(reference_rows)}',
        '',
        '## Bundle Validation',
        '',
        f'- validated bundles: {valid_count}/{len(results)}',
        '',
        '| bundle | title | valid | qc_grade | notes |',
        '| --- | --- | --- | --- | --- |',
    ]
    for item in results:
        metadata = item['metadata']
        qc = item['qc']
        notes = '; '.join(item['errors'] + item['warnings']) if (item['errors'] or item['warnings']) else 'bootstrap reference bundle'
        lines.append(
            f"| {item['bundle']} | {metadata.get('track_title', '')} | {'yes' if item['valid'] else 'no'} | {qc.get('qc_grade', '')} | {notes} |"
        )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding='utf-8')
    print(f'wrote {report_path.relative_to(REPO_ROOT)}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
