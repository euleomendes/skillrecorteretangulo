#!/usr/bin/env python3
"""Edição completa com motion graphics: corta silêncio, alinha o texto ao áudio,
renderiza o layout animado (HTML + Playwright) e compõe com legendas e áudio.

uso: motion_edit.py video.mp4 --scenes motion/scenes_leo.json --out output/final.mp4
"""
import argparse, json, os, re, shutil, sys, tempfile
from concurrent.futures import ThreadPoolExecutor
from bisect import bisect_right
from mix_sfx import build_track
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import FONT_DIR, ROOT, load_profile, probe, run
import apply_edit as AE

FPS = 30
MODEL = ROOT / "models" / "u2net_human_seg.onnx"
IMG_EXT = re.compile(r"\.(jpe?g|png|webp|gif|svg)$", re.I)


def load_logos():
    """Logos oficiais (Simple Icons, CC0) de assets/logos: {nome: {p: path SVG, hex, title}}."""
    folder = ROOT / "assets" / "logos"
    meta = json.loads((folder / "logos.json").read_text()) if (folder / "logos.json").is_file() else {}
    out = {}
    for f in sorted(folder.glob("*.svg")):
        m = re.search(r'<path[^>]*\sd="([^"]+)"', f.read_text())
        if m:
            info = meta.get(f.stem, {})
            out[f.stem] = {"p": m.group(1), "hex": info.get("hex", "#0d0d0d"), "title": info.get("title", f.stem)}
    return out


def make_cutouts(frames_dir, cuts_dir, idxs):
    """Recorte da pessoa (U2Net human seg) -> PNG RGBA por quadro."""
    import cv2, numpy as np, onnxruntime as ort
    if not MODEL.exists():
        raise SystemExit(f"Modelo de recorte ausente: {MODEL}\nRode scripts/setup.sh (baixa u2net_human_seg.onnx).")
    so = ort.SessionOptions(); so.intra_op_num_threads = 1
    sess = ort.InferenceSession(str(MODEL), so, providers=["CPUExecutionProvider"])
    name = sess.get_inputs()[0].name
    mean, std = np.array([0.485, 0.456, 0.406]), np.array([0.229, 0.224, 0.225])
    cuts_dir.mkdir(exist_ok=True)

    def one(i):
        f = frames_dir / f"f{i + 1:05d}.jpg"
        img = cv2.imread(str(f))
        h, w = img.shape[:2]
        x = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), (320, 320), interpolation=cv2.INTER_AREA)
        x = ((x.astype(np.float32) / 255. - mean) / std).transpose(2, 0, 1)[None].astype(np.float32)
        m = sess.run(None, {name: x})[0][0, 0]
        m = (m - m.min()) / (m.max() - m.min() + 1e-8)
        m = cv2.resize(m, (w, h), interpolation=cv2.INTER_CUBIC)
        a = (np.clip((m - 0.35) / 0.3, 0, 1) * 255).astype(np.uint8)
        cv2.imwrite(str(cuts_dir / f"f{i + 1:05d}.png"), np.dstack([img, a]))
        return i

    done = 0
    with ThreadPoolExecutor(max_workers=min(6, os.cpu_count() or 2)) as ex:
        for _ in ex.map(one, idxs):
            done += 1
            if done % 100 == 0:
                print(f"recorte {done}/{len(idxs)}", flush=True)


