---
name: skill-recorte-retangulo
description: Edita vídeos falados verticais para Reels, Shorts e TikTok no estilo "cartão com cabeça saliente" — fundo branco pontilhado ou escuro com brilho na cor de destaque, cartão de borda fina, avatar em círculo, PiP, prints de tela, legendas curtas com ênfase em serifa itálica, corte de pausas e efeitos sonoros do Real SFX (uisfx, CC0, local) e do Openverse.
---

# SKILL RECORTE RETANGULO

Use os scripts na pasta desta skill e passe o caminho do vídeo bruto. Saída: MP4 720 × 1280, 30 fps, −14 LUFS.

## Estilo (calibrado em 5 Reels de referência)

- **Kit de marca (padrão)**: **Mandarin Orange `#FD550A`** é a cor de destaque: borda do cartão, palavras `*destacadas*`, pílulas `a`, ênfases nas legendas e número dos contadores. **Forest Green `#015D47`** dá o tom do fundo escuro (base `#03110D` com brilho verde) e das pílulas `v`. **Crest Yellow `#E0F354`** faz os quadradinhos do fundo escuro e as pílulas `l` (texto preto). Não troque as cores por vídeo. Só sobrescreva com `accent`/`green`/`yellow` no `scenes.json` se o usuário pedir.
- **Fundo claro**: branco com pontilhado fino. **Fundo escuro**: verde-floresta quase preto com brilho verde e quadradinhos amarelos piscando. A troca claro↔escuro é um círculo que abre/fecha a partir do centro.
- **Cartão**: estreito (x 83–637), topo em y≈666, borda de 2,5 px na cor de destaque, cantos de 28 px. A cabeça sai bem acima da borda (topo da cabeça por volta de y≈460).
- **Títulos** pequenos e no topo (≈52–64 px, y≈160–180), Inter ExtraBold preto/branco misturado com *Instrument Serif itálica*. Abaixo, uma linha em fonte mono cinza (`sub`).
- **Elementos**: pílulas brancas pequenas com sombra, pílulas de vidro escuro, placas de vidro com rótulo mono em caixa alta e número grande, listas com check, prints/mockups com sombra.
- **Troca de cena a cada 3–6 s.** Alterne: cartão claro, cartão escuro, só gráfico com avatar no círculo, PiP, e rosto em tela cheia com pílulas.
- **Legendas**: brancas, 1–2 palavras, sombra suave, centro em y≈0,765. Palavras-chave em SERIFA ITÁLICA MAIÚSCULA, em laranja ou em pílula. Nas cenas sem rosto em fundo claro a legenda ganha caixa escura.

## Passo a passo

1. Rode `bash scripts/setup.sh` se faltar dependência. Veja os trechos de fala com `.venv/bin/python scripts/motion_edit.py VIDEO --print-segments`.
2. Transcreva com `.venv/bin/python scripts/transcribe.py VIDEO --out words.json` e revise o texto.
3. Escreva o `scenes.json` (formato abaixo). Use o kit de marca (não defina `accent`).
4. Efeitos sonoros (sempre coloque; veja "Efeitos sonoros" abaixo): busque com `python3 scripts/sfx.py search "whoosh"`, monte o `sfx.json` e mixe no render.
5. Prévias: `.venv/bin/python scripts/motion_edit.py VIDEO --scenes scenes.json --guide --sample 2.5,7,11` (salva em `analysis/`). Confira se a cabeça não cobre gráficos e se nada passa de y≈740 acima do cartão. Se a pessoa estiver enquadrada diferente, ajuste `geom` no `scenes.json`.
6. Render: `.venv/bin/python scripts/motion_edit.py VIDEO --scenes scenes.json --words words.json --sfx sfx.json --out output/final.mp4`.
7. Abra quadros do MP4 final e confira nitidez, sincronismo, legendas e áudio.

## Efeitos sonoros

Todo vídeo leva efeitos. Há duas fontes, e as duas são buscadas por `scripts/sfx.py`:

- **Real SFX** (local, `sfx/realsfx/`): 936 sons do pacote uisfx, CC0, sem precisar de crédito. São 78 tipos de som (`swipe`, `select`, `check`, `success`, `notification`, `typing`, `snap`, `lock`, `level-up`, `purchase`…) em 12 estilos. Veja os estilos com `python3 scripts/sfx.py packs`. Para este visual, use `minimal`, `glass` ou `studio`, e `cinematic` para impactos. Use um estilo só por vídeo.
- **Openverse** (online): gravações reais, CC0 por padrão. Com `--allow-cc-by`, preserve o `credit` na entrega.

