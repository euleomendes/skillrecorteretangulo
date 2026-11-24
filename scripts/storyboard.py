#!/usr/bin/env python3
"""Storyboard enumerado para o usuário aprovar antes do render final.

Renderiza um quadro por cena (no fim de cada cena, com os elementos já na tela),
numera e monta uma folha única.

uso: .venv/bin/python scripts/storyboard.py VIDEO --scenes PASTA/scenes.json --out PASTA/storyboard.jpg
     [--times 3.5,6.1,...]   # opcional: um tempo por cena (s, no vídeo editado)
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--scenes", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--times", default="")
    a = ap.parse_args()
    py = sys.executable
    if a.times:
        times = [float(t) for t in a.times.split(",")]
    else:
        segs = json.loads(subprocess.check_output([py, str(ROOT / "scripts" / "motion_edit.py"), a.video,
                                                   "--print-segments"], stderr=subprocess.DEVNULL))
        raw = json.loads(a.scenes.read_text())
        scenes = raw["scenes"] if isinstance(raw, dict) else raw
        starts = [float(sc.get("start", segs[sc["segs"][0]]["edited_start"])) for sc in scenes]
        last = segs[-1]
        total = last["edited_start"] + last["original_end"] - last["original_start"]
        ends = starts[1:] + [total]
        times = [round(max(s + .2, e - .35), 2) for s, e in zip(starts, ends)]
    for f in (ROOT / "analysis").glob("motion_*.png"):
        f.unlink()
    r = subprocess.run([py, str(ROOT / "scripts" / "motion_edit.py"), a.video, "--scenes", str(a.scenes),
                        "--sample", ",".join(map(str, times))], capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr[-2000:])
    shots = [ROOT / "analysis" / f"motion_{t:05.2f}.png" for t in times]
    fonts = ROOT / "assets" / "fonts"
    try:
        big = ImageFont.truetype(str(fonts / "Inter-ExtraBold.otf"), 30)
        small = ImageFont.truetype(str(fonts / "Inter-SemiBold.otf"), 20)
    except OSError:
        big = small = ImageFont.load_default()
    cols = min(5, len(shots))
    rows = (len(shots) + cols - 1) // cols
    tw, th, pad = 360, 640, 16
    sheet = Image.new("RGB", (cols * tw + (cols + 1) * pad, rows * (th + 50) + (rows + 1) * pad), (18, 18, 20))
    draw = ImageDraw.Draw(sheet)
    for i, (shot, t) in enumerate(zip(shots, times)):
        x, y = pad + (i % cols) * (tw + pad), pad + (i // cols) * (th + 50 + pad)
        sheet.paste(Image.open(shot).convert("RGB").resize((tw, th)), (x, y + 44))
        draw.rounded_rectangle((x, y, x + 54, y + 36), 8, fill=(253, 85, 10))
        draw.text((x + 27, y + 18), str(i + 1), font=big, fill="white", anchor="mm")
        draw.text((x + 64, y + 18), f"{t:.1f}s", font=small, fill=(200, 200, 205), anchor="lm")
    a.out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(a.out, quality=90)
    print(a.out)


if __name__ == "__main__":
    main()
