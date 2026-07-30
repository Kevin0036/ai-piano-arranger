#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = REPO_ROOT / 'schemas' / 'arrangement_bundle.schema.yaml'


def parse_simple_yaml(path: Path) -> dict[str, object]:
    data: dict[str, object] = {}
    current_key: str | None = None
    for raw_line in path.read_text(encoding='utf-8').splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if stripped.startswith('- '):
            if current_key is None:
                raise ValueError(f'list item without key in {path}')
            items = data.setdefault(current_key, [])
            assert isinstance(items, list)
            items.append(stripped[2:].strip())
            continue
        if ':' not in stripped:
            continue
        key, value = stripped.split(':', 1)
        key = key.strip()
        value = value.strip().strip('"')
        if value == '':
            data[key] = []
            current_key = key
        else:
            data[key] = value
            current_key = None
    return data


def validate_bundle(bundle_path: Path) -> dict[str, object]:
    schema = parse_simple_yaml(SCHEMA_PATH)
    required_paths = [Path(p) for p in schema.get('required_paths', [])]
    required_metadata = [str(item) for item in schema.get('required_metadata', [])]
    optional_paths = [Path(p) for p in schema.get('optional_paths', [])]

    errors: list[str] = []
    warnings: list[str] = []

    metadata_path = bundle_path / 'source' / 'metadata.yaml'
    qc_path = bundle_path / 'qc' / 'quality_report.yaml'
    metadata = parse_simple_yaml(metadata_path) if metadata_path.exists() else {}
    qc = parse_simple_yaml(qc_path) if qc_path.exists() else {}

    for rel_path in required_paths:
        if not (bundle_path / rel_path).exists():
            errors.append(f'missing required path: {rel_path.as_posix()}')

    for key in required_metadata:
        value = metadata.get(key, '')
        if str(value).strip() == '':
            errors.append(f'missing required metadata: {key}')

    for rel_path in optional_paths:
        if not (bundle_path / rel_path).exists():
            warnings.append(f'missing optional path: {rel_path.as_posix()}')

    render_flag = str(qc.get('render_audio_exists', '')).strip().lower()
    if render_flag and render_flag not in {'yes', 'unknown'}:
        warnings.append('qc indicates render audio is incomplete')

    return {
        'bundle': bundle_path.name,
        'valid': not errors,
        'errors': errors,
        'warnings': warnings,
        'metadata': metadata,
        'qc': qc,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate ArrangementBundle folders.')
    parser.add_argument('bundle_paths', nargs='*', help='Bundle paths to validate. Defaults to dataset/bundles/song_*')
    parser.add_argument('--json', action='store_true', dest='as_json', help='Emit JSON instead of text output')
    args = parser.parse_args()

    if args.bundle_paths:
        bundle_paths = [Path(path).resolve() for path in args.bundle_paths]
    else:
        bundle_paths = sorted((REPO_ROOT / 'dataset' / 'bundles').glob('song_*'))

    results = [validate_bundle(path) for path in bundle_paths if path.exists()]
    if args.as_json:
        print(json.dumps(results, ensure_ascii=False, indent=2))
        return 0 if all(item['valid'] for item in results) else 1

    for item in results:
        state = 'OK' if item['valid'] else 'FAIL'
        print(f"{state} {item['bundle']}")
        for error in item['errors']:
            print(f"  error: {error}")
        for warning in item['warnings']:
            print(f"  warn: {warning}")
    return 0 if all(item['valid'] for item in results) else 1


if __name__ == '__main__':
    raise SystemExit(main())
