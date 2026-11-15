"""Exporta intervalos de palavras no relógio do vídeo original."""
import argparse
import json
from pathlib import Path
from apply_edit import transcribe

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--lang", default="pt")
    parser.add_argument("--model", default="small", help="Nome do modelo Whisper ou diretório local")
    args = parser.parse_args()
    words = transcribe(args.video, args.lang, args.model)
    if not words:
        parser.exit(1, "Nenhuma fala detectada.\n")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(words, ensure_ascii=False, indent=2), encoding="utf-8")

if __name__ == "__main__":
    main()
