---
name: skill-recorte-retangulo
description: Edita vídeos falados verticais para Reels, Shorts e TikTok no estilo "cartão com cabeça saliente" — fundo branco pontilhado ou escuro com brilho na cor de destaque, cartão de borda fina, avatar em círculo, PiP, motion graphics (celular animado, notificações, gráficos, tipografia cinética, partículas, cursor), fotos reais, logos oficiais, legendas curtas com ênfase em serifa itálica, corte de pausas e efeitos sonoros com gravações reais (kit Freesound CC0 incluso e Openverse).
---

# SKILL RECORTE RETANGULO

Use os scripts na pasta desta skill e passe o caminho do vídeo bruto. Saída: MP4 720 × 1280, 30 fps, −14 LUFS.

## Estilo (calibrado em 5 Reels de referência)

- **Kit de marca (padrão)**: **Mandarin Orange `#FD550A`** é a cor de destaque: borda do cartão, palavras `*destacadas*`, pílulas `a`, ênfases nas legendas e número dos contadores. **Forest Green `#015D47`** dá o tom do fundo escuro (base `#03110D` com brilho verde) e das pílulas `v`. **Crest Yellow `#E0F354`** faz os quadradinhos do fundo escuro e as pílulas `l` (texto preto). Esse é o formato **CLÁSSICO**. Os outros formatos (seção abaixo) trocam fundo e destaque com `"format"`; fora deles, só sobrescreva `accent`/`green`/`yellow` se o usuário pedir.
- **Fundo claro**: branco com pontilhado fino. **Fundo escuro**: verde-floresta quase preto com brilho verde e quadradinhos amarelos piscando. A troca claro↔escuro é um círculo que abre/fecha a partir do centro.
- **Cartão**: estreito (x 83–637), topo em y≈666, borda de 2,5 px na cor de destaque, cantos de 28 px. A cabeça sai bem acima da borda (topo da cabeça por volta de y≈460).
- **Títulos** pequenos e no topo (≈52–64 px, y≈160–180), Inter ExtraBold preto/branco misturado com *Instrument Serif itálica*. Abaixo, uma linha em fonte mono cinza (`sub`).
- **Elementos**: pílulas brancas pequenas com sombra, pílulas de vidro escuro, placas de vidro com rótulo mono em caixa alta e número grande, listas com check, prints/mockups com sombra.
- **Troca de cena a cada 3–6 s.** Alterne: cartão claro, cartão escuro, só gráfico com avatar no círculo, PiP, e rosto em tela cheia com pílulas.
- **Tem que chamar atenção pela arte.** Toda cena precisa de pelo menos um elemento que se mexe junto da fala: logo, foto real, celular, gráfico, notificação, partículas ou tipografia cinética. Uma cena só com título e legenda não basta. Veja "Motion graphics" abaixo.
- **Legendas**: brancas, 1–2 palavras, sombra suave, centro em y≈0,765. Palavras-chave em SERIFA ITÁLICA MAIÚSCULA, em laranja ou em pílula. Nas cenas sem rosto em fundo claro a legenda ganha caixa escura.

## Formatos (o usuário escolhe pelo nome)

O usuário pode pedir um formato pelo nome ou pelo número ao mandar o vídeo ("edita no formato LIMA"). Veja `docs/formatos.jpg`. Se ele não disser nenhum, use **CLÁSSICO**, ou **PRINTS** quando houver imagens de apoio. Não repita o formato do vídeo anterior sem ser pedido. Modificadores combinam com qualquer formato: "sem rosto no círculo", "mais tela cheia", "mais rápido" (cenas de 2–4 s), "paleta verde", "fundo claro".

Cada formato tem **fundo e destaque próprios**: nenhum repete a cor de fundo nem a cor principal. Ative com `"format": "classico" | "prints" | "lima" | "tech" | "pop"` no topo do `scenes.json` (não escreva `accent`/`yellow`/`theme` à mão; qualquer chave escrita sobrescreve o padrão do formato). Chaves de fundo disponíveis: `bgDark` (base do fundo escuro), `glow` + `glowAlpha` (brilho), `squares` (cor dos quadradinhos ou `"none"`), `capAccent` (cor de destaque das legendas).

