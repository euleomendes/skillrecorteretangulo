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

Imagens oficiais (material de divulgação das próprias marcas, para ilustrar notícias e
comentários sobre o produto; não são livres: cite a fonte e não sugira parceria):
  images.py official tiktok            # sites oficiais, newsroom e central de ajuda da marca
  images.py app "capcut" [--fetch PASTA] [--n 6] [--country br]
                                       # ícone e telas oficiais do app na App Store
  images.py page URL [--fetch PASTA] [--n 8] [--min 500]
                                       # imagens de uma página oficial (og:image e fotos grandes)
  images.py shot URL PASTA/print.jpg [--mobile|--desktop] [--full] [--wait 2.5]
                                       # print real da página oficial (Playwright)
  images.py logo capcut [--app "capcut"]
                                       # adiciona um logo oficial à skill: Simple Icons (vetor, 3 mil+
                                       # marcas) ou, se não houver, o ícone oficial do app na App Store

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


UA_BROWSER = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
              "(KHTML, like Gecko) Chrome/131.0 Safari/537.36")

# Onde procurar material oficial de cada marca (newsroom = anúncios com imagens de divulgação)
OFFICIAL = {
    "tiktok": {"site": "https://www.tiktok.com", "newsroom": "https://newsroom.tiktok.com/pt-br",
               "ajuda": "https://support.tiktok.com/pt_BR", "app": "tiktok"},
    "capcut": {"site": "https://www.capcut.com/pt-br", "novidades": "https://www.capcut.com/pt-br/resource",
               "app": "capcut"},
    "instagram": {"site": "https://about.instagram.com/pt-br", "blog": "https://about.instagram.com/pt-br/blog",
                  "criadores": "https://creators.instagram.com", "ajuda": "https://help.instagram.com", "app": "instagram"},
    "facebook": {"newsroom": "https://about.fb.com/br/news/", "criadores": "https://www.facebook.com/creators",
                 "ajuda": "https://www.facebook.com/help", "app": "facebook"},
    "meta": {"newsroom": "https://about.fb.com/br/news/", "ia": "https://ai.meta.com/blog/", "app": "meta ai"},
    "whatsapp": {"site": "https://www.whatsapp.com", "blog": "https://blog.whatsapp.com", "app": "whatsapp messenger"},
    "threads": {"site": "https://about.instagram.com/pt-br/blog", "app": "threads"},
    "youtube": {"blog": "https://blog.youtube", "criadores": "https://www.youtube.com/creators", "app": "youtube"},
    "google": {"blog": "https://blog.google", "app": "google"},
    "gemini": {"site": "https://gemini.google.com", "blog": "https://blog.google/products/gemini/", "app": "google gemini"},
    "chatgpt": {"site": "https://openai.com/chatgpt", "news": "https://openai.com/news/", "app": "chatgpt"},
    "openai": {"news": "https://openai.com/news/", "app": "chatgpt"},
    "claude": {"site": "https://www.anthropic.com/claude", "news": "https://www.anthropic.com/news", "app": "claude by anthropic"},
    "canva": {"site": "https://www.canva.com/pt_br/", "novidades": "https://www.canva.com/newsroom/news/", "app": "canva"},
    "linkedin": {"news": "https://news.linkedin.com", "app": "linkedin"},
    "x": {"blog": "https://blog.x.com", "app": "x"},
    "spotify": {"newsroom": "https://newsroom.spotify.com", "app": "spotify"},
    "netflix": {"newsroom": "https://about.netflix.com/pt_br/newsroom", "app": "netflix"},
    "apple": {"newsroom": "https://www.apple.com/br/newsroom/"},
    "pinterest": {"newsroom": "https://newsroom.pinterest.com", "app": "pinterest"},
    "kwai": {"site": "https://www.kwai.com", "app": "kwai"},
    "mercadolivre": {"site": "https://www.mercadolivre.com.br", "app": "mercado livre"},
    "shopee": {"site": "https://shopee.com.br", "app": "shopee"},
}


def slug(t):
    import re
    import unicodedata
    t = unicodedata.normalize("NFKD", t).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", t).strip("-") or "img"


