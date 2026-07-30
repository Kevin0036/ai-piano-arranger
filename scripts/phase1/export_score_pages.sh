#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "usage: export_score_pages.sh <input.pdf> <output_dir>" >&2
  exit 1
fi

input_pdf="$1"
output_dir="$2"
mkdir -p "$output_dir"
pdftoppm -png "$input_pdf" "$output_dir/page"
