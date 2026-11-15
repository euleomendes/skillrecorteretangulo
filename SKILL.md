---
name: skill-recorte-retangulo
description: Edita vídeos falados verticais para Reels, Shorts e TikTok com recorte da cabeça acima de um cartão de borda amarela, motion graphics, emojis, legendas sincronizadas, corte de pausas e efeitos do Openverse.
---

# SKILL RECORTE RETANGULO

Use os scripts na pasta desta skill e passe o caminho do vídeo bruto. O padrão é MP4 de 720 × 1280 a 30 fps e áudio em torno de −14 LUFS. Alterne cartões claros e escuros. Reserve tela cheia com voz e legenda para a apresentação e a chamada final quando couber.

1. Rode `bash scripts/setup.sh` se o ambiente ainda precisar de dependências. Para analisar as pausas, use `.venv/bin/python scripts/motion_edit.py VIDEO --print-segments`.
2. Transcreva com `.venv/bin/python scripts/transcribe.py VIDEO --out words.json`. Revise a transcrição antes de escrever os gráficos. Use os tempos do vídeo bruto no JSON de palavras.
3. Crie `scenes.json` a partir de `motion/scenes_exemplo.json`. Adapte títulos, gráficos e emojis à fala. Cada cena tem `text`, `segs` (índices de trechos de fala) e `layout` (`light`, `dark` ou `full`). Use `start` em segundos na linha do tempo editada para iniciar uma cena no meio de um trecho. Para tela cheia com legenda e sem arte, use `layout: "full"` e `plain: true`.
4. Para efeitos, consulte `python3 scripts/openverse-sfx.py "short whoosh"`. Por padrão a busca usa CC0. Se usar `--allow-cc-by`, preserve o crédito do criador e o link da licença na entrega. Baixe apenas os sons escolhidos. Monte `sfx.json` como uma lista de entradas com `time` (segundos no vídeo editado), `file` (caminho relativo a `sfx.json`), `duration` (opcional, 0,5 s por padrão), `offset` (opcional, ponto de entrada no arquivo) e `peak_db` (opcional, −24 dBFS por padrão). Posicione sob a voz e sincronize com as entradas de elementos ou as transições.
5. Confira as prévias com `.venv/bin/python scripts/motion_edit.py VIDEO --scenes scenes.json --guide --sample 1.5,6`. Escolha tempos representativos dentro do vídeo editado. Mantenha textos importantes entre x=47 e x=697 e y=167 a y=740. Entre y=740 e y=1023, limite a borda direita a x=591. Em cartão, a borda superior fica em y=660. Confira se a cabeça se projeta sem cobrir os gráficos. Ajuste `geom.card` em `motion/template.html` quando a gravação pedir.
6. Renderize com `.venv/bin/python scripts/motion_edit.py VIDEO --scenes scenes.json --words words.json --sfx sfx.json --out output/final.mp4`. Sem uma faixa de efeitos, omita `--sfx`. Sem JSON de palavras, o script aproxima o tempo das legendas a partir das cenas.
7. Abra quadros do MP4 final e confira nitidez, sincronismo, áudio e zona de segurança. A fonte Inter ExtraBold aproxima a tipografia das referências. Preserve a fala e corte apenas as pausas.

Os títulos aceitam `|` para quebra de linha e `{itálico}` para trechos em serifa. As pílulas aceitam `text`, `emoji`, `x`, `y`, `rot`, `delay` e `style` (`y`, `k`, `w` ou `r`). Os cartões disponíveis estão em `motion/template.html`.
