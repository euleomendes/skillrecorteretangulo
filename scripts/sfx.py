#!/usr/bin/env python3
"""Busca efeitos sonoros em duas fontes e baixa os escolhidos.

Fontes:
  kit       — GRAVAÇÕES REAIS escolhidas e tratadas, em sfx/real/ (Freesound, CC0). Use sempre primeiro.
  openverse — API pública do Openverse: gravações reais do Freesound (CC0 por padrão; --allow-cc-by inclui CC BY)
  uisfx     — pacote uisfx do Real SFX em sfx/realsfx/ (CC0). São sons SINTETIZADOS de interface:
              soam artificiais em vídeo. Só use se o usuário pedir esse estilo.

uso:
  sfx.py search "whoosh" [--source all|kit|openverse|uisfx] [--pack cinematic] [--limit 8] [--allow-cc-by]
  sfx.py kit                         # lista o kit de gravações reais
  sfx.py packs
  sfx.py fetch URL DESTINO.mp3        # baixa um efeito do Openverse já escolhido
"""
import argparse
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REAL = ROOT / "sfx" / "realsfx"
KIT = ROOT / "sfx" / "real"

# termos comuns (pt/en) -> cues do Real SFX
SYN = {
    "whoosh": ["swipe", "open", "forward", "expand"], "swoosh": ["swipe", "forward"],
    "transicao": ["swipe", "forward", "open"], "transition": ["swipe", "forward", "open"],
    "pop": ["select", "reaction", "badge", "drop"], "bolha": ["reaction", "select"],
    "click": ["press", "select", "release"], "clique": ["press", "select", "release"], "tap": ["press", "select"],
    "ding": ["success", "notification", "complete"], "sino": ["notification", "success"], "chime": ["notification", "success"],
    "check": ["check", "success", "complete"], "sucesso": ["success", "complete", "achievement"],
    "erro": ["error", "invalid-drop", "blocked"], "alerta": ["warning", "error"], "atencao": ["warning"],
    "digitar": ["typing"], "teclado": ["typing"], "typing": ["typing"],
    "impacto": ["drop", "snap", "lock"], "hit": ["drop", "snap"], "stamp": ["lock", "snap", "drop"], "carimbo": ["lock", "snap"],
    "dinheiro": ["purchase", "coupon", "checkout"], "moeda": ["coupon", "reward", "purchase"], "coin": ["coupon", "reward"],
    "conquista": ["achievement", "level-up", "reward"], "subir": ["level-up", "progress-step"], "riser": ["level-up", "start"],
    "notificacao": ["notification", "receive", "mention"], "mensagem": ["send", "receive"],
    "contador": ["progress-step", "checkpoint"], "lista": ["progress-step", "check"],
}


def fold(text):
    text = unicodedata.normalize("NFKD", str(text).lower())
    return "".join(c for c in text if not unicodedata.combining(c))


def search_real(query, pack=None, limit=8):
    man = json.loads((REAL / "manifest.json").read_text())
    cues = {c["name"]: c for c in man["cues"]}
    words = re.findall(r"[\w-]+", fold(query))
    wanted = {}
    for w in words:
        wanted[w] = max(wanted.get(w, 0), 5)
        for i, s in enumerate(SYN.get(w, [])):
            wanted[s] = max(wanted.get(s, 0), 4 - i)
    out = []
    for a in man["assets"]:
        if pack and a["pack"] != pack:
            continue
        c = cues.get(a["cue"], {})
        hay = fold(" ".join([a["cue"], c.get("label", ""), c.get("description", ""), a["category"], a["pack"]]))
        score = sum(wt * 2 if w == a["cue"] else wt * .5 for w, wt in wanted.items() if w in hay)
        path = REAL / a["files"]["mp3"]["path"]
        if score and path.exists():
            out.append((score, {"source": "uisfx (sintetizado)", "title": f"{a['pack']}/{a['cue']}", "path": str(path),
                                "duration": a["duration"], "description": c.get("description"),
                                "license": "cc0", "credit": "uisfx (Real SFX) — CC0, sintetizado"}))
    # varia os estilos: o melhor de cada pack antes de repetir
    out.sort(key=lambda x: -x[0])
    seen, first, rest = set(), [], []
    for s, r in out:
        key = r["title"].split("/")[0]
        (rest if key in seen else first).append(r)
        seen.add(key)
    return (first + rest)[:limit]


