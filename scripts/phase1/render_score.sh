#!/usr/bin/env bash
set -euo pipefail

if [ "$#" -ne 2 ]; then
  echo "usage: render_score.sh <input_score> <output.wav>" >&2
  exit 1
fi

input_score="$1"
output_wav="$2"

if command -v musescore >/dev/null 2>&1; then
  musescore "$input_score" -o "$output_wav"
elif command -v mscore >/dev/null 2>&1; then
  mscore "$input_score" -o "$output_wav"
else
  echo "MuseScore CLI not found" >&2
  exit 2
fi