```
python3 scripts/sfx.py search "whoosh"                          # as duas fontes
python3 scripts/sfx.py search "pop" --source realsfx --pack glass
python3 scripts/sfx.py search "deep whoosh" --source openverse
python3 scripts/sfx.py fetch URL_DO_OPENVERSE pasta-do-video/sfx/whoosh.mp3   # baixe só os escolhidos
```

A busca entende termos em português e inglês (whoosh, transição, pop, clique, check, alerta, digitar, carimbo, dinheiro, conquista…). Os resultados do Real SFX trazem `path` absoluto, que pode ir direto no `sfx.json`. Os do Openverse trazem `url`, que você baixa com `fetch`.

**sfx.json**: lista de `{time, file, duration?, offset?, peak_db?}`. `time` é no vídeo editado, `file` é absoluto ou relativo ao `sfx.json`, `duration` vale 0,5 s por padrão e `peak_db` vale −24 por padrão.

| Momento | Som sugerido | Quando | Nível |
|---|---|---|---|
| Troca de cena | whoosh (Openverse) ou `swipe` (Real SFX) | ~0,3 s antes do `start` da cena | −22 dB |
| Pílula, ícone ou imagem entrando | `select` / `reaction` | no `delay` do elemento (+0,1 s) | −26 dB |
| Item de lista com check | `check` | na entrada de cada linha | −26 dB |
| Contador subindo | `progress-step`, depois `complete` | início e fim da contagem | −26 dB |
| Carimbo (`stamp`) | `cinematic/snap` ou `lock` | em `stampAt` | −22 dB |
| Alerta ou pílula vermelha | `warning` | na entrada | −24 dB |
| Dinheiro ou preço | `purchase` / `coupon` | na entrada | −24 dB |
| Chamada final (seguir) | `success` / `achievement` | na entrada da pílula | −24 dB |

Não empilhe dois sons em menos de 0,15 s, e deixe a voz sempre mais alta que os efeitos.

## Formato do scenes.json

```json
{
  "emph": {"pronto": "serif", "virais": "accent", "um": "pill"},
  "geom": {"card": {"oy": 556}},
  "scenes": [
    {"segs": [0], "layout": "light", "text": "...", "title": "703 vídeos {*pro seu negócio*}", "sub": "do seu Mac · no iPhone"}
  ]
}
```

Uma lista simples de cenas também funciona.

**Cena**: `segs` (índices dos trechos de fala), `text`, `layout`, e opcionalmente `start` (segundos no vídeo editado), `plain` (corte seco sem recorte), `transition: "pixels"` e `capBox` (força ou desliga a caixa da legenda).

**Layouts**:
- `light` / `dark`: cartão com a cabeça saliente.
- `graphic`: sem cartão, rosto no círculo do canto superior direito. Use `bg: "light"` para fundo branco e `avatar: false` para esconder o rosto.
- `pip` / `pipL`: rosto numa janela à direita/esquerda (y 330–680). Use `bg` como em `graphic`.
- `full`: rosto em tela cheia. Pílulas por volta de y 780–860.

**Texto**: `title` (`|` quebra a linha, `{x}` serifa itálica, `*x*` cor de destaque, combináveis como `{*x*}`), `titleY`, `titleSize`, `titleAlign` (`center` | `left`), `titleX`, `sub` (linha mono), `texts` (lista `{text, x, y, size, font: xb|sb|sf|mono, color: "accent"|"green"|"yellow"|hex, align, delay}`).

**Pílulas**: `{text, emoji, x, y, rot, delay, size, style}`. Estilos: `w` (branca), `a` (laranja), `v` (verde), `l` (amarela), `g` (vidro escuro), `k` (preta), `r` (vermelha), `o` (contorno).

**Imagens** (prints, logos, mockups; caminho relativo ao `scenes.json`): `images: [{src, x, y, w, h?, r?, rot?, delay?, anim: pop|slide, border?, shadow?}]`.

**Cartões** (`card.type`):
- `counter`: `{label, prefix, value, unit, caption, y}`. Placa com número animado e unidade em serifa.
- `list`: `{y, gap, step, rows: [{text, emoji?, delay?}]}`. Linhas com check.
- `bars`: `{y, rows: [{label, w, style?: "muted"}]}`.
- `bigicon` `{emoji, x, y}`, `stamp` `{text, stamp, stampAt, y}`, `camicon` `{emoji?, x, y}`, `nameplate` `{initials, name, role, y}`, `follow` `{text, y}`.

`delay` é contado em segundos a partir do início da cena. Sincronize com a palavra falada usando os tempos do `words.json`.

**Zonas seguras** (720 × 1280): conteúdo importante entre y=160 e y=1020, legendas em y≈980. Acima de um cartão, mantenha os gráficos até y≈440 para não colidir com a cabeça.
