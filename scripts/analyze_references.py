#!/usr/bin/env python3
"""Analisa os vídeos em referencias/ e grava analysis/style_profile.json.

Extrai: formato, fps, loudness, ritmo de cortes, estatísticas de cor e uma
ESTIMATIVA de legendas via OCR (altura, posição, cor). A estimativa de legenda
precisa ser confirmada olhando as imagens geradas (ver SKILL.md, passo 3).
"""
import json
import re
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (OUT_DIR, PROFILE, REF_DIR, VIDEO_EXT, color_stats, extract_frames,
                    finite, load_small, probe, rgb_to_hex, run)

N_FRAMES = 12


def loudness(path):
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-af",
             "loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json", "-f", "null", "-"])
    m = re.search(r"\{[^{}]*\"input_i\"[^{}]*\}", r.stderr, re.S)
    if not m:
        return None
    d = json.loads(m.group(0))
    lufs, tp = float(d["input_i"]), float(d["input_tp"])
    if not (finite(lufs) and finite(tp)):
        return None
    return {"lufs": lufs, "true_peak": tp}


def scene_cuts(path, thr=0.3):
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(path), "-vf",
             f"select='gt(scene,{thr})',showinfo", "-an", "-f", "null", "-"])
    return [float(x) for x in re.findall(r"pts_time:([0-9.]+)", r.stderr)]