| # | Formato | Fundo | Destaque | Cenas | Transições | Elementos-assinatura |
|---|---|---|---|---|---|---|
| 1 | **CLÁSSICO** | verde-floresta escuro com brilho verde e quadradinhos amarelos | laranja | quase tudo `dark`, `graphic`, `pip`, `full`; no máximo 1 `light` para respirar | círculo (iris) + 1–2 `swipe` | gráfico de linha, celular, contador, pílulas laranja, kinetic, `follow` |
| 2 | **PRINTS** | **todo branco** pontilhado | verde-floresta (laranja só em alertas, números e legendas) | só `light`, `graphic`/`pip` com `"bg": "light"` e `full` (nenhuma cena escura) | `swipe`, `pixels` (sem iris) | prints do usuário em iPhone (`frame: "phone"`) e cartões, `notifs`, `list`, `bars`, chuva de moedas/ícones (`rain`) |
| 3 | **LIMA** | preto/grafite com grade fina | lima (laranja de apoio) | quase tudo `dark`, um só `light` | `swipe`, `whip`, `glitch`, `zoom` (nada de iris) | logos grandes, `list`, `notifs`, `camicon`, `bigicon`, marca-texto laranja, caixa ATENÇÃO |
| 4 | **TECH** | azul-noite com grade e brilho azul | azul-claro (lima de apoio) | `cutout` com `bgColor` azul-noite (`#060B1E`/`#0E1A3A`) e `bigword` em branco, `accent` ou `yellow` (nunca escuro), `split`, `graphic`, `full` (sem cartão) | `glitch`, `whip`, `zoom` | `window` (navegador), `hud` de detecção, celular com perfil, palavra gigante atrás da pessoa |
| 5 | **POP** | laranja chapado (cutouts alternam com lima chapado via `bgColor`) | lima, preto e branco | `cutout` em fundo chapado + `dark` (laranja); nada de `light` nem `"bg": "light"` (destaque lima some no branco) | `whip`, `swipe`, `zoom` | polaroids, `bigword` com contorno, carimbos, tipografia grande |

TECH e POP fogem do retângulo: use só quando o usuário pedir pelo nome.

## Variedade: cada vídeo com cara própria

A **identidade é o retângulo**: o cartão (`light`/`dark`) com a cabeça saindo por cima. Ele é a base de todo vídeo e aparece em pelo menos 3 cenas, alternado com `graphic` (avatar no círculo), `pip`/`pipL` e `full`. A variedade vem dos **elementos**, das **cores** e das **transições**, nunca de trocar essa identidade.

Para não repetir a fórmula do vídeo anterior, mude:
- os elementos principais: prints em iPhone (`frame: "phone"`), polaroids, celular com perfil, notificações, contador, gráfico, barras, carimbo, janela de navegador, HUD, logos;
- a cor das pílulas (`w`, `a`, `l`, `g`, `k`, `v`) e a posição dos títulos (centro ou esquerda);
- as transições (círculo, `swipe`, `whip`, `zoom`, `glitch`), usando pelo menos 2 tipos;
- o tema (`dots` ou `grid` para tecnologia).

Os prints que o usuário mandar são prova visual: mostre-os grandes, em iPhone ou recortados com `pos` no trecho que importa, sincronizados com a fala.

**Telas cheias**: nas cenas `graphic` (rosto no círculo) e `pip`, preencha a tela até perto da legenda (y≈940) com informação ligada à fala: lista, print, contador, pílulas, notificações. Nada de grandes áreas vazias.

Recursos ousados (`cutout` com `bgColor` e `bigword` atrás da pessoa, `split`) só entram se o usuário pedir. Não são o estilo padrão.

## Passo a passo

