
#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
from pathlib import Path

SOURCE_MAP = {
    "New York Magazine": {
        "ja": "ニューヨーク・マガジン",
        "th": "นิตยสารนิวยอร์ก"
    },
    "NBC News": {
        "ja": "NBCニュース",
        "th": "ข่าว NBC"
    },
    "Financial Post": {
        "ja": "フィナンシャル・ポスト",
        "th": "ไฟแนนเชียลโพสต์"
    },
    "Fox News": {
        "ja": "フォックスニュース",
        "th": "ข่าว Fox"
    },
    "Crypto Briefing": {
        "ja": "クリプト・ブリーフィング",
        "th": "Crypto Briefing"
    },
    "CNA": {
        "ja": "CNA",
        "th": "CNA"
    }
}

def enrich_source_i18n(input_path: Path, output_path: Path):
    data = json.loads(input_path.read_text(encoding="utf-8"))

    for item in data.get("items", []):
        src = item.get("source")
        if not src:
            continue

        if "source_i18n" not in item:
            item["source_i18n"] = {}

        mapping = SOURCE_MAP.get(src)

        if mapping:
            item["source_i18n"]["ja"] = mapping["ja"]
            item["source_i18n"]["th"] = mapping["th"]
            item["source_i18n"]["en"] = src
        else:
            item["source_i18n"]["ja"] = src
            item["source_i18n"]["th"] = src
            item["source_i18n"]["en"] = src

    output_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] wrote: {output_path}")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--in", dest="inp", required=True)
    parser.add_argument("--out", dest="out", required=True)
    args = parser.parse_args()

    enrich_source_i18n(Path(args.inp), Path(args.out))
