# SKILL RECORTE RETANGULO

Skill para editar vídeos falados verticais (Reels, Shorts, TikTok). Faz:

- cartão arredondado com borda fina e a cabeça saindo por cima, com enquadramento automático;
- avatar em círculo, PiP e tela cheia;
- fundo branco pontilhado ou escuro com brilho;
- motion graphics: celular com perfil animado, notificações, gráfico que se desenha, tipografia cinética, partículas, cursor clicando, marca-texto, punch-in;
- fotos reais (Wikimedia Commons e Openverse, CC0), logos oficiais de qualquer marca (Simple Icons ou ícone do app) e material oficial: telas do app na App Store, imagens de newsroom e prints de páginas oficiais;
- legendas curtas com ênfase em serifa itálica;
- corte de pausas;
- efeitos sonoros com gravações reais: kit de 25 sons do Freesound (CC0, incluso) e busca no Openverse; mixagem encaixada pelo pico/ataque, com ducking sob a voz.

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
- Kit de gravações reais: Freesound, CC0 (`sfx/real/LICENSE-AUDIO`, origem de cada som em `sfx/real/manifest.json`).
- Sons sintetizados uisfx (opcionais): CC0 (`sfx/realsfx/LICENSE-AUDIO`).
- Efeitos do Openverse: confira a licença de cada um. CC BY exige crédito.
- Logos: Simple Icons 16.38.1 (CC0, `assets/logos`). As marcas pertencem aos donos; use só para citar a plataforma.
- Material oficial (ícones e telas de apps, imagens e prints de sites oficiais): pertence às marcas; use para informar e comentar, citando a fonte. Não é versionado.
- Fotos do Wikimedia Commons e do Openverse: CC0/domínio público por padrão. Com `--allow-cc-by`, dê o crédito indicado.