Rode todos os comandos **de dentro da pasta desta skill** (`cd` para ela) e use sempre `.venv/bin/python`. Coloque os arquivos de trabalho de cada vídeo (`words.json`, `scenes.json`, `sfx.json`, imagens, sons baixados, `output/`) numa pasta própria do vídeo, **fora da skill**, e passe os caminhos absolutos. Caminhos com espaço vão entre aspas.

0. Verifique a instalação: `.venv/bin/python scripts/check.py`. Se a `.venv` não existir ou algum item falhar, rode `bash scripts/setup.sh` (uma vez só: leva alguns minutos e baixa ~200 MB) e verifique de novo. Se continuar falhando, mostre ao usuário a correção que o `check.py` indica.
1. Veja os trechos de fala com `.venv/bin/python scripts/motion_edit.py VIDEO --print-segments`. O vídeo pode ter qualquer resolução vertical 9:16, porque a saída é sempre 720 × 1280.
2. Transcreva com `.venv/bin/python scripts/transcribe.py VIDEO --out PASTA/words.json` (português por padrão; outra língua: `--lang en`). Revise o texto. A primeira vez baixa o modelo Whisper.
3. Escreva o `scenes.json` (formato abaixo) com `"format"` no topo (o que o usuário pediu, ou `classico`/`prints` por padrão). Não defina `accent` à mão. Planeje o motion de cada cena (veja "Motion graphics") e busque as fotos reais e os logos que a fala pede (veja "Fotos reais e logos").
4. Efeitos sonoros (sempre coloque; veja "Efeitos sonoros" abaixo): use as gravações reais do kit (`python3 scripts/sfx.py kit`), monte o `sfx.json` com `role` em cada som e mixe no render.
5. Prévias: `.venv/bin/python scripts/motion_edit.py VIDEO --scenes scenes.json --guide --sample 2.5,7,11` (salva em `analysis/`). Confira se a cabeça não cobre gráficos e se nada passa de y≈740 acima do cartão. O enquadramento é **automático**: o script mede a cabeça no vídeo e posiciona o rosto no cartão, no avatar e no PiP (ele imprime `Enquadramento automático: ...`). Só se a prévia mostrar a cabeça cortada ou fora do lugar, corrija com `geom` no `scenes.json` (ex.: `{"geom": {"card": {"oy": 520}}}`; `oy` maior sobe a pessoa). Para desligar a medição, use `"autoGeom": false`.
5b. **Storyboard (obrigatório)**: gere `.venv/bin/python scripts/storyboard.py VIDEO --scenes PASTA/scenes.json --out PASTA/storyboard.jpg`, envie a imagem ao usuário e, junto, uma lista numerada "1. tempo — fala — o que aparece". Pergunte o que melhorar ou seguir e **só renderize depois da resposta**. Se o usuário mandar o roteiro, corrija o `words.json` para as legendas seguirem o texto dele.
6. Render: `.venv/bin/python scripts/motion_edit.py VIDEO --scenes PASTA/scenes.json --words PASTA/words.json --sfx PASTA/sfx.json --out PASTA/output/final.mp4`. Um vídeo de 1 minuto leva uns 10 minutos, então rode em segundo plano. Para um teste rápido, use `--max-frames 90`.
7. Abra quadros do MP4 final e confira nitidez, sincronismo, legendas e áudio.

## Motion graphics

Inspirado nos modelos do prompt-motion.com. Regras de movimento:

- Tudo entra com **mola** (leve overshoot que assenta) e fica **vivo**: pílulas, logos e celular flutuam de leve depois de entrar.
- **Sem tempo morto**: cada palavra-chave da fala dispara alguma coisa (sincronize `delay` com o `words.json`; tempo do elemento = início da cena + 0,1 + `delay`).
- Os títulos entram palavra por palavra, saindo de baixo de uma máscara. O `sub` é digitado com cursor.
- Cada troca de cena dá um pequeno zoom de câmera (desligue com `"kick": false`).
- Movimento com motivo: um elemento entra porque a pessoa falou dele, nunca por enfeite.

