#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from music21 import converter, metadata, stream
import miditoolkit
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from bootstrap_arranger.paths import resolve_picogen_root  # noqa: E402

PICOGEN_ROOT = resolve_picogen_root()
if str(PICOGEN_ROOT) not in sys.path:
    sys.path.insert(0, str(PICOGEN_ROOT))

from picogen2 import Tokenizer  # noqa: E402


@dataclass
class BundlePaths:
    song_id: str
    bundle_dir: Path
    pdf_path: Path
    pages_dir: Path
    symbolic_dir: Path
    page_xml_dir: Path
    combined_xml_path: Path
    midi_path: Path
    token_path: Path
    review_path: Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run HOMR on Phase 1 trial bundles.")
    parser.add_argument(
        "--config",
        default="configs/phase1/bootstrap_mert_overfit.yaml",
        help="Phase 1 bootstrap config used to discover bundle ids.",
    )
    parser.add_argument(
        "--skip-homr",
        action="store_true",
        help="Reuse existing page-level MusicXML outputs instead of invoking homr again.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Pass --debug to homr for more verbose per-page processing.",
    )
    return parser.parse_args()


def load_bundle_paths(config_path: Path) -> list[BundlePaths]:
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    bundle_root = REPO_ROOT / config["dataset"]["bundle_root"]
    bundle_ids = list(config["dataset"]["bundle_ids"])
    bundles: list[BundlePaths] = []
    for song_id in bundle_ids:
        bundle_dir = bundle_root / song_id
        score_dir = bundle_dir / "arrangement" / "score"
        symbolic_dir = bundle_dir / "arrangement" / "symbolic"
        page_xml_dir = symbolic_dir / "homr_pages"
        bundles.append(
            BundlePaths(
                song_id=song_id,
                bundle_dir=bundle_dir,
                pdf_path=score_dir / "source.pdf",
                pages_dir=score_dir / "pages",
                symbolic_dir=symbolic_dir,
                page_xml_dir=page_xml_dir,
                combined_xml_path=symbolic_dir / "homr_combined.musicxml",
                midi_path=symbolic_dir / "homr.mid",
                token_path=symbolic_dir / "picogen_tokens.json",
                review_path=symbolic_dir / "homr_review.json",
            )
        )
    return bundles


def ensure_page_images(bundle: BundlePaths) -> list[Path]:
    bundle.pages_dir.mkdir(parents=True, exist_ok=True)
    page_images = sorted(bundle.pages_dir.glob("page-*.png"))
    if page_images:
        return page_images

    subprocess.run(
        [
            "pdftoppm",
            "-png",
            str(bundle.pdf_path),
            str(bundle.pages_dir / "page"),
        ],
        check=True,
    )
    page_images = sorted(bundle.pages_dir.glob("page-*.png"))
    if not page_images:
        raise FileNotFoundError(f"No page images were exported for {bundle.song_id}")
    return page_images


def run_homr_on_page(page_image: Path, debug: bool = False) -> Path:
    command = ["homr"]
    if debug:
        command.append("--debug")
    command.append(str(page_image))
    subprocess.run(command, check=True)
    page_xml = page_image.with_suffix(".musicxml")
    if not page_xml.exists():
        raise FileNotFoundError(f"homr did not emit {page_xml}")
    return page_xml


def collect_page_xmls(bundle: BundlePaths, page_images: list[Path], skip_homr: bool, debug: bool) -> list[Path]:
    bundle.page_xml_dir.mkdir(parents=True, exist_ok=True)
    xml_paths: list[Path] = []
    for page_image in page_images:
        page_xml = page_image.with_suffix(".musicxml")
        if not skip_homr or not page_xml.exists():
            page_xml = run_homr_on_page(page_image, debug=debug)
        copied_xml = bundle.page_xml_dir / page_xml.name
        copied_xml.write_text(page_xml.read_text(encoding="utf-8"), encoding="utf-8")
        xml_paths.append(copied_xml)
    return xml_paths