def auto_geom(frames_dir, n_frames, samples=7):
    """Mede onde está a cabeça (U2Net em alguns quadros) e calcula o enquadramento de
    cada layout: no cartão, o topo da cabeça fica em y≈460 e o rosto centralizado; no
    avatar e no PiP, o rosto preenche a janela. Devolve {} se não achar uma pessoa."""
    import cv2, numpy as np, onnxruntime as ort
    if not MODEL.exists():
        return {}
    sess = ort.InferenceSession(str(MODEL), providers=["CPUExecutionProvider"])
    name = sess.get_inputs()[0].name
    mean, std = np.array([0.485, 0.456, 0.406]), np.array([0.229, 0.224, 0.225])
    tops, cxs, hws = [], [], []
    for k in range(samples):
        i = int((k + .5) * n_frames / samples)
        img = cv2.imread(str(frames_dir / f"f{i + 1:05d}.jpg"))
        if img is None:
            continue
        h, w = img.shape[:2]
        x = cv2.resize(cv2.cvtColor(img, cv2.COLOR_BGR2RGB), (320, 320), interpolation=cv2.INTER_AREA)
        x = ((x.astype(np.float32) / 255. - mean) / std).transpose(2, 0, 1)[None].astype(np.float32)
        m = cv2.resize(sess.run(None, {name: x})[0][0, 0], (w, h)) > .5
        rows = np.where(m.sum(1) > w * .04)[0]
        if len(rows) < h * .15:
            continue
        top = int(rows[0])
        x0 = int(np.where(m[top + 3])[0].mean()) if m[top + 3].any() else w // 2
        widths, centers = [], []
        for y in range(top + int(h * .03), min(h, top + int(h * .11)), 4):
            if not m[y, x0]:
                continue
            row = m[y]
            l = x0 - np.argmin(row[x0::-1]) + 1 if not row[:x0].all() else 0
            r = x0 + np.argmin(row[x0:]) if not row[x0:].all() else w
            widths.append(r - l); centers.append((l + r) / 2)
            x0 = int((l + r) / 2)          # segue o centro da cabeça, ignora objetos ao lado
        if len(widths) < 3:
            continue
        tops.append(top); cxs.append(float(np.median(centers))); hws.append(float(np.median(widths)))
    if len(tops) < 2:
        return {}
    ht, cx, hw = float(np.median(tops)), float(np.median(cxs)), float(np.median(hws))
    hw = min(max(hw, 120), 520)
    fy = ht + .8 * hw                      # centro aproximado do rosto
    clamp = lambda v, a, b: min(max(v, a), b)

    def window(x, y, w, h, s, tx, ty, r, bw):
        ox = clamp(cx * s - tx, 0, max(0, 720 * s - w))
        oy = clamp(fy * s - ty if ty is not None else 0, 0, max(0, 1280 * s - h))
        return dict(x=x, y=y, w=w, h=h, r=r, s=round(s, 3), ox=round(ox, 1), oy=round(oy, 1), bw=bw)

    # cartão: topo da cabeça em y=460, quadro cobrindo o cartão até o pé do vídeo
    s = clamp(max(.92, 820 / max(1280 - ht, 1)), .92, 1.5)
    card = window(83, 666, 554, 700, s, 277, None, 28, 2.5)
    card["oy"] = round(clamp(206 + ht * s, 0, 666 + 1280 * s - 1280), 1)
    avatar_s = clamp(144 / hw, .25, .9)
    pip_s = clamp(118 / hw, .35, 1)
    geom = {
        "card": card,
        "avatar": window(500, 126, 184, 184, avatar_s, 92, 92, 92, 3.5),
        "pip": window(400, 330, 280, 350, pip_s, 140, 150, 26, 2.5),
        "pipL": window(40, 330, 280, 350, pip_s, 140, 150, 26, 2.5),
        "split": window(0, 0, 720, 640, clamp(290 / hw, .75, 1.6), 360, 330, 0, 5),
    }
    geom["none"] = {**geom["avatar"], "x": 592, "y": 218, "w": 0, "h": 0, "r": 0, "bw": 0}
    print(f"Enquadramento automático: topo da cabeça y={ht:.0f}, centro x={cx:.0f}, largura {hw:.0f}px")
    return geom


def trimmed_map(segs):
    """[(orig_a, orig_b, trimmed_start)]"""
    out, acc = [], 0.0
    for a, b in segs:
        out.append((a, b, acc))
        acc += b - a
    return out, acc


def align(scenes, tmap):
    """Distribui as palavras de cada cena por peso de caracteres nos trechos de fala.
    Os tempos são APROXIMADOS (sem reconhecimento de fala)."""
    words, starts = [], []
    for sc in scenes:
        spans = [(tmap[i][2], tmap[i][2] + tmap[i][1] - tmap[i][0]) for i in sc["segs"]]
        toks = sc["text"].split()
        total_c = sum(len(t) + 1 for t in toks)
        total_t = sum(e - s for s, e in spans)
        starts.append(spans[0][0])
        cum = 0
        for t in toks:
            w = len(t) + 1
            u0, u1 = cum / total_c * total_t, (cum + w) / total_c * total_t
            cum += w
            def at(u):
                for s, e in spans:
                    if u <= e - s:
                        return s + u
                    u -= e - s
                return spans[-1][1]
            words.append((at(u0), at(u1) - 0.02, t))
    return words, starts


def norm(word):
    return re.sub(r"[^\w%$]", "", word.lower())


