# SKILL RECORTE RETANGULO

Skill para editar vídeos falados verticais (Reels, Shorts, TikTok). Faz:

- cartão arredondado com borda fina e a cabeça saindo por cima, com enquadramento automático;
- avatar em círculo, PiP e tela cheia;
- fundo branco pontilhado ou escuro com brilho;
- motion graphics e prints de tela;
- legendas curtas com ênfase em serifa itálica;
- corte de pausas;
- efeitos sonoros do Real SFX (uisfx, CC0, inclusos) e do Openverse.

Cores do kit de marca: Mandarin Orange `#FD550A`, Forest Green `#015D47` e Crest Yellow `#E0F354`.

## Requisitos

- macOS ou Linux (no Windows, use o WSL)
- Python 3.10 ou mais novo
- FFmpeg com libass, cURL e unzip
  - macOS: `brew install python ffmpeg`
  - Ubuntu/Debian: `sudo apt install python3 python3-venv ffmpeg curl unzip`
- Cerca de 1,5 GB livres: bibliotecas, Chromium, modelo de recorte e modelo Whisper

## Instalação no Claude Code

Para todos os seus projetos:

```bash
git clone https://github.com/euleomendes/skillrecorteretangulo ~/.claude/skills/skill-recorte-retangulo
```

```bash
cd ~/.claude/skills/skill-recorte-retangulo && bash scripts/setup.sh
```

Para um projeto só, clone em `.claude/skills/skill-recorte-retangulo` dentro do projeto e rode o setup lá.

O setup instala as bibliotecas com versões fixas, o Chromium, as fontes, a fonte de emoji (fora do macOS) e o modelo de recorte U2Net. No fim, ele roda a verificação. Para conferir de novo a qualquer momento:

```bash
.venv/bin/python scripts/check.py
```

## Uso

No Claude Code, peça:

> Edite meu vídeo /caminho/video.mp4 com a skill-recorte-retangulo.

Ou chame `/skill-recorte-retangulo /caminho/video.mp4`.

O Claude transcreve o vídeo, monta as cenas e os efeitos, mostra prévias e renderiza o MP4. Veja [SKILL.md](SKILL.md) para os comandos, o formato das cenas e a tabela de efeitos.

## Atualizar

```bash
cd ~/.claude/skills/skill-recorte-retangulo && git pull && bash scripts/setup.sh
```

## Licenças

- Fontes: Inter e Instrument Serif (OFL); Noto Color Emoji (OFL).
- Sons do Real SFX/uisfx: CC0 (`sfx/realsfx/LICENSE-AUDIO`).
- Efeitos do Openverse: confira a licença de cada um. CC BY exige crédito.