def curl_text(url, timeout=40):
    r = subprocess.run(["curl", "-fsSL", "--compressed", "--max-time", str(timeout), "-A", UA_BROWSER,
                        "-H", "Accept-Language: pt-BR,pt;q=0.9,en;q=0.8", url], capture_output=True)
    if r.returncode:
        return None
    return r.stdout.decode("utf-8", "replace")


def img_size(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=width,height",
                        "-of", "csv=p=0", str(path)], capture_output=True, text=True)
    try:
        w, h = r.stdout.strip().split("\n")[0].split(",")[:2]
        return int(w), int(h)
    except ValueError:
        return 0, 0


def fetch_quiet(url, dest, min_side=0):
    """Baixa e converte para JPG; devolve (caminho, w, h) ou None se falhar ou for pequena."""
    dest = Path(dest).expanduser().resolve().with_suffix(".jpg")
    dest.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        raw = Path(tmp) / "raw"
        if subprocess.run(["curl", "-fsSL", "--max-time", "60", "-A", UA_BROWSER, "-o", str(raw), url]).returncode:
            return None
        w, h = img_size(raw)
        if not w or max(w, h) < min_side:
            return None
        r = subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(raw), "-frames:v", "1",
                            "-vf", "scale='min(1400,iw)':-2", "-q:v", "3", str(dest)], capture_output=True)
        if r.returncode:
            return None
    return str(dest), w, h


def app_store(query, country="br", limit=3):
    import re
    import urllib.parse
    url = ("https://itunes.apple.com/search?" + urllib.parse.urlencode(
        {"term": query, "entity": "software", "country": country, "limit": limit}))
    txt = curl_text(url)
    if txt is None:
        sys.exit("A App Store não respondeu. Verifique a internet e tente de novo.")
    out = []
    for it in json.loads(txt).get("results", []):
        out.append({"name": it.get("trackName"), "seller": it.get("sellerName"),
                    "icon": (it.get("artworkUrl512") or it.get("artworkUrl100") or "").replace("512x512bb", "1024x1024bb"),
                    "screenshots": [re.sub(r"/\d+x\d+\w*\.(jpg|png|webp)$", "/1290x0w.jpg", u)
                                    for u in it.get("screenshotUrls") or it.get("ipadScreenshotUrls") or []],
                    "page": it.get("trackViewUrl"), "source": "App Store (material oficial do app)"})
    return out


def page_images(url):
    import html as H
    import re
    from urllib.parse import urljoin
    txt = curl_text(url)
    if txt is None:
        return page_images_browser(url)
    found = []
    def add(u, kind):
        u = H.unescape(u.strip())
        if not u or u.startswith("data:") or re.search(r"\.svg(\?|$)", u, re.I):
            return
        u = urljoin(url, u)
        if u not in [f["url"] for f in found]:
            found.append({"url": u, "kind": kind})
    for m in re.finditer(r'<meta[^>]+(?:property|name)=["\'](og:image(?::secure_url)?|twitter:image(?::src)?)["\'][^>]*>', txt, re.I):
        c = re.search(r'content=["\']([^"\']+)', m.group(0), re.I)
        if c:
            add(c.group(1), "capa (og:image)")
    for m in re.finditer(r'<img\b[^>]*>', txt, re.I):
        tag = m.group(0)
        ss = re.search(r'srcset=["\']([^"\']+)', tag, re.I)
        if ss:
            best = sorted(((int(w or 0), u) for u, w in re.findall(r'(\S+)\s+(\d+)w', ss.group(1))), reverse=True)
            if best:
                add(best[0][1], "foto da página")
                continue
        src = re.search(r'(?:data-src|src)=["\']([^"\']+)', tag, re.I)
        if src:
            add(src.group(1), "foto da página")
    if len(found) < 2:  # página montada por JavaScript: abre no navegador
        found += [f for f in page_images_browser(url) if f["url"] not in [x["url"] for x in found]]
    return found


