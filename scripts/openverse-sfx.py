#!/usr/bin/env python3
"""Busque efeitos CC0 e CC BY pela API pública do Openverse."""
import argparse
import json
import subprocess

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Nome do efeito que você procura")
    parser.add_argument("--limit", type=int, choices=range(1, 21), default=8, metavar="1–20")
    parser.add_argument("--allow-cc-by", action="store_true", help="Inclui efeitos que exigem atribuição")
    args = parser.parse_args()
    allowed = ("cc0", "by") if args.allow_cc_by else ("cc0",)
    command = ["curl", "-fsSG", "--max-time", "15", "https://api.openverse.org/v1/audio/",
               "--data-urlencode", f"q={args.query}", "--data-urlencode", f"license={','.join(allowed)}",
               "--data-urlencode", f"page_size={args.limit}"]
    try:
        data = json.loads(subprocess.check_output(command))
    except (OSError, subprocess.CalledProcessError, ValueError) as error:
        parser.exit(1, f"Não foi possível consultar o Openverse: {error}\n")
    keys = ("title","creator","duration","license","license_url","url","foreign_landing_url","attribution")
    results = [{key: row.get(key) for key in keys} for row in data["results"] if row.get("license") in allowed]
    print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
