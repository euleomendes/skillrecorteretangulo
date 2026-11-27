#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
for binary in python3 ffmpeg ffprobe curl unzip; do
  command -v "$binary" >/dev/null || { echo "Instale $binary antes de rodar o setup." >&2; exit 1; }
done
if ! ffmpeg -hide_banner -filters 2>/dev/null | awk '/[[:space:]]ass[[:space:]]/{found=1} END {exit !found}'; then
  echo 'Instale uma versão do FFmpeg com o filtro ass (libass).' >&2
  exit 1
fi
python3 -c 'import sys; sys.exit(sys.version_info < (3, 10))' || { echo "Use Python 3.10 ou mais novo." >&2; exit 1; }
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
if [[ "$(uname)" == "Linux" ]]; then
  .venv/bin/python -m playwright install --with-deps chromium || .venv/bin/python -m playwright install chromium
else
  .venv/bin/python -m playwright install chromium
fi
mkdir -p models assets/fonts
asset_tmp=$(mktemp -d)
trap 'rm -rf "$asset_tmp"' EXIT
if [[ ! -s assets/fonts/Inter-ExtraBold.otf || ! -s assets/fonts/Inter-Medium.otf ||
      ! -s assets/fonts/Inter-SemiBold.otf || ! -s assets/fonts/Inter-LICENSE.txt ]]; then
  curl -fLsS --retry 2 -o "$asset_tmp/inter.zip" \
    https://github.com/rsms/inter/releases/download/v4.1/Inter-4.1.zip
  unzip -j -o "$asset_tmp/inter.zip" 'extras/otf/Inter-ExtraBold.otf' \
    'extras/otf/Inter-Medium.otf' 'extras/otf/Inter-SemiBold.otf' -d assets/fonts
  unzip -p "$asset_tmp/inter.zip" LICENSE.txt > assets/fonts/Inter-LICENSE.txt
fi
if [[ ! -s assets/fonts/InstrumentSerif-Italic.ttf || ! -s assets/fonts/InstrumentSerif-OFL.txt ]]; then
  base=https://raw.githubusercontent.com/google/fonts/main/ofl/instrumentserif
  curl -fLsS --retry 2 -o "$asset_tmp/InstrumentSerif-Italic.ttf" "$base/InstrumentSerif-Italic.ttf"
  curl -fLsS --retry 2 -o "$asset_tmp/InstrumentSerif-OFL.txt" "$base/OFL.txt"
  mv "$asset_tmp/"InstrumentSerif-* assets/fonts/
fi
if [[ ! -s models/u2net_human_seg.onnx ]]; then
  tmp="$asset_tmp/u2net.onnx"
  curl --fail --location --retry 2 -o "$tmp" \
    https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net_human_seg.onnx
  test "$(wc -c < "$tmp" | tr -d " ")" -eq 175997641
  mv "$tmp" models/u2net_human_seg.onnx
fi
if [[ ! -s models/rvm_mobilenetv3_fp32.onnx ]]; then
  tmp="$asset_tmp/rvm.onnx"
  curl --fail --location --retry 2 -o "$tmp" \
    https://github.com/PeterL1n/RobustVideoMatting/releases/download/v1.0.0/rvm_mobilenetv3_fp32.onnx
  test "$(wc -c < "$tmp" | tr -d " ")" -eq 14975696
  mv "$tmp" models/rvm_mobilenetv3_fp32.onnx
fi
# emojis: o macOS já tem Apple Color Emoji; nos outros sistemas baixa a Noto Color Emoji (OFL)
if [[ "$(uname)" != "Darwin" && ! -s assets/fonts/NotoColorEmoji-Regular.ttf ]]; then
  curl -fLsS --retry 2 -o "$asset_tmp/emoji.ttf" \
    https://raw.githubusercontent.com/google/fonts/main/ofl/notocoloremoji/NotoColorEmoji-Regular.ttf
  mv "$asset_tmp/emoji.ttf" assets/fonts/NotoColorEmoji-Regular.ttf
fi
.venv/bin/python scripts/check.py