def build_ass_motion(words, cap, W, H, path, accent, emph, box_spans):
    """Legendas no estilo das referências: 1–2 palavras, ênfase em serifa itálica
    maiúscula ("serif"), cor de destaque ("accent") ou pílula ("pill"), e caixa escura
    nas cenas sem rosto em fundo claro."""
    family = AE.font_family(cap)
    size = round(cap["font_size_ratio"] * H)
    prim = AE.ass_color(cap["primary_color"])
    acc = AE.ass_color(accent)
    r, g, b = AE.hex_to_rgb(accent)
    on_acc = "&H000D0D0D" if (0.2126 * r + 0.7152 * g + 0.0722 * b) / 255 > 0.6 else prim
    x, y = cap.get("x_center", W // 2), round(cap["y_center_ratio"] * H)
    spacing = f"{cap.get('letter_spacing_ratio', 0) * H:.2f}"
    margin = int(W * 0.06)
    head = (f"[Script Info]\nScriptType: v4.00+\nPlayResX: {W}\nPlayResY: {H}\n"
            "WrapStyle: 2\nScaledBorderAndShadow: yes\n\n[V4+ Styles]\n"
            "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,"
            "BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,"
            "BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\n"
            f"Style: Cap,{family},{size},{prim},{prim},&H00000000,&H{cap.get('shadow_alpha','80')}000000,"
            f"0,0,0,0,100,100,{spacing},0,1,0,{cap.get('shadow', 2)},5,{margin},{margin},0,1\n"
            f"Style: Box,{family},{size},{prim},{prim},&H101C1C1E,&H101C1C1E,"
            f"0,0,0,0,100,100,{spacing},0,3,10,0,5,{margin},{margin},0,1\n\n[Events]\n"
            "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n")
    serif = round(size * 1.5)

    def fmt(word):
        t = word.replace("{", "(").replace("}", ")")
        kind = emph.get(norm(word))
        if kind == "serif":
            return f"{{\\fnInstrument Serif\\i1\\fs{serif}\\fsp0}}{t.upper()}{{\\r}}"
        if kind == "accent":
            return f"{{\\c{acc}}}{t}{{\\c{prim}}}"
        if kind == "pill":
            return f"{{\\3c{acc}\\bord9\\shad0\\c{on_acc}}}{t}{{\\r}}"
        return t

    def boxed(t0):
        return any(a <= t0 < b for a, b in box_spans)

    lines = []
    for grp in AE.group_words(words, cap["words_per_caption"], cap.get("max_chars", 99)):
        style = "Box" if boxed(grp[0][0]) else "Cap"
        pos = f"{{\\an5\\pos({x},{y})}}"
        txt = " ".join(fmt(w[2]) for w in grp).replace("{\\r}", "{\\r" + style + "}")
        lines.append(f"Dialogue: 0,{AE.ts(grp[0][0])},{AE.ts(grp[-1][1])},{style},,0,0,0,,{pos}{txt}")
    path.write_text(head + "\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--scenes", type=Path)
    ap.add_argument("--out", default=None)
    ap.add_argument("--max-frames", type=int, default=0, help="teste rápido")
    ap.add_argument("--sample", default="", help="tempos (s) separados por vírgula: salva PNGs e sai")
    ap.add_argument("--no-captions", action="store_true")
    ap.add_argument("--guide", action="store_true", help="mostra a zona de segurança do Reels nas amostras")
    ap.add_argument("--words", type=Path, help="JSON com [início, fim, palavra] no vídeo bruto")
    ap.add_argument("--sfx", type=Path, help="JSON dos efeitos locais, no tempo editado")
    ap.add_argument("--print-segments", action="store_true", help="Lista os índices e tempos dos trechos de fala")
    a = ap.parse_args()

    prof = load_profile()
    cap = {**prof["captions"], "x_center": 360, "blur": 0, "shadow": 2, "outline_width_ratio": 0,
           "words_per_caption": 2, "max_chars": 14, "font_size_ratio": .036, "y_center_ratio": .765}
    src = Path(a.video).expanduser().resolve()
    out = Path(a.out).expanduser().resolve() if a.out else ROOT / "output" / f"{src.stem}_motion.mp4"
    info = probe(src)
    segs = AE.speech_segments(src, info["duration"])
    tmap, total = trimmed_map(segs)
    if a.print_segments:
        print(json.dumps([dict(index=i, original_start=b, original_end=e, edited_start=t)
                          for i, (b, e, t) in enumerate(tmap)], ensure_ascii=False, indent=2))
        return
    if not a.scenes:
        ap.error("--scenes é obrigatório para renderizar")
    from playwright.sync_api import sync_playwright
    out.parent.mkdir(parents=True, exist_ok=True)
    raw = json.loads(a.scenes.read_text())
    cfg = {k: v for k, v in raw.items() if k != "scenes"} if isinstance(raw, dict) else {}
    scenes = raw["scenes"] if isinstance(raw, dict) else raw
    accent = cfg.get("accent", "#FD550A")
    if not scenes or any(not sc.get("segs") or any(not 0 <= i < len(segs) for i in sc["segs"])
                         for sc in scenes):
        ap.error("--scenes deve listar trechos de fala existentes")

    work = Path(tempfile.mkdtemp(prefix="motion_"))
    try:
        trimmed = work / "trimmed.mp4"
        AE.remove_silence(src, trimmed, info["duration"])
        tinfo = probe(trimmed)
        words, starts = align(scenes, tmap)
        starts = [round(float(sc.get("start", st)), 3) for sc, st in zip(scenes, starts)]
        starts[0] = 0.0
        if any(not 0 <= st < total for st in starts) or any(a >= b for a, b in zip(starts, starts[1:])):
            ap.error("Os inícios das cenas devem ser crescentes e estar dentro do vídeo editado")
        if a.words:
            words = []
            for ws, we, word in json.loads(a.words.read_text()):
                spans = [(max(ws, b), min(we, e), b, t) for b, e, t in tmap
                         if min(we, e) > max(ws, b)]
                if spans:
                    left, right, origin, shift = max(spans, key=lambda span: span[1] - span[0])
                    words.append((left - origin + shift, right - origin + shift, word))
        elif not a.sample and not a.no_captions:
            print("Legendas com tempos aproximados. Use --words para sincronizar com o Whisper.")
        for sc, st in zip(scenes, starts):
            sc["start"] = round(st, 3)
        print(f"{len(segs)} trechos de fala; duração final {tinfo['duration']:.1f}s")

        # quadros
        fr = work / "frames"; fr.mkdir()
        r = run(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-i", str(trimmed),
                 "-vf", f"fps={FPS},scale=720:1280", "-q:v", "3", str(fr / "f%05d.jpg")])
        if r.returncode:
            raise SystemExit(r.stderr)
        n = len(list(fr.glob("f*.jpg")))
        if not n:
            raise SystemExit("O vídeo não gerou quadros.")
        # enquadramento: medido no vídeo; "geom" do scenes.json ainda tem a palavra final
        auto = auto_geom(fr, n) if cfg.get("autoGeom", True) else {}
        user = cfg.get("geom", {})
        cfg["geom"] = {k: {**auto.get(k, {}), **user.get(k, {})} for k in set(auto) | set(user)}
        if not auto and cfg.get("autoGeom", True):
            print("Aviso: não encontrei a pessoa nos quadros; usando o enquadramento padrão.")
        if a.max_frames:
            n = min(n, a.max_frames)

        # imagens das cenas (caminhos relativos ao scenes.json): images[].src,
        # card.avatar e card.posts[] do celular
        (work / "img").mkdir()
        copied = {}

        def local(path):
            srcp = (a.scenes.parent / path).expanduser().resolve()
            if not srcp.is_file():
                ap.error(f"Imagem não encontrada: {srcp}")
            if srcp not in copied:
                copied[srcp] = f"img/{len(copied)}{srcp.suffix.lower()}"
                shutil.copy(srcp, work / copied[srcp])
            return copied[srcp]

        for sc in scenes:
            for m in sc.get("images", []):
                m["src"] = local(m["src"])
            if sc.get("bgImage"):
                sc["bgImage"] = local(sc["bgImage"])
            for c in [sc.get("card") or {}]:
                for key in ("src", "file"):
                    if c.get(key):
                        c[key] = local(c[key])
            card = sc.get("card") or {}
            if card.get("avatar"):
                card["avatar"] = local(card["avatar"])
            if card.get("posts"):
                card["posts"] = [local(p) if IMG_EXT.search(p) else p for p in card["posts"]]
        logos = load_logos()
        used = {x.get("name") for sc in scenes for x in sc.get("logos", [])} | \
               {x.get("logo") for sc in scenes for x in sc.get("pills", [])} | \
               {x.get("logo") for sc in scenes for x in ((sc.get("card") or {}).get("rows") or [])} | \
               {x.get("logo") for sc in scenes for x in ((sc.get("card") or {}).get("notifs") or
                                                          (sc.get("card") or {}).get("items") or [])}
        for name in sorted(n for n in used if n and n not in logos):
            print(f"Aviso: logo '{name}' não existe em assets/logos (veja `python3 scripts/images.py logos`).")

        # página
        sample_t = [float(x) for x in a.sample.split(",")] if a.sample else []
        if any(not 0 <= t < n / FPS for t in sample_t):
            ap.error("--sample deve usar tempos dentro do vídeo editado")
        frames = [(int(t * FPS), t) for t in sample_t] if sample_t else [(i, i / FPS) for i in range(n)]
        shutil.copytree(FONT_DIR, work / "fonts")
        html = (ROOT / "motion" / "template.html").read_text()
        dump = lambda v: json.dumps(v, ensure_ascii=False).replace("<", r"\u003c")
        html = html.replace("/*SCENES*/[]", dump(scenes)).replace("/*CONFIG*/{}", dump(cfg)) \
                   .replace("/*TOTAL*/10", f"{tinfo['duration']:.3f}") \
                   .replace("/*LOGOS*/{}", dump(logos))
        (work / "page.html").write_text(html)

        shots = work / "shots"; shots.mkdir()
        with sync_playwright() as p:
            browser = os.environ.get("CHROMIUM_EXECUTABLE")
            br = p.chromium.launch(executable_path=browser) if browser else p.chromium.launch()
            pg = br.new_page(viewport={"width": 720, "height": 1280})
            pg.goto((work / "page.html").as_uri() + ("#guide" if a.guide else ""))
            pg.evaluate("document.fonts.ready")
            pg.evaluate("Promise.all([...document.images].filter(i=>i.src).map(i=>i.decode().catch(()=>0)))")
            pg.wait_for_timeout(400)
            need = pg.evaluate("ts => ts.map(t => cutNeed(t))", [t for _, t in frames])
            idxs = sorted({i for (i, _), nd in zip(frames, need) if nd})
            if idxs:
                print("Recortando a pessoa...")
                make_cutouts(fr, work / "cuts", idxs)
            if a.sample:
                (ROOT / "analysis").mkdir(exist_ok=True)
                for tt in sample_t:
                    i = int(tt * FPS)
                    pg.evaluate(f"setFrame({i},{tt})")
                    dest = ROOT / "analysis" / f"motion_{tt:05.2f}.png"
                    pg.screenshot(path=str(dest)); print("amostra:", dest)
                br.close(); return
            for i in range(n):
                pg.evaluate(f"setFrame({i},{i / FPS})")
                pg.screenshot(path=str(shots / f"f{i + 1:05d}.jpg"), type="jpeg", quality=93)
                if i % 60 == 0:
                    print(f"frame {i}/{n}", flush=True)
            br.close()

        # legendas
        vf = ""
        if cap.get("enabled") and not a.no_captions:
            (work / "cfonts").mkdir()
            for f in FONT_DIR.glob("*"):
                if f.suffix.lower() in (".ttf", ".otf"):
                    shutil.copy(f, work / "cfonts" / f.name)
            ends = [sc["start"] for sc in scenes[1:]] + [tinfo["duration"] + 1]
            box = [(sc["start"], e) for sc, e in zip(scenes, ends)
                   if sc.get("capBox", sc.get("layout") not in ("light", "dark", "full")
                             and sc.get("bg") == "light")]
            emph = {norm(k): v for k, v in cfg.get("emph", {}).items()}
            build_ass_motion(words, cap, 720, 1280, work / "subs.ass", accent, emph, box)
            vf = ["-vf", "ass=subs.ass:fontsdir=cfonts"]

        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", "-framerate", str(FPS),
               "-i", str(shots / "f%05d.jpg"), "-i", str(trimmed), "-map", "0:v", "-map", "1:a"]
        loudness = f"loudnorm=I={prof['audio']['lufs']}:TP={prof['audio']['true_peak']}:LRA=11"
        if a.sfx:
            effects = work / "effects.wav"
            build_track(a.sfx, effects, tinfo["duration"])
            cmd = cmd[:-4] + ["-i", str(effects), "-filter_complex",
                              "[1:a]aformat=channel_layouts=stereo,asplit=2[v][vk];"
                              "[2:a][vk]sidechaincompress=threshold=0.035:ratio=2.5:attack=10:release=260[s];"
                              f"[v][s]amix=inputs=2:duration=first:normalize=0,{loudness}[a]",
                              "-map", "0:v", "-map", "[a]"]
        else:
            cmd += ["-af", loudness]
        if vf:
            cmd += vf
        cmd += ["-c:v", "libx264", "-preset", "medium", "-crf", "17", "-pix_fmt", "yuv420p",
                "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest",
                "-movflags", "+faststart", str(out)]
        r = run(cmd, cwd=work)
        if r.returncode:
            raise SystemExit("ffmpeg falhou:\n" + r.stderr)
        print("OK ->", out)
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    main()
