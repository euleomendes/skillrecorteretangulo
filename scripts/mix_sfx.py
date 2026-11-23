"""Monta a faixa estéreo de efeitos a partir de gravações locais licenciadas.

Cada item do sfx.json: {time, file, role?, align?, duration?, offset?, peak_db?, gain_db?, pitch?, pan?}

- role: whoosh | swish | hit | impact | pop | click | ui | paper | coins | notify | riser | chime |
  typing | shutter | stamp | marker | ambience.
  Define o nível padrão (pico em dBFS antes da masterização), o encaixe e a duração.
- align: "onset" encaixa o ataque do som em `time` (o silêncio do começo do arquivo é ignorado);
  "peak" encaixa o ponto mais alto em `time` (whoosh passando no corte);
  "end" faz o som terminar em `time` (riser chegando no impacto); "start" usa o arquivo como está.
- pitch: semitons. Se o mesmo arquivo se repete, cada repetição ganha uma pequena variação automática.
"""
import json
import math
import subprocess
import wave
from pathlib import Path

import numpy as np

RATE = 48000
# pico alvo (dBFS), encaixe, duração máxima (s), corte de graves (Hz)
ROLES = {
    "whoosh":  (-15, "peak", 1.6, 120),
    "swish":   (-19, "peak", 0.8, 200),
    "hit":     (-11, "onset", 2.5, 40),
    "impact":  (-11, "onset", 2.5, 40),
    "pop":     (-19, "onset", 0.6, 150),
    "click":   (-20, "onset", 0.35, 200),
    "ui":      (-20, "onset", 0.8, 200),
    "paper":   (-17, "onset", 1.0, 150),
    "coins":   (-17, "onset", 1.6, 200),
    "notify":  (-19, "onset", 1.4, 200),
    "riser":   (-17, "end", 3.5, 80),
    "chime":   (-19, "onset", 2.2, 200),
    "typing":  (-23, "onset", 1.2, 200),
    "shutter": (-19, "onset", 0.8, 150),
    "stamp":   (-13, "onset", 1.2, 60),
    "marker":  (-21, "onset", 0.7, 250),
    "ambience": (-30, "start", 30, 80),
}
VARY = [0, .45, -.4, .8, -.7, .25, -.2]


def decode(path, offset, rate_factor, hp):
    af = [f"asetrate={RATE * rate_factor:.0f}", f"aresample={RATE}"] if rate_factor != 1 else []
    if hp:
        af.append(f"highpass=f={hp}:poles=2")
    cmd = ["ffmpeg", "-v", "error", "-ss", str(offset), "-i", str(path), "-ac", "2", "-ar", str(RATE)]
    if af:
        cmd += ["-af", ",".join(af)]
    raw = subprocess.check_output(cmd + ["-f", "f32le", "-"])
    return np.frombuffer(raw, dtype="<f4").reshape(-1, 2).copy()


def envelope(x, win=.01):
    n = max(1, int(win * RATE))
    m = np.abs(x).max(axis=1)
    return np.convolve(m, np.ones(n) / n, mode="same")


def build_track(manifest, output, duration):
    manifest = Path(manifest).resolve()
    track = np.zeros((round(duration * RATE), 2), dtype=np.float32)
    uses = {}
    for cue in json.loads(manifest.read_text()):
        role = cue.get("role", "ui")
        if role not in ROLES:
            raise ValueError(f"role desconhecido em {cue}: use {', '.join(ROLES)}")
        peak_def, align_def, dur_def, hp = ROLES[role]
        peak_db = float(cue.get("peak_db", peak_def)) + float(cue.get("gain_db", 0))
        align = cue.get("align", align_def)
        limit = float(cue.get("duration", dur_def))
        if not -50 <= peak_db <= -3 or not .03 <= limit <= 30:
            raise ValueError(f"Efeito fora dos limites: {cue}")
        asset = (manifest.parent / cue["file"]).resolve()
        if not asset.is_file():
            raise ValueError(f"Arquivo de efeito não encontrado: {asset}")
        k = uses.get(asset, 0)
        uses[asset] = k + 1
        semis = float(cue.get("pitch", VARY[k % len(VARY)]))
        clip = decode(asset, cue.get("offset", 0), 2 ** (semis / 12), hp)
        if not len(clip):
            raise ValueError(f"Efeito sem áudio: {asset}")
        env = envelope(clip)
        top = float(env.max()) or 1
        if align == "onset":  # pula o silêncio inicial: o ataque cai em `time`
            first = int(np.argmax(env > top * .12))
            clip, env = clip[max(0, first - int(.004 * RATE)):], env[max(0, first - int(.004 * RATE)):]
        clip = clip[:int(limit * RATE)]
        env = env[:len(clip)]
        if align == "peak":
            anchor = int(np.argmax(env))
        elif align == "end":
            anchor = len(clip)
        else:
            anchor = 0
        start = round(float(cue["time"]) * RATE) - anchor
        if start < 0:
            clip, start = clip[-start:], 0
        clip = clip[:len(track) - start]
        if not len(clip):
            continue
        t = np.arange(len(clip)) / RATE
        fade = min(.12, t[-1] * .3) or .01
        clip *= (np.minimum(1, t / .003) * np.minimum(1, (t[-1] - t) / fade))[:, None]
        pan = float(cue.get("pan", 0))
        if pan:
            clip *= np.array([min(1, 1 - pan), min(1, 1 + pan)], dtype=np.float32)
        peak = float(np.max(np.abs(clip)))
        if peak > 0 and math.isfinite(peak):
            track[start:start + len(clip)] += clip * (10 ** (peak_db / 20) / peak)
    with wave.open(str(output), "wb") as audio:
        audio.setparams((2, 2, RATE, len(track), "NONE", "not compressed"))
        audio.writeframes((np.clip(track, -1, 1) * 32767).astype("<i2").tobytes())