def contact_sheet(frames, out, cols=4, thumb=270):
    ims = [Image.open(p).convert("RGB") for p in frames]
    if not ims:
        return
    ratio = ims[0].height / ims[0].width
    tw, th = thumb, int(thumb * ratio)
    rows = (len(ims) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * tw, rows * th), "black")
    for i, im in enumerate(ims):
        sheet.paste(im.resize((tw, th)), ((i % cols) * tw, (i // cols) * th))
    sheet.save(out, quality=90)


def ocr_boxes(img_path):
    if not shutil.which("tesseract"):
        return []
    r = run(["tesseract", str(img_path), "stdout", "--psm", "11", "tsv"])
    boxes = []
    for line in r.stdout.splitlines()[1:]:
        p = line.split("\t")
        if len(p) < 12:
            continue
        try:
            conf = float(p[10])
        except ValueError:
            continue
        txt = p[11].strip()
        if conf >= 60 and len(txt) >= 2 and any(c.isalnum() for c in txt):
            boxes.append((int(p[6]), int(p[7]), int(p[8]), int(p[9]), txt))
    return boxes


def text_color(img, box):
    l, t, w, h, _ = box
    crop = img.crop((l, t, l + w, t + h)).convert("RGB")
    if crop.width < 2 or crop.height < 2:
        return None
    q = crop.quantize(colors=4)
    pal = q.getpalette()[:12]
    cols = [tuple(pal[i:i + 3]) for i in range(0, 12, 3)]
    counts = sorted(q.getcolors(), reverse=True)
    arr = np.asarray(crop)
    edge = np.concatenate([arr[0], arr[-1], arr[:, 0], arr[:, -1]]).reshape(-1, 3)
    bg = np.median(edge, axis=0)
    best = max((cols[idx] for _, idx in counts if idx < len(cols)),
               key=lambda c: float(np.linalg.norm(np.array(c) - bg)), default=None)
    return rgb_to_hex(best) if best else None


def estimate_captions(frames):
    heights, ys, colors, n_frames_with_text = [], [], [], 0
    for p in frames:
        img = Image.open(p).convert("RGB")
        boxes = ocr_boxes(p)
        if boxes:
            n_frames_with_text += 1
        for b in boxes:
            heights.append(b[3] / img.height)
            ys.append((b[1] + b[3] / 2) / img.height)
            c = text_color(img, b)
            if c:
                colors.append(c)
    if not heights:
        return None
    common = max(set(colors), key=colors.count) if colors else None
    return {
        "frames_with_text": n_frames_with_text,
        "median_word_height_ratio": round(float(np.median(heights)), 4),
        "median_y_center_ratio": round(float(np.median(ys)), 3),
        "most_common_text_color": common,
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    vids = sorted(p for p in REF_DIR.iterdir() if p.suffix.lower() in VIDEO_EXT) \
        if REF_DIR.exists() else []
    if not vids:
        raise SystemExit(f"Nenhum vídeo em {REF_DIR}. Coloque as referências lá.")

    refs, all_frames, cap_est = [], [], []
    for v in vids:
        print(f"-> {v.name}")
        info = probe(v)
        frames = extract_frames(v, info["duration"], N_FRAMES, OUT_DIR, v.stem)
        all_frames += frames
        contact_sheet(frames, OUT_DIR / f"{v.stem}_contact.jpg")
        cuts = scene_cuts(v)
        n_shots = len(cuts) + 1
        refs.append({
            "file": v.name, **info,
            "color": color_stats(frames),
            "audio": loudness(v) if info["has_audio"] else None,
            "cuts": len(cuts),
            "avg_shot_seconds": round(info["duration"] / n_shots, 2),
        })
        est = estimate_captions(frames)
        if est:
            cap_est.append(est)

    # agrega: cor = média das referências
    mean = np.mean([r["color"]["mean"] for r in refs], axis=0)
    std = np.mean([r["color"]["std"] for r in refs], axis=0)
    sat = float(np.mean([r["color"]["saturation"] for r in refs]))
    audios = [r["audio"] for r in refs if r["audio"]]
    first = refs[0]

    captions = {
        "enabled": True, "font_name": "Montserrat", "font_file": None,
        "bold": True, "uppercase": False,
        "primary_color": "#FFFFFF", "outline_color": "#000000",
        "outline_width_ratio": 0.004, "shadow": 0,
        "highlight_color": None, "words_per_caption": 3,
        "y_center_ratio": 0.70, "font_size_ratio": 0.045,
        "_verified": False,
    }
    if cap_est:
        h = float(np.median([c["median_word_height_ratio"] for c in cap_est]))
        captions["font_size_ratio"] = round(h * 1.3, 4)
        captions["y_center_ratio"] = round(
            float(np.median([c["median_y_center_ratio"] for c in cap_est])), 3)
        cols = [c["most_common_text_color"] for c in cap_est if c["most_common_text_color"]]
        if cols:
            captions["primary_color"] = max(set(cols), key=cols.count)
    else:
        captions["_note"] = ("OCR não detectou texto (ou tesseract ausente). "
                             "Confira as imagens; se não há legenda, enabled=false.")

    profile = {
        "format": {"width": first["width"], "height": first["height"], "fps": first["fps"]},
        "grade": {"mean": [round(float(x), 2) for x in mean],
                  "std": [round(float(x), 2) for x in std],
                  "saturation": round(sat, 2)},
        "audio": ({"lufs": round(float(np.mean([a["lufs"] for a in audios])), 1),
                   "true_peak": -1.5} if audios else None),
        "pacing": {"avg_shot_seconds": round(float(np.mean(
            [r["avg_shot_seconds"] for r in refs])), 2),
            "cuts_per_minute": round(float(np.mean(
                [r["cuts"] / (r["duration"] / 60) for r in refs])), 1)},
        "captions": captions,
        "references": refs,
    }

    # não sobrescreve legendas/grade já confirmadas pelo usuário/agente
    if PROFILE.exists():
        old = json.loads(PROFILE.read_text())
        if old.get("captions", {}).get("_verified"):
            profile["captions"] = old["captions"]
            profile["grade"] = old.get("grade", profile["grade"])
            print("(perfil já verificado: legendas e grade mantidas)")

    PROFILE.write_text(json.dumps(profile, indent=2, ensure_ascii=False))
    print(f"\nPerfil salvo em {PROFILE}")
    print("Próximo passo: abra analysis/*_contact.jpg e confirme legendas/fonte/cores.")


if __name__ == "__main__":
    main()