def page_images_browser(url):
    """Abre a página no Chromium (Playwright), rola e coleta og:image e as fotos grandes já carregadas."""
    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as p:
            b = p.chromium.launch()
            pg = b.new_page(viewport={"width": 1280, "height": 900}, locale="pt-BR", user_agent=UA_BROWSER)
            pg.goto(url, wait_until="domcontentloaded", timeout=60000)
            pg.wait_for_timeout(2500)
            for _ in range(6):
                pg.mouse.wheel(0, 1400)
                pg.wait_for_timeout(500)
            items = pg.evaluate("""() => {
              const out = [];
              document.querySelectorAll('meta[property^="og:image"],meta[name^="twitter:image"]')
                .forEach(m => m.content && out.push({url: m.content, kind: 'capa (og:image)'}));
              document.querySelectorAll('img').forEach(i => {
                const u = i.currentSrc || i.src;
                if (u && !u.startsWith('data:') && !/\\.svg(\\?|$)/i.test(u) && i.naturalWidth >= 300)
                  out.push({url: u, kind: 'foto da página', w: i.naturalWidth, h: i.naturalHeight});
              });
              return out;
            }""")
            b.close()
    except Exception as e:
        print(f"Aviso: não consegui abrir {url} no navegador ({e.__class__.__name__}).", file=sys.stderr)
        return []
    seen, out = set(), []
    for it in items:
        if it["url"] not in seen:
            seen.add(it["url"])
            out.append(it)
    return out


def shot(url, dest, mobile=True, full=False, wait=2.5):
    from playwright.sync_api import sync_playwright
    dest = Path(dest).expanduser().resolve()
    dest.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        b = p.chromium.launch()
        ctx = b.new_context(viewport={"width": 390, "height": 844} if mobile else {"width": 1280, "height": 800},
                            device_scale_factor=3 if mobile else 2, is_mobile=mobile, has_touch=mobile,
                            locale="pt-BR", user_agent=None if not mobile else
                            "Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 "
                            "(KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1")
        pg = ctx.new_page()
        pg.goto(url, wait_until="domcontentloaded", timeout=60000)
        pg.wait_for_timeout(int(wait * 1000))
        # fecha avisos de cookies recusando o que não é essencial, quando houver o botão
        for label in ("Recusar", "Rejeitar", "Recusar todos", "Rejeitar todos", "Apenas essenciais",
                      "Decline", "Reject all", "Only allow essential cookies"):
            btn = pg.get_by_role("button", name=label, exact=False)
            if btn.count():
                try:
                    btn.first.click(timeout=1500)
                    pg.wait_for_timeout(600)
                    break
                except Exception:
                    pass
        png = dest.with_suffix(".png")
        pg.screenshot(path=str(png), full_page=full)
        b.close()
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(png), "-q:v", "2",
                    str(dest.with_suffix(".jpg"))], check=True)
    png.unlink()
    print(dest.with_suffix(".jpg"))


SI_VER = "16.38.1"


