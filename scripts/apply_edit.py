#!/usr/bin/env python3
"""Aplica o estilo de analysis/style_profile.json a um vídeo novo."""
import argparse
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (FONT_DIR, ROOT, color_stats, extract_frames, hex_to_rgb, load_profile,
                    load_small, probe, run, saturation_mean)


# ---------- silêncio ----------
def speech_segments(video, dur, noise_db=-35, min_sil=0.35, pad=0.08):
    r = run(["ffmpeg", "-hide_banner", "-nostats", "-i", str(video), "-af",
             f"silencedetect=noise={noise_db}dB:d={min_sil}", "-f", "null", "-"])
    starts = [float(x) for x in re.findall(r"silence_start: ([0-9.]+)", r.stderr)]
    ends = [float(x) for x in re.findall(r"silence_end: ([0-9.]+)", r.stderr)]
    segs, cur = [], 0.0
    for i, s in enumerate(starts):
        if s - cur > 0.15:
            segs.append((max(0, cur - pad), min(dur, s + pad)))
        cur = ends[i] if i < len(ends) else dur
    if dur - cur > 0.15:
        segs.append((max(0, cur - pad), dur))
    return segs or [(0, dur)]


def remove_silence(video, out, dur):
    segs = speech_segments(video, dur)
    parts, labels = [], ""
    for i, (a, b) in enumerate(segs):
        parts.append(f"[0:v]trim=start={a:.3f}:end={b:.3f},setpts=PTS-STARTPTS[v{i}];"
                     f"[0:a]atrim=start={a:.3f}:end={b:.3f},asetpts=PTS-STARTPTS[a{i}];")
        labels += f"[v{i}][a{i}]"
    graph = "".join(parts) + f"{labels}concat=n={len(segs)}:v=1:a=1[v][a]"
    script = out.with_suffix(".filter.txt")
    script.write_text(graph)
    r = run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(video),
             "-filter_complex", graph, "-map", "[v]", "-map", "[a]",
             "-c:v", "libx264", "-crf", "14", "-preset", "veryfast",
             "-c:a", "aac", "-b:a", "192k", str(out)])
    if r.returncode != 0:
        raise SystemExit("Falha ao remover silêncio:\n" + r.stderr)
    print(f"Silêncio removido: {len(segs)} trechos mantidos")


# ---------- cor ----------
def grade_params(tgt, src, strength):
    ks, ms, mt = [], [], []
    for i in range(3):
        s_in = max(src["std"][i], 1.0)
        k = 1 + strength * (tgt["std"][i] / s_in - 1)
        k = float(np.clip(k, 0.5, 2.0))
        ks.append(k)
        ms.append(src["mean"][i])
        mt.append(src["mean"][i] + strength * (tgt["mean"][i] - src["mean"][i]))
    return ks, ms, mt


def grade_filter(ks, ms, mt, sat_ratio):
    ch = []
    for name, k, m_in, m_t in zip("rgb", ks, ms, mt):
        ch.append(f"{name}='clip((val-{m_in:.2f})*{k:.4f}+{m_t:.2f},0,maxval)'")
    f = "lutrgb=" + ":".join(ch)
    if abs(sat_ratio - 1) > 0.02:
        f += f",eq=saturation={sat_ratio:.3f}"
    return f


def simulated_saturation(frames, ks, ms, mt):
    sats = []
    for p in frames:
        a = np.asarray(load_small(p)).astype(np.float64)
        for i in range(3):
            a[..., i] = np.clip((a[..., i] - ms[i]) * ks[i] + mt[i], 0, 255)
        sats.append(saturation_mean(a.astype(np.uint8)))
    return float(np.mean(sats))


# ---------- legendas ----------
def transcribe(video, lang, model_name):
    try:
        from faster_whisper import WhisperModel
    except ImportError:
        raise SystemExit("faster-whisper ausente. Rode scripts/setup.sh")
    model = WhisperModel(model_name, device="cpu", compute_type="int8")
    pcm = subprocess.check_output(["ffmpeg", "-v", "error", "-i", str(video), "-ac", "1",
                                   "-ar", "16000", "-f", "s16le", "-"])
    samples = np.frombuffer(pcm, dtype="<i2").astype(np.float32) / 32768
    segs, _ = model.transcribe(samples, language=lang, word_timestamps=True,
                               vad_filter=True)
    words = []
    for s in segs:
        for w in (s.words or []):
            t = w.word.strip()
            if t:
                words.append((w.start, w.end, t))
    return words


