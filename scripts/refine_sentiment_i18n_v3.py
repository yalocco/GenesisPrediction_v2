
import argparse
import json
import time
from pathlib import Path

import requests
from requests.exceptions import RequestException, ReadTimeout
from tqdm import tqdm

SYSTEM_PROMPT = """
You are a professional translator and editor.

Task:
- Rewrite the given English text into high-quality Japanese and Thai.
- Make it SHORT (1-2 sentences max)
- Make it NATURAL
- Remove noise, redundancy, and broken grammar
- Keep the meaning, but simplify
- Return strict JSON only

Output JSON:
{
  "ja": "...",
  "th": "..."
}
""".strip()


def build_prompt(text: str) -> str:
    return f"""{SYSTEM_PROMPT}

Text:
{text}
"""


def translate(text: str, model: str, url: str, timeout: int, retries: int, sleep_sec: float) -> dict:
    prompt = build_prompt(text)
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False,
        "format": "json",
    }

    last_error = None
    for attempt in range(retries + 1):
        try:
            r = requests.post(
                f"{url.rstrip('/')}/api/generate",
                json=payload,
                timeout=timeout,
            )
            r.raise_for_status()
            raw = r.json().get("response", "").strip()
            parsed = json.loads(raw)
            ja = str(parsed.get("ja", "")).strip()
            th = str(parsed.get("th", "")).strip()
            if ja and th:
                return {"ja": ja, "th": th, "_status": "translated"}
            return {"ja": text, "th": text, "_status": "fallback_empty"}
        except (ReadTimeout, RequestException, json.JSONDecodeError) as e:
            last_error = e
            if attempt < retries:
                time.sleep(sleep_sec)

    return {
        "ja": text,
        "th": text,
        "_status": f"fallback_error:{type(last_error).__name__}" if last_error else "fallback_error"
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--infile", required=True)
    parser.add_argument("--outfile", required=True)
    parser.add_argument("--model", default="gemma3:4b")
    parser.add_argument("--ollama-url", default="http://localhost:11435")
    parser.add_argument("--timeout", type=int, default=90)
    parser.add_argument("--retries", type=int, default=1)
    parser.add_argument("--sleep-sec", type=float, default=1.5)
    parser.add_argument("--save-every", type=int, default=1)
    args = parser.parse_args()

    infile = Path(args.infile)
    outfile = Path(args.outfile)
    data = json.loads(infile.read_text(encoding="utf-8"))

    items = data.get("items", [])
    updated = 0
    translated = 0
    fallback = 0

    for idx, item in enumerate(tqdm(items), start=1):
        desc = item.get("description", "")
        if not desc:
            continue

        result = translate(
            text=desc,
            model=args.model,
            url=args.ollama_url,
            timeout=args.timeout,
            retries=args.retries,
            sleep_sec=args.sleep_sec,
        )

        item["description_i18n"] = {
            "en": desc,
            "ja": result.get("ja", desc),
            "th": result.get("th", desc),
        }

        item["description_i18n_status"] = result.get("_status", "unknown")

        updated += 1
        if result.get("_status") == "translated":
            translated += 1
        else:
            fallback += 1

        if idx % args.save_every == 0:
            outfile.write_text(
                json.dumps(data, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )

    outfile.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print(f"[OK] refined: {updated} items")
    print(f"[OK] translated: {translated}")
    print(f"[OK] fallback: {fallback}")
    print(f"[OK] wrote: {outfile}")


if __name__ == "__main__":
    main()