| Recurso | Como usar | Bom para |
|---|---|---|
| Marca-texto | `[palavra]` no título; `marks: [0.4, 1.1]` sincroniza cada marca com a fala | perguntas, listas faladas |
| Logos oficiais | `logos: [{name, x, y, size, rot, delay, label?, plain?, tile:"white"?}]`, `logo` em pílulas, linhas de lista e notificações | citar plataformas e apps |
| Fotos reais | `images` com `frame:"polaroid"` + `caption`, `mask:"circle"`, `anim:"deal"` (voa de baixo girando); Ken Burns automático (`kb:false` desliga) | exemplos concretos |
| Celular | `card.type:"phone"` (abaixo) | redes sociais, seguidores, vendas |
| Notificações | `card.type:"notifs"` com `items:[{logo|emoji, title?, text, at}]` | parcerias, vendas, mensagens |
| Gráfico | `card.type:"chart"` com `values`, `label`, `title?`, `callout`, `delay`, `dur` | crescimento, resultados |
| Tipografia cinética | `card.type:"kinetic"` com `lines:[{text, delay, style:"box"|"outline", size, rot}]`: entra com impacto, deslocamento de cor e tremor | alertas, viradas, frases de efeito |
| Partículas | `bursts:[{x, y, at, n, emoji?, colors?, mode?: "rise"|"rain", dur?}]`: confete/emoji estourando, corações subindo (`rise`) ou chuva caindo do topo (`rain`, com `x0`/`x1`, `life`) | dinheiro, curtidas, conquista, CTA |
| Cursor | `cursor:[{x, y, at, click}]`, ou automático com `clickAt` no `phone` e no `follow` | botões, "me segue" |
| Punch-in | em `full`: `punch:[{at, s:1.15}]` (`punchY` ajusta o centro) | ênfase no rosto |
| Transição | `transition`: `swipe` (faixa diagonal), `whip` (chicote com desfoque), `zoom` (zoom com desfoque), `glitch` (faixas digitais e tremor), `pixels` | mudança de assunto |

**Celular** (`card.type:"phone"`): `{x, y, w (largura, padrão 320), rot, delay, handle, name, bio, from, to, countAt, countDur, posts: [imagens ou emojis, até 9], gridAt, clickAt, button?, buttonDone?, likeAt?, likeTile?, notifs:[{logo, text, at}], avatar?}`. O avatar mostra o rosto ao vivo do vídeo, a contagem de seguidores sobe e o botão "Seguir" é clicado por um cursor em `clickAt`.

## Fotos reais e logos

```
python3 scripts/images.py logos                                     # 30 logos oficiais (Simple Icons, CC0)
python3 scripts/images.py search "ring light" --limit 8             # Wikimedia Commons + Openverse, CC0/domínio público
python3 scripts/images.py fetch URL pasta-do-video/img/ringlight.jpg   # baixa e converte para JPG
```

- Busque fotos em inglês e baixe só as escolhidas para `img/` da pasta do vídeo. No `scenes.json`, use o caminho relativo (`"img/ringlight.jpg"`).
- Abra as fotos antes de usar: o acervo tem de tudo, então confira se a imagem mostra mesmo o que a fala diz.
- Por padrão só vêm fotos CC0 ou de domínio público. Com `--allow-cc-by`, ponha o `credit` de cada foto na legenda do post.
- Os logos servem para citar a plataforma. Não os use para sugerir parceria ou patrocínio que não existe.

## Efeitos sonoros

Todo vídeo leva efeitos, e **sempre gravações reais** (o som de verdade de papel, moeda, clique, ar). Sons sintetizados soam amadores.

- **Kit real** (`sfx/real/`, local): 25 gravações do Freesound em CC0, escolhidas e tratadas (sem silêncio no começo, pico normalizado, sem ruído de fundo). Liste com `python3 scripts/sfx.py kit`. Use primeiro.
- **Openverse** (online): milhões de gravações reais do Freesound. Busque em inglês quando o kit não tiver o som (`--source openverse`); CC0 por padrão. Abra o resultado antes de usar e evite títulos com cartoon, synth, 8-bit ou game.
- **uisfx** (`sfx/realsfx/`): sons de interface **sintetizados**. Não use, a menos que o usuário peça esse estilo.