# termos (pt/en) -> pastas do kit real
KIT_SYN = {
    "whoosh": ["whoosh", "swish"], "swoosh": ["whoosh", "swish"], "transicao": ["whoosh"], "transition": ["whoosh"],
    "swish": ["swish"], "swipe": ["swish", "whoosh"], "pop": ["pop"], "bolha": ["pop"], "bubble": ["pop"],
    "click": ["click"], "clique": ["click"], "botao": ["click"], "button": ["click"], "cursor": ["click"],
    "digitar": ["typing"], "teclado": ["typing"], "typing": ["typing"], "keyboard": ["typing"],
    "foto": ["shutter", "paper"], "camera": ["shutter"], "shutter": ["shutter"], "papel": ["paper"], "paper": ["paper"],
    "polaroid": ["paper", "shutter"], "cartao": ["paper"], "card": ["paper"],
    "dinheiro": ["coins"], "moeda": ["coins"], "coin": ["coins"], "money": ["coins"], "pix": ["coins", "notify"],
    "notificacao": ["notify"], "notification": ["notify"], "ding": ["notify", "chime"], "sino": ["chime", "notify"],
    "sucesso": ["chime"], "success": ["chime"], "conquista": ["chime"], "chime": ["chime"],
    "carimbo": ["stamp", "hit"], "stamp": ["stamp", "hit"], "impacto": ["hit"], "impact": ["hit"], "hit": ["hit"],
    "alerta": ["hit"], "atencao": ["hit"], "riser": ["riser"], "subir": ["riser"], "grafico": ["riser"],
    "marcador": ["marker"], "marca-texto": ["marker"], "marker": ["marker"], "caneta": ["marker"], "sublinhado": ["marker"],
}


def search_kit(query, limit=8):
    man = json.loads((KIT / "manifest.json").read_text())
    words = re.findall(r"[\w-]+", fold(query))
    want = {}
    for w in words:
        for i, f in enumerate(KIT_SYN.get(w, [w])):
            want[f] = max(want.get(f, 0), 3 - i)
    out = []
    for m in man:
        score = want.get(m["role"], 0) + sum(1 for w in words if w in fold(m["use"] + " " + m["file"]))
        if score:
            out.append((score, {"source": "kit (gravação real)", "title": m["file"], "path": str(KIT / m["file"]),
                                "role": m["role"], "use": m["use"], "duration": m["duration"], "license": "cc0",
                                "origin": m["page"]}))
    out.sort(key=lambda x: -x[0])
    return [r for _, r in out[:limit]]


def search_openverse(query, limit=8, allow_cc_by=False):
    allowed = ("cc0", "by") if allow_cc_by else ("cc0",)
    cmd = ["curl", "-fsSG", "--max-time", "15", "https://api.openverse.org/v1/audio/",
           "--data-urlencode", f"q={query}", "--data-urlencode", f"license={','.join(allowed)}",
           "--data-urlencode", f"page_size={min(limit, 20)}",
           "-H", "User-Agent: skill-recorte-retangulo"]
    try:
        data = json.loads(subprocess.check_output(cmd))
    except (OSError, subprocess.CalledProcessError, ValueError) as error:
        print(f"Openverse indisponível ({error}). Se for limite de pedidos (429), espere alguns minutos.", file=sys.stderr)
        return []
    out = []
    for row in data.get("results", []):
        if row.get("license") not in allowed:
            continue
        dur = row.get("duration")
        out.append({"source": "openverse", "title": row.get("title"), "url": row.get("url"),
                    "duration": round(dur / 1000, 2) if dur else None, "creator": row.get("creator"),
                    "license": row.get("license"), "license_url": row.get("license_url"),
                    "page": row.get("foreign_landing_url"), "credit": row.get("attribution")})
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--source", choices=["all", "kit", "openverse", "uisfx", "realsfx"], default="all")
    s.add_argument("--pack", help="estilo do Real SFX (veja `sfx.py packs`)")
    s.add_argument("--limit", type=int, default=8)
    s.add_argument("--allow-cc-by", action="store_true")
    sub.add_parser("packs")
    sub.add_parser("kit")
    f = sub.add_parser("fetch")
    f.add_argument("url")
    f.add_argument("dest", type=Path)
    a = ap.parse_args()

    if a.cmd == "packs":
        man = json.loads((REAL / "manifest.json").read_text())
        for p in man["packs"]:
            print(f"{p['name']:<11} {p['description']}  ({p.get('bestFor', '')})")
        return
    if a.cmd == "kit":
        for m in json.loads((KIT / "manifest.json").read_text()):
            print(f"{m['file']:<22} {m['duration']:>5}s  role={m['role']:<8} {m['use']}")
        print(f"\nCaminho: {KIT}")
        return
    if a.cmd == "fetch":
        if not a.url.startswith("https://"):
            ap.error("Use a URL https do resultado do Openverse")
        a.dest.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["curl", "-fsSL", "--max-time", "60", "-o", str(a.dest), a.url], check=True)
        print(a.dest)
        return
    res = []
    if a.source in ("all", "kit"):
        res += search_kit(a.query, a.limit)
    if a.source in ("uisfx", "realsfx"):
        res += search_real(a.query, a.pack, a.limit)
    if a.source in ("all", "openverse"):
        res += search_openverse(a.query, a.limit, a.allow_cc_by)
    print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
