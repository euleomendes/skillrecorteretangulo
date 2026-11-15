"""Funções compartilhadas pela skill editor-clone-referencia."""
import json
import math
import re
import subprocess
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
REF_DIR = ROOT / "referencias"
OUT_DIR = ROOT / "analysis"
FONT_DIR = ROOT / "assets" / "fonts"
PROFILE = OUT_DIR / "style_profile.json"
VIDEO_EXT = {".mp4", ".mov", ".m4v", ".mkv", ".webm", ".avi"}


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def probe(path):
    r = run(["ffprobe", "-v", "error", "-print_format", "json",
             "-show_streams", "-show_format", str(path)])
    j = json.loads(r.stdout)
    v = next(s for s in j["streams"] if s["codec_type"] == "video")
    num, den = v["avg_frame_rate"].split("/")
    fps = float(num) / float(den) if float(den) else 30.0
    rot = 0
    for sd in v.get("side_data_list", []) or []:
        if "rotation" in sd:
            rot = int(sd["rotation"])
    w, h = int(v["width"]), int(v["height"])
    if abs(rot) in (90, 270):
        w, h = h, w
    return {"width": w, "height": h, "fps": round(fps, 3),
            "duration": float(j["format"]["duration"]),
            "has_audio": any(s["codec_type"] == "audio" for s in j["streams"])}


def extract_frames(path, duration, n, outdir, stem):
    outdir.mkdir(parents=True, exist_ok=True)
    paths = []
    for i in range(n):
        t = duration * (i + 0.5) / n
        p = outdir / f"{stem}_f{i:02d}.png"
        run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
             "-ss", f"{t:.3f}", "-i", str(path), "-frames:v", "1", str(p)])
        if p.exists():
            paths.append(p)
    return paths


def load_small(p, width=360):
    im = Image.open(p).convert("RGB")
    h = max(1, round(im.height * width / im.width))
    return im.resize((width, h), Image.LANCZOS)


def saturation_mean(arr_uint8):
    im = Image.fromarray(arr_uint8, "RGB").convert("HSV")
    return float(np.asarray(im)[..., 1].mean())


def color_stats(image_paths):
    """Média/desvio por canal RGB, saturação média (0-255), percentis 1/99."""
    arrs = [np.asarray(load_small(p)) for p in image_paths]
    flat = np.concatenate([a.reshape(-1, 3) for a in arrs]).astype(np.float64)
    sat = float(np.mean([saturation_mean(a) for a in arrs]))
    return {
        "mean": [round(float(x), 2) for x in flat.mean(0)],
        "std": [round(float(x), 2) for x in flat.std(0)],
        "p1": [round(float(x), 2) for x in np.percentile(flat, 1, axis=0)],
        "p99": [round(float(x), 2) for x in np.percentile(flat, 99, axis=0)],
        "saturation": round(sat, 2),
    }


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#%02X%02X%02X" % tuple(int(round(x)) for x in rgb)


def finite(x):
    return x is not None and not (isinstance(x, float) and (math.isinf(x) or math.isnan(x)))


def load_profile():
    if not PROFILE.exists():
        raise SystemExit("Perfil não encontrado. Rode primeiro: "
                         ".venv/bin/python scripts/analyze_references.py")
    return json.loads(PROFILE.read_text())
