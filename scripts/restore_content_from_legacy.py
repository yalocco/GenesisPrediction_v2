import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATIC = ROOT / "app" / "static"
TMP = ROOT / "tmp_legacy"

PAGES = [
    ("index.html", TMP / "index_legacy.html"),
    ("overlay.html", TMP / "overlay_legacy.html"),
    ("sentiment.html", TMP / "sentiment_legacy.html"),
    ("digest.html", TMP / "digest_legacy.html"),
]

def extract_main(html: str) -> str | None:
    """
    Extract <main>...</main> from legacy HTML.
    If not found, fallback to <body>...</body> (excluding obvious legacy headers/nav).
    """
    m = re.search(r"<main\b[^>]*>.*?</main>", html, flags=re.IGNORECASE | re.DOTALL)
    if m:
        return m.group(0)

    # fallback: body inner
    b = re.search(r"<body\b[^>]*>(.*)</body>", html, flags=re.IGNORECASE | re.DOTALL)
    if not b:
        return None

    body_inner = b.group(1)

    # drop common legacy header/nav blocks if present (best-effort)
    body_inner = re.sub(r"<header\b[^>]*>.*?</header>", "", body_inner, flags=re.IGNORECASE | re.DOTALL)
    body_inner = re.sub(r"<nav\b[^>]*>.*?</nav>", "", body_inner, flags=re.IGNORECASE | re.DOTALL)

    # wrap into main
    return "<main>\n" + body_inner.strip() + "\n</main>"

def replace_main(current: str, new_main: str) -> str:
    """
    Replace current <main>...</main>.
    If current has no <main>, insert it right after <body ...>.
    """
    if re.search(r"<main\b", current, flags=re.IGNORECASE):
        return re.sub(
            r"<main\b[^>]*>.*?</main>",
            new_main,
            current,
            flags=re.IGNORECASE | re.DOTALL,
            count=1,
        )

    # Insert after <body ...>
    return re.sub(
        r"(<body\b[^>]*>)",
        r"\1\n" + new_main + "\n",
        current,
        flags=re.IGNORECASE | re.DOTALL,
        count=1,
    )

def sanity_keep_shared_nav(current: str) -> bool:
    """
    Ensure current file looks like the unified skeleton (shared header injection present).
    We just do a light check to avoid overwriting with wrong base.
    """
    return ("_shared_nav.js" in current) or ("shared_nav" in current.lower()) or ("header injected" in current.lower())

def main():
    errors = []

    for fname, legacy_path in PAGES:
        cur_path = STATIC / fname
        if not cur_path.exists():
            errors.append(f"[MISS] current not found: {cur_path}")
            continue
        if not legacy_path.exists():
            errors.append(f"[MISS] legacy not found: {legacy_path}")
            continue

        current = cur_path.read_text(encoding="utf-8", errors="ignore")
        legacy = legacy_path.read_text(encoding="utf-8", errors="ignore")

        if not sanity_keep_shared_nav(current):
            errors.append(f"[SKIP] {fname}: current does not look like unified skeleton (shared header not detected).")
            continue

        legacy_main = extract_main(legacy)
        if not legacy_main:
            errors.append(f"[FAIL] {fname}: cannot extract main/body from legacy.")
            continue

        updated = replace_main(current, legacy_main)

        # Keep a backup
        bak_path = cur_path.with_suffix(cur_path.suffix + ".bak_before_restore")
        if not bak_path.exists():
            bak_path.write_text(current, encoding="utf-8")

        cur_path.write_text(updated, encoding="utf-8")
        print(f"[OK] restored main content: {fname}")

    if errors:
        print("\n--- issues ---")
        for e in errors:
            print(e)
        print("\nIf you see [SKIP], stop and tell me that line (screenshot OK).")
        sys.exit(2)

if __name__ == "__main__":
    main()