from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT / 'scripts' / 'phase1'))
import validate_bundle as vb


class ValidateBundleTest(unittest.TestCase):
    def test_valid_bundle_passes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = Path(temp_dir) / 'song_999'
            (bundle / 'source').mkdir(parents=True)
            (bundle / 'arrangement' / 'score').mkdir(parents=True)
            (bundle / 'arrangement' / 'render').mkdir(parents=True)
            (bundle / 'qc').mkdir(parents=True)
            (bundle / 'source' / 'song_audio.mp3').write_bytes(b'')
            (bundle / 'arrangement' / 'score' / 'source.pdf').write_bytes(b'')
            (bundle / 'arrangement' / 'render' / 'piano_clean.wav').write_bytes(b'')
            (bundle / 'source' / 'metadata.yaml').write_text(
                'song_id: song_999\n'
                'singer: ヨルシカ\n'
                'track_title: test\n'
                'arranger: unknown\n'
                'source_duration_sec: 123.0\n'
                'version_match: yes\n'
                'target_tier: Gold\n',
                encoding='utf-8',
            )
            (bundle / 'qc' / 'quality_report.yaml').write_text(
                'qc_grade: bootstrap_gold\nrender_audio_exists: yes\n',
                encoding='utf-8',
            )
            result = vb.validate_bundle(bundle)
            self.assertTrue(result['valid'])
            self.assertEqual(result['errors'], [])

    def test_missing_render_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            bundle = Path(temp_dir) / 'song_998'
            (bundle / 'source').mkdir(parents=True)
            (bundle / 'arrangement' / 'score').mkdir(parents=True)
            (bundle / 'qc').mkdir(parents=True)
            (bundle / 'source' / 'song_audio.mp3').write_bytes(b'')
            (bundle / 'arrangement' / 'score' / 'source.pdf').write_bytes(b'')
            (bundle / 'source' / 'metadata.yaml').write_text(
                'song_id: song_998\n'
                'singer: ヨルシカ\n'
                'track_title: test\n'
                'arranger: unknown\n'
                'source_duration_sec: 123.0\n'
                'version_match: yes\n'
                'target_tier: Gold\n',
                encoding='utf-8',
            )
            (bundle / 'qc' / 'quality_report.yaml').write_text('qc_grade: missing\n', encoding='utf-8')
            result = vb.validate_bundle(bundle)
            self.assertFalse(result['valid'])
            self.assertTrue(any('piano_clean.wav' in error for error in result['errors']))


if __name__ == '__main__':
    unittest.main()