def add_logo(name, app_query=None):
    """Salva em assets/logos: <slug>.svg (Simple Icons) ou <slug>.jpg (ícone oficial do app)."""
    key = slug(name).replace("-", "")
    data = curl_text(f"https://cdn.jsdelivr.net/npm/simple-icons@{SI_VER}/data/simple-icons.json")
    meta_p = LOGOS / "logos.json"
    meta = json.loads(meta_p.read_text()) if meta_p.is_file() else {}
    if data and not app_query:
        icons = json.loads(data)
        hit = next((i for i in icons if i["slug"] == key), None) or next(
            (i for i in icons if slug(i["title"]).replace("-", "") == key), None)
        if hit:
            svg = curl_text(f"https://cdn.jsdelivr.net/npm/simple-icons@{SI_VER}/icons/{hit['slug']}.svg")
            if svg and "<path" in svg:
                (LOGOS / f"{key}.svg").write_text(svg)
                meta[key] = {"title": hit["title"], "hex": "#" + hit["hex"], "source": hit.get("source", "")}
                meta_p.write_text(json.dumps(dict(sorted(meta.items())), ensure_ascii=False, indent=1) + "\n")
                print(json.dumps({"logo": key, "type": "vetor (Simple Icons)", "title": hit["title"]},
                                 ensure_ascii=False))
                return
    res = app_store(app_query or name)
    if not res:
        sys.exit(f"Não achei '{name}' no Simple Icons nem na App Store. Tente --app com o nome do app.")
    g = fetch_quiet(res[0]["icon"], LOGOS / f"{key}.jpg")
    if not g:
        sys.exit("Falhou ao baixar o ícone do app.")
    subprocess.run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", g[0], "-vf", "scale=256:256",
                    "-q:v", "2", g[0]], check=True)
    meta[key] = {"title": res[0]["name"], "hex": "#ffffff", "source": res[0]["page"], "kind": "app-icon"}
    meta_p.write_text(json.dumps(dict(sorted(meta.items())), ensure_ascii=False, indent=1) + "\n")
    print(json.dumps({"logo": key, "type": "ícone do app (App Store)", "title": res[0]["name"],
                      "seller": res[0]["seller"]}, ensure_ascii=False))


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
    lg = sub.add_parser("logo")
    lg.add_argument("name")
    lg.add_argument("--app", help="força o ícone do app com esta busca na App Store")
    o = sub.add_parser("official")
    o.add_argument("brand", nargs="?")
    ap_ = sub.add_parser("app")
    ap_.add_argument("query")
    ap_.add_argument("--fetch", metavar="PASTA")
    ap_.add_argument("--n", type=int, default=6, help="quantas telas baixar")
    ap_.add_argument("--country", default="br")
    pg = sub.add_parser("page")
    pg.add_argument("url")
    pg.add_argument("--fetch", metavar="PASTA")
    pg.add_argument("--n", type=int, default=8)
    pg.add_argument("--min", type=int, default=500, help="menor lado mínimo (px) para baixar")
    sh = sub.add_parser("shot")
    sh.add_argument("url")
    sh.add_argument("dest")
    g = sh.add_mutually_exclusive_group()
    g.add_argument("--mobile", action="store_true", default=True)
    g.add_argument("--desktop", action="store_true")
    sh.add_argument("--full", action="store_true", help="página inteira (rolagem)")
    sh.add_argument("--wait", type=float, default=2.5)
    a = ap.parse_args()
    if a.cmd == "logo":
        add_logo(a.name, a.app)
        return
    if a.cmd == "official":
        k = slug(a.brand).replace("-", "") if a.brand else None
        sel = {k: OFFICIAL[k]} if k in OFFICIAL else OFFICIAL
        if a.brand and k not in OFFICIAL:
            print(f"Sem atalho para '{a.brand}'. Procure o site oficial na web e use page/shot. Marcas com atalho:",
                  file=sys.stderr)
        print(json.dumps(sel, ensure_ascii=False, indent=1))
        return
    if a.cmd == "app":
        res = app_store(a.query, a.country)
        if not res:
            sys.exit("Nenhum app encontrado. Tente o nome em inglês ou outro país (--country us).")
        if not a.fetch:
            print(json.dumps(res, ensure_ascii=False, indent=1))
            return
        top, base = res[0], slug(res[0]["name"])[:24]
        got = [fetch_quiet(top["icon"], Path(a.fetch) / f"{base}_icone")]
        for i, u in enumerate(top["screenshots"][:a.n], 1):
            got.append(fetch_quiet(u, Path(a.fetch) / f"{base}_tela{i}"))
        print(json.dumps({"app": top["name"], "seller": top["seller"], "source": top["source"],
                          "files": [{"path": g[0], "w": g[1], "h": g[2]} for g in got if g]},
                         ensure_ascii=False, indent=1))
        return
    if a.cmd == "page":
        res = page_images(a.url)
        if not a.fetch:
            print(json.dumps(res[:40], ensure_ascii=False, indent=1))
            return
        base, files = slug(a.url.split("//")[-1])[:30], []
        for it in res:
            if len(files) >= a.n:
                break
            g = fetch_quiet(it["url"], Path(a.fetch) / f"{base}_{len(files) + 1}", a.min)
            if g:
                files.append({"path": g[0], "w": g[1], "h": g[2], "kind": it["kind"], "url": it["url"]})
        if not files:
            print("Nenhuma imagem grande na página (o site pode carregar as fotos por JavaScript). "
                  "Use images.py shot para um print.", file=sys.stderr)
        print(json.dumps({"source": a.url, "files": files}, ensure_ascii=False, indent=1))
        return
    if a.cmd == "shot":
        shot(a.url, a.dest, mobile=not a.desktop, full=a.full, wait=a.wait)
        return
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
        for name in sorted({p.stem for p in LOGOS.glob("*.svg")} | {p.stem for p in LOGOS.glob("*.jpg")}):
            print(f"{name:14} {meta.get(name, {}).get('title', '')}  {meta.get(name, {}).get('hex', '')}")


if __name__ == "__main__":
    main()
