
import argparse
import requests
import json
import re
from pathlib import Path

def clean_text(text):
    if not text:
        return text
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def call_ollama(prompt, model, url):
    r = requests.post(
        f"{url}/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "stream": False
        },
        timeout=300
    )
    r.raise_for_status()
    return r.json()["response"]

def refine_item(desc_en, model, url):
    prompt = f'''
Translate the following English text into Japanese and Thai.

Rules:
- Preserve proper nouns exactly (names, places, organizations)
- No English words in output
- Natural sentences
- No truncation

Text:
{desc_en}

Return JSON:
{{ "ja": "...", "th": "..." }}
'''
    res = call_ollama(prompt, model, url)

    try:
        data = json.loads(res)
    except:
        return None

    return {
        "ja": clean_text(data.get("ja", "")),
        "th": clean_text(data.get("th", ""))
    }

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--infile", required=True)
    parser.add_argument("--outfile", required=True)
    parser.add_argument("--model", required=True)
    parser.add_argument("--ollama-url", required=True)

    args = parser.parse_args()

    path = Path(args.infile)
    data = json.loads(path.read_text(encoding="utf-8"))

    count = 0

    for item in data.get("items", []):
        desc = item.get("description", "")
        if not desc:
            continue

        refined = refine_item(desc, args.model, args.ollama_url)
        if refined:
            if "description_i18n" not in item:
                item["description_i18n"] = {}

            item["description_i18n"]["ja"] = refined["ja"]
            item["description_i18n"]["th"] = refined["th"]
            count += 1

    Path(args.outfile).write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"[OK] refined description_i18n for {count} items")

if __name__ == "__main__":
    main()
