#!/usr/bin/env python3
"""QA: gera imagens lado a lado (referência x resultado) e compara estatísticas de cor."""
import sys
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import OUT_DIR, color_stats, extract_frames, load_profile, probe


def main():
    if len(sys.argv) < 2:
        raise SystemExit("uso: compare_frames.py <video_final.mp4>")
    video = Path(sys.argv[1]).expanduser().resolve()
    prof = load_profile()
    info = probe(video)
    tmp = Path(tempfile.mkdtemp(prefix="qa_"))
    outs = extract_frames(video, info["duration"], 3, tmp, "out")
    refs = sorted(OUT_DIR.glob("*_f*.png"))
    if not refs:
        raise SystemExit("Sem frames de referência em analysis/. Rode analyze_references.py")

    step = max(1, len(refs) // 3)
    for i, o in enumerate(outs):
        r = refs[(i * step) % len(refs)]
        a, b = Image.open(r).convert("RGB"), Image.open(o).convert("RGB")
        h = 800
        a = a.resize((int(a.width * h / a.height), h))
        b = b.resize((int(b.width * h / b.height), h))
        sheet = Image.new("RGB", (a.width + b.width + 20, h + 30), "black")
        sheet.paste(a, (0, 30))
        sheet.paste(b, (a.width + 20, 30))
        d = ImageDraw.Draw(sheet)
        d.text((8, 8), "REFERENCIA", fill="white")
        d.text((a.width + 28, 8), "RESULTADO", fill="white")
        p = OUT_DIR / f"qa_{i}.jpg"
        sheet.save(p, quality=90)
        print("QA:", p)

    s = color_stats(outs)
    t = prof["grade"]
    print("\nCor (alvo da referência x resultado)")
    print("  média RGB :", t["mean"], "x", s["mean"])
    print("  desvio RGB:", t["std"], "x", s["std"])
    print("  saturação :", t["saturation"], "x", s["saturation"])
    print("  formato   :", f'{prof["format"]["width"]}x{prof["format"]["height"]}',
          "x", f'{info["width"]}x{info["height"]}')
    print("\nA cor varia com o conteúdo de cada vídeo; use as imagens qa_*.jpg como juiz final.")


if __name__ == "__main__":
    main()