def _append_part_measures(target_part: stream.Part, source_part: stream.Part) -> None:
    for measure in source_part.getElementsByClass(stream.Measure):
        target_part.append(copy.deepcopy(measure))


def combine_page_musicxml(page_xmls: list[Path], output_path: Path) -> stream.Score:
    if not page_xmls:
        raise ValueError("No page-level MusicXML files to combine.")

    parsed_scores = [converter.parse(str(path)) for path in page_xmls]
    first_score = parsed_scores[0]
    combined = stream.Score(id="homr_combined")
    combined.metadata = metadata.Metadata()
    if first_score.metadata is not None:
        combined.metadata.title = first_score.metadata.title
        combined.metadata.composer = first_score.metadata.composer

    combined_parts: list[stream.Part] = []
    for first_part in first_score.parts:
        new_part = stream.Part(id=first_part.id)
        for element in first_part.getElementsByClass(("Instrument", "Clef", "KeySignature", "TimeSignature")):
            new_part.append(copy.deepcopy(element))
        _append_part_measures(new_part, first_part)
        combined.append(new_part)
        combined_parts.append(new_part)

    for extra_score in parsed_scores[1:]:
        for index, part in enumerate(extra_score.parts):
            if index >= len(combined_parts):
                new_part = stream.Part(id=part.id)
                combined.append(new_part)
                combined_parts.append(new_part)
            _append_part_measures(combined_parts[index], part)

    for part in combined.parts:
        for measure_index, measure in enumerate(part.getElementsByClass(stream.Measure), start=1):
            measure.number = measure_index

    output_path.parent.mkdir(parents=True, exist_ok=True)
    combined.write("musicxml", fp=str(output_path))
    return combined


def write_midi_and_tokens(score: stream.Score, midi_path: Path, token_path: Path) -> dict[str, int]:
    midi_path.parent.mkdir(parents=True, exist_ok=True)
    score.write("midi", fp=str(midi_path))

    tokenizer = Tokenizer()
    midi_obj = miditoolkit.MidiFile(str(midi_path))
    song = tokenizer.get_song_from_midi(midi_obj)
    token_ids = [tokenizer.e2i(event) for event in song["events"]]
    token_path.write_text(json.dumps(token_ids, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        "num_parts": len(score.parts),
        "num_measures": max(
            (len(part.getElementsByClass(stream.Measure)) for part in score.parts),
            default=0,
        ),
        "num_tokens": len(token_ids),
        "num_midi_instruments": len(midi_obj.instruments),
    }


def process_bundle(bundle: BundlePaths, skip_homr: bool, debug: bool) -> None:
    page_images = ensure_page_images(bundle)
    page_xmls = collect_page_xmls(bundle, page_images, skip_homr=skip_homr, debug=debug)
    score = combine_page_musicxml(page_xmls, bundle.combined_xml_path)
    stats = write_midi_and_tokens(score, bundle.midi_path, bundle.token_path)

    review = {
        "song_id": bundle.song_id,
        "pdf_path": str(bundle.pdf_path.relative_to(REPO_ROOT)),
        "page_images": [str(path.relative_to(REPO_ROOT)) for path in page_images],
        "page_musicxml": [str(path.relative_to(REPO_ROOT)) for path in page_xmls],
        "combined_musicxml": str(bundle.combined_xml_path.relative_to(REPO_ROOT)),
        "midi_path": str(bundle.midi_path.relative_to(REPO_ROOT)),
        "picogen_tokens": str(bundle.token_path.relative_to(REPO_ROOT)),
        **stats,
    }
    bundle.review_path.write_text(json.dumps(review, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"processed {bundle.song_id}: measures={stats['num_measures']} tokens={stats['num_tokens']}")


def main() -> int:
    args = parse_args()
    bundles = load_bundle_paths((REPO_ROOT / args.config).resolve())
    for bundle in bundles:
        process_bundle(bundle, skip_homr=args.skip_homr, debug=args.debug)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
