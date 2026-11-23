#!/usr/bin/env python3
"""Fotos reais e logos oficiais para as cenas.

Fontes de fotos reais (CC0 e domínio público por padrão; --allow-cc-by inclui CC BY e
CC BY-SA, que exigem o crédito do campo "credit" na legenda do post):
  wikimedia — Wikimedia Commons (rápido, acervo enorme)
  openverse — Openverse (às vezes fica lento ou fora do ar)
  logos     — logos oficiais do Simple Icons (CC0) já inclusos em assets/logos

uso:
  images.py search "smartphone camera" [--source all|wikimedia|openverse] [--limit 10] [--allow-cc-by] [--orientation tall|wide|square]
  images.py fetch URL DESTINO.jpg      # baixa, converte para JPG e limita a 1400 px
  images.py logos                      # lista os logos disponíveis (use o nome em "logos", "logo")

Busque em inglês: o acervo do Openverse é quase todo indexado em inglês.
As marcas são propriedade dos donos: use os logos só para citar a plataforma, sem sugerir parceria.
"""
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LOGOS = ROOT / "assets" / "logos"


def lic_ok(name, allow_cc_by):
    n = (name or "").lower().replace("-", " ")
    if n in ("cc0", "pdm") or n.startswith("cc0") or "public domain" in n or n == "pd":
        return True
    return allow_cc_by and n.startswith(("cc by", "by"))


def shape(w, h, orientation):
    if not orientation or not (w and h):
        return True
    r = w / h
    return {"tall": r < .9, "wide": r > 1.15, "square": .9 <= r <= 1.15}[orientation]


def search_wikimedia(query, limit=10, allow_cc_by=False, orientation=None):
    import re
    cmd = ["curl", "-fsSG", "--max-time", "30", "https://commons.wikimedia.org/w/api.php",
           "--data-urlencode", "action=query", "--data-urlencode", "format=json",
           "--data-urlencode", "generator=search", "--data-urlencode", "gsrnamespace=6",
           "--data-urlencode", f"gsrsearch={query} filetype:bitmap", "--data-urlencode", "gsrlimit=50",
           "--data-urlencode", "prop=imageinfo", "--data-urlencode", "iiprop=url|size|extmetadata",
           "--data-urlencode", "iiurlwidth=1400", "-H", "User-Agent: skill-recorte-retangulo/1.0"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode:
        return None
    pages = sorted(json.loads(r.stdout).get("query", {}).get("pages", {}).values(), key=lambda p: p.get("index", 0))
    out = []
    for p in pages:
        ii = (p.get("imageinfo") or [{}])[0]
        m = ii.get("extmetadata", {})
        lic = m.get("LicenseShortName", {}).get("value", "")
        w, h = ii.get("width") or 0, ii.get("height") or 0
        if not lic_ok(lic, allow_cc_by) or min(w, h) < 500 or not shape(w, h, orientation):
            continue
        artist = re.sub(r"<[^>]+>", "", m.get("Artist", {}).get("value", "")).strip() or "autor desconhecido"
        title = p["title"].removeprefix("File:").rsplit(".", 1)[0]
        out.append({"source": "wikimedia", "title": title, "url": ii.get("thumburl") or ii.get("url"),
                    "size": f"{w}x{h}", "license": lic, "credit": f"{title} — {artist[:60]} ({lic}, Wikimedia Commons)",
                    "page": ii.get("descriptionurl")})
        if len(out) >= limit:
            break
    return out


def search_openverse(query, limit=10, allow_cc_by=False, orientation=None):
    ok_lic = {"cc0", "pdm"} | ({"by"} if allow_cc_by else set())
    base = ["curl", "-fsSG", "--max-time", "40", "https://api.openverse.org/v1/images/",
            "--data-urlencode", f"q={query}", "-H", "User-Agent: skill-recorte-retangulo"]
    if orientation:
        base += ["--data-urlencode", f"aspect_ratio={orientation}"]
    # a API às vezes demora (504) com filtro de licença: tenta com filtro, depois sem e filtra aqui
    tries = [["--data-urlencode", "license=" + ",".join(sorted(ok_lic)), "--data-urlencode", f"page_size={max(limit * 2, 10)}"]] * 2 + \
            [["--data-urlencode", "page_size=80"]] * 2
    data = None
    for extra in tries:
        r = subprocess.run(base + extra, capture_output=True, text=True)
        if not r.returncode:
            data = json.loads(r.stdout)
            break
    if data is None:
        return None
    out = []
    for it in data.get("results", []):
        if it.get("license") not in ok_lic or it.get("mature"):
            continue
        w, h = it.get("width") or 0, it.get("height") or 0
        if w and h and min(w, h) < 500 or not shape(w, h, orientation):
            continue
        out.append({"source": "openverse", "title": it.get("title"), "url": it.get("url"), "thumbnail": it.get("thumbnail"),
                    "size": f"{w}x{h}" if w else "?", "license": f"{it.get('license')} {it.get('license_version') or ''}".strip(),
                    "credit": f"{it.get('title')} — {it.get('creator') or 'autor desconhecido'} ({it.get('license')})",
                    "page": it.get("foreign_landing_url")})
        if len(out) >= limit:
            break
    return out


def fetch(url, dest):
    dest = Path(dest).expanduser().resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "raw"
        subprocess.run(["curl", "-fsSL", "--max-time", "90", "-A", "skill-recorte-retangulo", "-o", str(raw), url], check=True)
        r = subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(raw), "-frames:v", "1",
                            "-vf", "scale='min(1400,iw)':-2", "-q:v", "3", str(dest.with_suffix(".jpg"))],
                           capture_output=True, text=True)
        if r.returncode:
            sys.exit("O arquivo baixado não é uma imagem válida:\n" + r.stderr)
    print(dest.with_suffix(".jpg"))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--source", choices=["all", "wikimedia", "openverse"], default="all")
    s.add_argument("--limit", type=int, default=10)
    s.add_argument("--allow-cc-by", action="store_true")
    s.add_argument("--orientation", choices=["tall", "wide", "square"])
    f = sub.add_parser("fetch")
    f.add_argument("url")
    f.add_argument("dest")
    sub.add_parser("logos")
    a = ap.parse_args()
    if a.cmd == "search":
        res, failed = [], []
        for name, fn in (("wikimedia", search_wikimedia), ("openverse", search_openverse)):
            if a.source in ("all", name):
                got = fn(a.query, a.limit, a.allow_cc_by, a.orientation)
                if got is None:
                    failed.append(name)
                else:
                    res += got
        if failed and not res:
            sys.exit(f"Sem resposta de: {', '.join(failed)}. Verifique a internet e tente de novo.")
        if failed:
            print(f"Aviso: {', '.join(failed)} não respondeu; mostrando as outras fontes.", file=sys.stderr)
        if not res:
            print("Nada com licença livre. Tente outros termos em inglês ou --allow-cc-by.", file=sys.stderr)
        print(json.dumps(res, ensure_ascii=False, indent=1))
    elif a.cmd == "fetch":
        fetch(a.url, a.dest)
    else:
        meta = json.loads((LOGOS / "logos.json").read_text())
        for name in sorted(p.stem for p in LOGOS.glob("*.svg")):
            print(f"{name:14} {meta.get(name, {}).get('title', '')}  {meta.get(name, {}).get('hex', '')}")


if __name__ == "__main__":
    main()
