# SKILL RECORTE RETANGULO

Skill para editar vídeos falados verticais. Aplica cartão arredondado com borda fina na cor de destaque e cabeça saliente, avatar em círculo, PiP, motion graphics, legendas nítidas, corte de pausas e efeitos sonoros do Real SFX (uisfx, CC0, local) e do Openverse.

## Instalação

Clone o repositório em `~/.agents/skills/skill-recorte-retangulo` ou extraia o ZIP nessa pasta. Em macOS ou Linux, instale Python 3, FFmpeg com libass, cURL e unzip. Rode `bash scripts/setup.sh` na pasta da skill. O setup instala as bibliotecas, o Chromium, as fontes Inter e Instrument Serif e o modelo U2Net. A primeira transcrição baixa o modelo Whisper selecionado.

## Uso no Codex

> Use $skill-recorte-retangulo para editar meu vídeo vertical em /caminho/video.mp4. Adicione gráficos e efeitos sonoros sincronizados com a fala.

Veja [SKILL.md](SKILL.md) para os comandos, o formato das cenas e a mixagem.