```
python3 scripts/sfx.py kit                                      # o kit de gravações reais
python3 scripts/sfx.py search "carimbo"                         # kit + Openverse
python3 scripts/sfx.py search "glass break" --source openverse
python3 scripts/sfx.py fetch URL_DO_OPENVERSE pasta-do-video/sfx/vidro.mp3
```

**sfx.json**: lista de `{time, file, role, gain_db?, align?, duration?, offset?, pitch?, pan?}`. `file` é absoluto ou relativo ao `sfx.json`. O `role` define o nível, o encaixe e a duração; ajuste com `gain_db` (±dB), não com o pico absoluto.

Como o mix trabalha (no estilo do Real SFX):
- **Encaixe pelo som, não pelo arquivo**: whoosh e swish põem o **pico** em `time` (o ar passa exatamente no corte: use o `start` da cena); clique, pop, carimbo e impacto põem o **ataque** em `time`; riser **termina** em `time`.
- **Variação automática**: o mesmo arquivo repetido ganha uma afinação um pouco diferente a cada vez, para não soar robótico.
- **Ducking**: os efeitos baixam alguns dB enquanto a pessoa fala, e a voz sempre fica na frente.

| Momento | Arquivo do kit | role | Quando |
|---|---|---|---|
| Troca de cena | `whoosh/deep` (grande), `whoosh/air`, `whoosh/low`, `whoosh/wide`: alterne | whoosh | no `start` da cena |
| Elemento entrando de lado, celular subindo | `swish/bamboo`, `swish/swing` | swish | na entrada |
| Pílula, logo, ícone | `pop/bubble`, `pop/mouth`: alterne | pop | no `delay` (+0,1 s) |
| Cursor clicando | `click/mouse` | click | no `clickAt` |
| Texto digitado (`sub`) | `typing/keyboard` com `duration` ≈ tempo da digitação | typing | início do `sub` |
| Foto/polaroid | `paper/slide` + `shutter/camera` | paper / shutter | na entrada |
| Dinheiro, Pix, preço | `coins/table`, `coins/drop` | coins | na palavra |
| Notificação | `notify/ding` | notify | no `at` |
| Conquista, chamada final | `chime/bell`, `chime/ding` | chime | na entrada |
| Carimbo | `stamp/stamp` + `hit/thump` (camada, `gain_db:-6`) | stamp / hit | em `stampAt` |
| Tipografia cinética, alerta | `hit/impact` | hit | na entrada da linha |
| Punch-in no rosto | `hit/thump` com `gain_db:-9` | hit | no `at` do punch |
| Gráfico subindo | `riser/smooth` ou `riser/build` | riser | `time` = fim do traço |
| Marca-texto | `marker/marker` | marker | em cada `marks` |

Ritmo: de 3 a 9 sons por 10 s (sons em camada a menos de 80 ms contam como um). Golpes fortes (impacto, carimbo) em no máximo um terço das cenas. Nem todo elemento precisa de som: prefira os que a fala destaca.

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

**Cena**: `segs` (índices dos trechos de fala), `text`, `layout`, e opcionalmente `start` (segundos no vídeo editado; permite dividir um trecho longo em duas cenas com o mesmo `segs`), `plain` (corte seco sem recorte), `transition` (`pixels`, `swipe`, `whip`, `zoom`, `glitch`), `kick: false` e `capBox` (força ou desliga a caixa da legenda).

