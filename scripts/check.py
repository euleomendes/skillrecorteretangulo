#!/usr/bin/env python3
"""Confere se a skill está pronta para editar: programas, bibliotecas, navegador,
fontes, modelo de recorte e sons. Rode com o Python da .venv:

    .venv/bin/python scripts/check.py
"""
import importlib
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ok = True


def item(good, label, fix=""):
    global ok
    ok &= bool(good)
    print(("  ✓ " if good else "  ✗ ") + label + ("" if good or not fix else f"\n      → {fix}"))


print("Skill Recorte Retângulo — verificação\n")
item(sys.version_info >= (3, 10), f"Python {platform.python_version()}", "use Python 3.10 ou mais novo")
item(Path(sys.prefix).resolve() == (ROOT / ".venv").resolve(), "rodando pela .venv da skill",
     "rode `bash scripts/setup.sh` e use `.venv/bin/python`")

for prog in ("ffmpeg", "ffprobe", "curl"):
    item(shutil.which(prog), prog, "instale (macOS: `brew install ffmpeg curl`; Ubuntu: `sudo apt install ffmpeg curl`)")
if shutil.which("ffmpeg"):
    filt = subprocess.run(["ffmpeg", "-hide_banner", "-filters"], capture_output=True, text=True).stdout
    item(any(l.split()[1:2] == ["ass"] for l in filt.splitlines()), "ffmpeg com libass (legendas)",
         "instale um ffmpeg com libass (o do Homebrew e o do apt já têm)")

for mod in ("numpy", "PIL", "cv2", "onnxruntime", "faster_whisper", "playwright"):
    try:
        importlib.import_module(mod)
        item(True, f"biblioteca {mod}")
    except Exception as error:
        item(False, f"biblioteca {mod} ({error.__class__.__name__})", "rode `bash scripts/setup.sh`")

try:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        p.chromium.launch().close()
    item(True, "navegador Chromium (Playwright)")
except Exception as error:
    item(False, f"navegador Chromium ({str(error).splitlines()[0][:90]})",
         "rode `.venv/bin/python -m playwright install chromium` (Linux: `--with-deps`)")

fonts = ROOT / "assets" / "fonts"
for f in ("Inter-ExtraBold.otf", "Inter-SemiBold.otf", "Inter-Medium.otf", "InstrumentSerif-Italic.ttf"):
    item((fonts / f).is_file() and (fonts / f).stat().st_size > 0, f"fonte {f}", "rode `bash scripts/setup.sh`")
if platform.system() != "Darwin":
    item((fonts / "NotoColorEmoji-Regular.ttf").is_file(), "fonte de emoji Noto Color Emoji", "rode `bash scripts/setup.sh`")

model = ROOT / "models" / "u2net_human_seg.onnx"
item(model.is_file() and model.stat().st_size == 175997641, "modelo de recorte U2Net", "rode `bash scripts/setup.sh`")
item((ROOT / "analysis" / "style_profile.json").is_file(), "perfil de estilo (analysis/style_profile.json)",
     "restaure o arquivo do repositório")

kit = ROOT / "sfx" / "real" / "manifest.json"
if kit.is_file():
    rows = json.loads(kit.read_text())
    miss = [r for r in rows if not (kit.parent / r["file"]).is_file()]
    item(not miss, f"kit de gravações reais ({len(rows) - len(miss)}/{len(rows)})", "restaure sfx/real do repositório")
else:
    item(False, "kit de gravações reais", "restaure sfx/real do repositório")

logos = list((ROOT / "assets" / "logos").glob("*.svg"))
item(len(logos) >= 30 and (ROOT / "assets" / "logos" / "logos.json").is_file(), f"logos oficiais ({len(logos)})",
     "restaure assets/logos do repositório")

man = ROOT / "sfx" / "realsfx" / "manifest.json"
if man.is_file():
    assets = json.loads(man.read_text())["assets"]
    missing = [a for a in assets if not (ROOT / "sfx" / "realsfx" / a["files"]["mp3"]["path"]).is_file()]
    item(not missing, f"sons uisfx sintetizados ({len(assets) - len(missing)}/{len(assets)})", "restaure sfx/realsfx do repositório")
else:
    item(False, "sons uisfx sintetizados", "restaure sfx/realsfx do repositório")

print("\nTudo pronto." if ok else "\nCorrija os itens marcados com ✗ e rode de novo.")
sys.exit(0 if ok else 1)