def ass_color(hex_rgb):
    r, g, b = hex_to_rgb(hex_rgb)
    return f"&H00{b:02X}{g:02X}{r:02X}"


def ts(t):
    t = max(0, t)
    h, m = int(t // 3600), int(t % 3600 // 60)
    return f"{h}:{m:02d}:{t % 60:05.2f}"


def font_family(cap):
    ff = cap.get("font_file")
    if ff:
        p = FONT_DIR / ff
        if p.exists():
            fam, style = ImageFont.truetype(str(p), 20).getname()
            # nome completo (ex.: "Inter ExtraBold"): evita que o libass escolha
            # outro peso da mesma família instalada no sistema
            return fam if style in ("Regular", "Bold", "Italic", "Bold Italic") \
                else f"{fam} {style}"
    return cap["font_name"]


def warn_font(cap, family):
    if cap.get("font_file") and (FONT_DIR / cap["font_file"]).exists():
        return
    r = run(["fc-list", ":", "family"])
    if r.returncode == 0 and family.lower() not in r.stdout.lower():
        print(f"\n!!! AVISO: a fonte '{family}' não está instalada nem em assets/fonts/.\n"
              "    O ffmpeg vai usar outra fonte e o resultado NÃO será idêntico.\n"
              "    Coloque o .ttf/.otf em assets/fonts/ e preencha 'font_file' no perfil.\n")


def group_words(words, n, max_chars=99):
    groups, cur = [], []
    for w in words:
        if cur and (len(cur) >= n or len(' '.join(x[2] for x in cur + [w])) > max_chars or w[0] - cur[-1][1] > 0.8
                    or cur[-1][2][-1:] in ".!?"):
            groups.append(cur)
            cur = []
        cur.append(w)
    if cur:
        groups.append(cur)
    return groups


def build_ass(words, cap, W, H, path):
    family = font_family(cap)
    size = round(cap["font_size_ratio"] * H)
    outline = round(cap["outline_width_ratio"] * H, 1)
    prim = ass_color(cap["primary_color"])
    hl = ass_color(cap["highlight_color"]) if cap.get("highlight_color") else None
    bold = -1 if cap.get("bold") else 0
    x, y = cap.get("x_center", W // 2), round(cap["y_center_ratio"] * H)
    head = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {W}\nPlayResY: {H}\n"
            "WrapStyle: 2\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\n"
            "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,"
            "BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,"
            "BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n"
            f"Style: Cap,{family},{size},{prim},{prim},{ass_color(cap['outline_color'])},"
            f"&H{cap.get('shadow_alpha','80')}000000,{bold},0,0,0,100,100,{cap.get('letter_spacing_ratio', 0) * H:.2f},0,1,{outline},{cap.get('shadow', 0)},5,"
            f"{int(W * 0.06)},{int(W * 0.06)},0,1\n\n[Events]\n"
            "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")

    def clean(t):
        t = t.replace("{", "(").replace("}", ")")
        return t.upper() if cap.get("uppercase") else t

    pos = f"{{\\an5\\pos({x},{y})\\blur{cap.get('blur', 0)}}}"
    lines = []
    for g in group_words(words, cap["words_per_caption"], cap.get("max_chars", 99)):
        g_end = g[-1][1]
        if hl:
            for i, (s, e, t) in enumerate(g):
                end = g[i + 1][0] if i + 1 < len(g) else g_end
                txt = " ".join(
                    (f"{{\\c{hl}}}{clean(w[2])}{{\\c{prim}}}" if j == i else clean(w[2]))
                    for j, w in enumerate(g))
                lines.append(f"Dialogue: 0,{ts(s)},{ts(max(end, s + 0.05))},Cap,,0,0,0,,{pos}{txt}")
        else:
            txt = " ".join(clean(w[2]) for w in g)
            lines.append(f"Dialogue: 0,{ts(g[0][0])},{ts(g_end)},Cap,,0,0,0,,{pos}{txt}")
    path.write_text(head + "\n".join(lines) + "\n", encoding="utf-8")
    return family


# ---------- main ----------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--out", default=None)
    ap.add_argument("--remove-silence", action="store_true")
    ap.add_argument("--grade-strength", type=float, default=1.0)
    ap.add_argument("--fit", choices=["cover", "blur"], default="cover",
                    help="cover = corta para preencher; blur = fundo desfocado")
    ap.add_argument("--lang", default="pt")
    ap.add_argument("--whisper-model", default="small")
    ap.add_argument("--no-captions", action="store_true")
    ap.add_argument("--words-json", default=None,
                    help="transcrição pronta: lista JSON [[inicio, fim, palavra], ...] "
                         "(use junto com a duração do vídeo JÁ sem silêncio)")
    a = ap.parse_args()

    prof = load_profile()
    cap = prof["captions"]
    fmt = prof["format"]
    W, H, FPS = fmt["width"], fmt["height"], fmt["fps"]

    src = Path(a.video).expanduser().resolve()
    if not src.exists():
        raise SystemExit(f"Vídeo não encontrado: {src}")
    out = Path(a.out).expanduser().resolve() if a.out else ROOT / "output" / f"{src.stem}_editado.mp4"
    out.parent.mkdir(parents=True, exist_ok=True)

    work = Path(tempfile.mkdtemp(prefix="clone_edit_"))
    try:
        info = probe(src)
        cur = src
        if a.remove_silence and info["has_audio"]:
            trimmed = work / "trimmed.mp4"
            remove_silence(src, trimmed, info["duration"])
            cur, info = trimmed, probe(trimmed)

        # cor
        if prof["grade"].get("enabled", True):
            frames = extract_frames(cur, info["duration"], 10, work, "src")
            sstats = color_stats(frames)
            ks, ms, mt = grade_params(prof["grade"], sstats, a.grade_strength)
            sim_sat = simulated_saturation(frames, ks, ms, mt)
            sat_ratio = prof["grade"]["saturation"] / max(sim_sat, 1.0)
            sat_ratio = 1 + a.grade_strength * (float(np.clip(sat_ratio, 0.6, 1.6)) - 1)
            gfilter = grade_filter(ks, ms, mt, sat_ratio) + ","
        else:
            gfilter = ""  # referências têm fundos diferentes: sem grade global

        # legendas
        vf_tail = ""
        if cap.get("enabled") and not a.no_captions and info["has_audio"]:
            if a.words_json:
                import json as _json
                words = [(float(s), float(e), str(t)) for s, e, t in
                         _json.loads(Path(a.words_json).read_text())]
            else:
                print("Transcrevendo (primeira vez baixa o modelo)...")
                words = transcribe(cur, a.lang, a.whisper_model)
            if words:
                (work / "fonts").mkdir()
                for f in FONT_DIR.glob("*"):
                    if f.suffix.lower() in (".ttf", ".otf", ".ttc"):
                        shutil.copy(f, work / "fonts" / f.name)
                fam = build_ass(words, cap, W, H, work / "subs.ass")
                warn_font(cap, fam)
                vf_tail = ",ass=subs.ass:fontsdir=fonts"
            else:
                print("Nenhuma fala detectada; sem legendas.")

        # vídeo
        if a.fit == "blur":
            head = (f"[0:v]split[a][b];[a]scale={W}:{H}:force_original_aspect_ratio=increase,"
                    f"crop={W}:{H},boxblur=30:5[bg];[b]scale={W}:{H}:"
                    f"force_original_aspect_ratio=decrease[fg];[bg][fg]overlay=(W-w)/2:(H-h)/2")
        else:
            head = f"[0:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H}"
        graph = f"{head},fps={FPS},setsar=1,{gfilter}format=yuv420p{vf_tail}[v]"
        (work / "graph.txt").write_text(graph)

        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(cur),
               "-filter_complex", graph, "-map", "[v]"]
        if info["has_audio"]:
            cmd += ["-map", "0:a:0"]
            if prof.get("audio"):
                cmd += ["-af", f"loudnorm=I={prof['audio']['lufs']}:TP={prof['audio']['true_peak']}:LRA=11"]
            cmd += ["-c:a", "aac", "-b:a", "192k", "-ar", "48000"]
        cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "16",
                "-movflags", "+faststart", str(out)]
        print("Renderizando...")
        r = run(cmd, cwd=work)
        if r.returncode != 0:
            raise SystemExit("Erro no ffmpeg:\n" + r.stderr)
        print(f"\nOK -> {out}")
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