**Layouts**:
- `light` / `dark`: cartão com a cabeça saliente.
- `graphic`: sem cartão, rosto num círculo de 184 px no canto superior direito (x 500–684, y 126–310). Comece os gráficos abaixo de y≈320 à direita e mantenha os títulos à esquerda. Use `bg: "light"` para fundo branco e `avatar: false` para esconder o rosto.
- `pip` / `pipL`: rosto numa janela à direita/esquerda (y 330–680). Use `bg` como em `graphic`.
- `full`: rosto em tela cheia. Pílulas por volta de y 780–860.
- `cutout`: a pessoa recortada (corpo inteiro) sobre um fundo próprio: `bgColor` (`accent`, `green`, `yellow` ou hex) ou `bgImage` (foto com zoom lento e sombreado; `bgShade` muda o sombreado). Ajuste com `personScale`, `personX` e `personY`. Combine com `bigword` para o texto aparecer **atrás** da pessoa. A cabeça fica entre y≈250 e 560, então a palavra gigante vai em y≈110–200.
- `split`: rosto na metade de cima (y 0–640, linha laranja embaixo) e conteúdo na metade de baixo (y 660–940). Use `bgColor` para a cor da metade de baixo.

**Fundo por cena**: qualquer layout aceita `bgColor` ou `bgImage`. A cor do texto (claro/escuro) se ajusta sozinha.

**Palavra gigante** (`bigword`): `{text ("|" quebra a linha), y, size (≈150–220), color, style?: "outline", delay, rot?}`. Fica atrás da pessoa e entra com impacto.

**Tema** (no topo do `scenes.json`): `"theme": "dots"` (padrão), `"grid"` (linhas técnicas) ou `"plain"`.

**Texto**: `title` (`|` quebra a linha, `{x}` serifa itálica, `*x*` cor de destaque, `[x]` marca-texto amarelo, combináveis como `{*x*}` ou `[{x}]`), `marks`, `titleDelay`, `titleY`, `titleSize`, `titleAlign` (`center` | `left`), `titleX`, `sub` (linha mono), `texts` (lista `{text, x, y, size, font: xb|sb|sf|mono, color: "accent"|"green"|"yellow"|hex, align, delay}`).

**Pílulas**: `{text, emoji | logo, x, y, rot, delay, size, style, float?}`. Estilos: `w` (branca), `a` (laranja), `v` (verde), `l` (amarela), `g` (vidro escuro), `k` (preta), `r` (vermelha), `o` (contorno).

**Imagens** (fotos, prints, mockups; caminho relativo ao `scenes.json`): `images: [{src, x, y, w, h?, r?, rot?, delay?, anim: pop|slide|deal, frame?: "polaroid"|"phone", caption?, mask?: "circle", pos? (ex.: "top", recorte da imagem), kb?, border?, shadow?}]`. Use `frame: "phone"` para mostrar prints de celular dentro de um iPhone.

**Cartões** (`card.type`):
- `counter`: `{label, prefix, value, unit, caption, y}`. Placa com número animado e unidade em serifa.
- `list`: `{y, gap, step, rows: [{text, emoji?, delay?}]}`. Linhas com check.
- `bars`: `{y, rows: [{label, w, style?: "muted"}]}`.
- `bigicon` `{emoji, x, y}`, `stamp` `{text, stamp, stampAt, stampX?, y}`, `camicon` `{emoji?, x, y}`, `nameplate` `{initials, name, role, y}`, `follow` `{text, y, delay?, clickAt?}`.
- `phone`, `notifs`, `chart`, `kinetic`: veja "Motion graphics".
- `window`: janela de navegador/app `{x, y, w, h, url, title?, hint?, icon?, src? (imagem dentro), file? + fileAt (imagem que cai na área de upload), scanAt? + scanDur (linha escaneando), result?: {text, emoji, style, at, size, anim}}`.
- `hud`: cantoneiras de detecção sobre o rosto ou um objeto `{x, y, w, h, delay, label ("ANALISANDO"), result ("IA {v}%"), value, valueAt, color?, scan?}`. Em `full`, o rosto fica por volta de x 200–520, y 210–610.

`delay` é contado em segundos a partir do início da cena. Sincronize com a palavra falada usando os tempos do `words.json`.

**Zonas seguras** (720 × 1280): conteúdo importante entre y=160 e y=1020, legendas em y≈980. Acima de um cartão, mantenha os gráficos até y≈440 para não colidir com a cabeça.
