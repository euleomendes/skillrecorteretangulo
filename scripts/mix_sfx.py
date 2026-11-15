"""Monta uma faixa mono de efeitos a partir de arquivos locais licenciados."""
import json
import math
import subprocess
import wave
from pathlib import Path

import numpy as np

RATE = 48000

def build_track(manifest, output, duration):
    manifest = Path(manifest).resolve()
    track = np.zeros(round(duration * RATE), dtype=np.float32)
    for cue in json.loads(manifest.read_text()):
        start = round(float(cue["time"]) * RATE)
        limit = float(cue.get("duration", .5))
        peak_db = float(cue.get("peak_db", -24))
        if not 0 <= start < len(track) or not .03 <= limit <= 5 or not -50 <= peak_db <= -6:
            raise ValueError(f"Efeito fora dos limites: {cue}")
        asset = manifest.parent / cue["file"]
        cmd = ["ffmpeg", "-v", "error", "-ss", str(cue.get("offset", 0)), "-i", str(asset),
               "-t", str(limit), "-af", "highpass=f=85", "-ac", "1", "-ar", str(RATE), "-f", "f32le", "-"]
        clip = np.frombuffer(subprocess.check_output(cmd), dtype="<f4").copy()
        clip = clip[:len(track) - start]
        if not len(clip):
            raise ValueError(f"Efeito sem áudio: {asset}")
        t = np.arange(len(clip)) / RATE
        clip *= np.minimum(1, t / .004) * np.minimum(1, (t[-1] - t) / .035)
        peak = float(np.max(np.abs(clip)))
        if peak > 0 and math.isfinite(peak):
            track[start:start+len(clip)] += clip * (10 ** (peak_db / 20) / peak)
    with wave.open(str(output), "wb") as audio:
        audio.setparams((1, 2, RATE, len(track), "NONE", "not compressed"))
        audio.writeframes((np.clip(track, -1, 1) * 32767).astype("<i2").tobytes())
