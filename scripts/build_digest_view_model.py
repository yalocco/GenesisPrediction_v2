# scripts/build_digest_view_model.py
from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

VERSION = "v1"
DEFAULT_SECTION_ID = "world_politics"

DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")


# ---------------------------
# Utilities
# ---------------------------

def iso_now_local() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def read_text_safe(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return p.read_text(encoding="cp932", errors="replace")


def read_json_safe(p: Path) -> Any:
    return json.loads(read_text_safe(p))


def find_repo_root(start: Path) -> Path:
    cur = start.resolve()
    for _ in range(12):
        if (cur / ".git").exists():
            return cur
        if (cur / "scripts").exists() and (cur / "app").exists():
            return cur
        if (cur / "docker-compose.yml").exists() or (cur / "compose.yml").exists():
            return cur
        cur = cur.parent
    return start.resolve().parent


def extract_date_from_filename(name: str) -> Optional[str]:
    m = DATE_RE.search(name)
    return m.group(1) if m else None


def validate_date(date_str: str) -> str:
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError as e:
        raise SystemExit(f"[ERROR] invalid --date '{date_str}': {e}")
    return date_str


def short(s: str, n: int) -> str:
    s = re.sub(r"\s+", " ", (s or "")).strip()
    return s if len(s) <= n else s[: n - 1].rstrip() + "…"


def host_of(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    try:
        h = urlparse(url).netloc
        return h or None
    except Exception:
        return None


def norm_space(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "")).strip()


# ---------------------------
# ViewModel models
# ---------------------------

@dataclass
class Card:
    title: str
    summary: str
    source: Optional[str] = None
    url: Optional[str] = None
    image: Optional[str] = None
    tags: Optional[List[str]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "summary": self.summary,
            "source": self.source,
            "url": self.url,
            "image": self.image,
            "tags": self.tags or [],
        }


@dataclass
class Section:
    id: str
    title: str
    status: str  # ok | na | error
    cards: List[Card]
    notes: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "status": self.status,
            "cards": [c.to_dict() for c in self.cards],
            "notes": self.notes,
        }


# ---------------------------
# Extractors (JSON fallback)
# ---------------------------

def build_cards_from_json(obj: Any, max_cards: int) -> List[Card]:
    cards: List[Card] = []

    if isinstance(obj, dict):
        if isinstance(obj.get("cards"), list):
            for it in obj["cards"][:max_cards]:
                if not isinstance(it, dict):
                    continue
                url = it.get("url") if isinstance(it.get("url"), str) else None
                src = it.get("source") or host_of(url)
                cards.append(
                    Card(
                        title=str(it.get("title") or "Untitled"),
                        summary=str(it.get("summary") or ""),
                        source=src if isinstance(src, str) else None,
                        url=url,
                        image=it.get("image") if isinstance(it.get("image"), str) else None,
                        tags=it.get("tags") if isinstance(it.get("tags"), list) else [],
                    )
                )
            return cards

        for key in ("items", "news", "articles", "entries"):
            if isinstance(obj.get(key), list):
                for it in obj[key][:max_cards]:
                    if not isinstance(it, dict):
                        continue
                    title = it.get("title") or it.get("headline") or it.get("name") or "Untitled"
                    summary = it.get("summary") or it.get("description") or it.get("snippet") or ""
                    url = it.get("url") if isinstance(it.get("url"), str) else None
                    src = it.get("source") or host_of(url)
                    cards.append(
                        Card(
                            title=str(title),
                            summary=str(summary),
                            source=src if isinstance(src, str) else None,
                            url=url,
                            image=(it.get("image") or it.get("image_path")) if isinstance((it.get("image") or it.get("image_path")), str) else None,
                            tags=it.get("tags") if isinstance(it.get("tags"), list) else [],
                        )
                    )
                return cards

        headline = obj.get("headline") or obj.get("title")
        bullets = obj.get("bullets") or obj.get("highlights") or obj.get("summary_bullets")
        if headline and isinstance(bullets, list):
            summary = "\n".join(f"- {str(b)}" for b in bullets[:8])
            cards.append(Card(title=str(headline), summary=summary))
            return cards

    return cards


# ---------------------------
# Extractors (HTML digest → news cards)
# ---------------------------

@dataclass
class _CardCtx:
    depth: int
    first_href: Optional[str] = None
    first_img: Optional[str] = None
    title_text: str = ""
    summary_text: str = ""
    tags: List[str] = None
    domain_text: str = ""
    _in_a: bool = False
    _in_p: bool = False
    _in_h: bool = False
    _span_class: str = ""

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class DigestCardHTMLParser(HTMLParser):
    """
    Heuristic parser:
    - Detect "card-like" container: <article> or <div class="...card...">
    - Inside it, collect:
      - first <a href=...> text as title candidate
      - first heading text (h1/h2/h3) as stronger title candidate
      - first <p> text as summary
      - first <img src=...> as image
      - <span class="..."> used for tags / domain (chip/pill/tag/badge)
    """
    def __init__(self, max_cards: int):
        super().__init__(convert_charrefs=True)
        self.max_cards = max_cards
        self.stack_depth = 0
        self.cards: List[Card] = []
        self.ctx: Optional[_CardCtx] = None

    def handle_starttag(self, tag: str, attrs: List[Tuple[str, Optional[str]]]):
        self.stack_depth += 1
        a = dict(attrs)
        cls = (a.get("class") or "").lower()

        def start_new_card():
            self.ctx = _CardCtx(depth=self.stack_depth)

        # Enter card container
        if self.ctx is None:
            if tag.lower() == "article":
                start_new_card()
            elif tag.lower() == "div" and "card" in cls:
                start_new_card()

        # If inside a card, capture fields
        if self.ctx is not None:
            if tag.lower() == "a":
                href = a.get("href")
                if self.ctx.first_href is None and isinstance(href, str) and href.strip():
                    self.ctx.first_href = href.strip()
                self.ctx._in_a = True

            elif tag.lower() in ("h1", "h2", "h3", "h4"):
                self.ctx._in_h = True

            elif tag.lower() == "p":
                # capture first paragraph as summary
                self.ctx._in_p = True

            elif tag.lower() == "img":
                src = a.get("src")
                if self.ctx.first_img is None and isinstance(src, str) and src.strip():
                    self.ctx.first_img = src.strip()

            elif tag.lower() == "span":
                self.ctx._span_class = (a.get("class") or "").lower()

    def handle_endtag(self, tag: str):
        # close flags
        if self.ctx is not None:
            if tag.lower() == "a":
                self.ctx._in_a = False
            elif tag.lower() in ("h1", "h2", "h3", "h4"):
                self.ctx._in_h = False
            elif tag.lower() == "p":
                self.ctx._in_p = False
            elif tag.lower() == "span":
                self.ctx._span_class = ""

            # Exit container: when depth returns above ctx.depth
            if self.stack_depth == self.ctx.depth and tag.lower() in ("div", "article"):
                self._finalize_ctx()
                self.ctx = None

        self.stack_depth = max(0, self.stack_depth - 1)

    def handle_data(self, data: str):
        if self.ctx is None:
            return
        t = norm_space(data)
        if not t:
            return

        # tags / domain chips
        sc = self.ctx._span_class
        if sc:
            # domain often in a span with "domain" class
            if "domain" in sc and len(t) <= 80:
                if not self.ctx.domain_text:
                    self.ctx.domain_text = t
                return
            # tags/pills
            if any(k in sc for k in ("tag", "pill", "chip", "badge")) and 1 <= len(t) <= 30:
                if t not in self.ctx.tags:
                    self.ctx.tags.append(t)
                return

        # title preference: heading > anchor text
        if self.ctx._in_h and len(t) >= 6:
            if not self.ctx.title_text:
                self.ctx.title_text = t
            return

        if self.ctx._in_a and len(t) >= 8:
            # only if heading not already set
            if not self.ctx.title_text:
                self.ctx.title_text = t
            return

        # summary: first paragraph
        if self.ctx._in_p and not self.ctx.summary_text:
            if len(t) >= 20:
                self.ctx.summary_text = t

    def _finalize_ctx(self):
        if len(self.cards) >= self.max_cards:
            return
        c = self.ctx
        if c is None:
            return

        url = c.first_href
        src = c.domain_text or host_of(url)
        title = short(c.title_text or "Untitled", 180)
        summary = short(c.summary_text or "", 520)

        # drop junk titles
        if title.lower() in ("open", "read", "link"):
            title = "Untitled"

        # keep if it has something meaningful
        if title == "Untitled" and not summary and not url:
            return

        self.cards.append(
            Card(
                title=title,
                summary=summary,
                source=src,
                url=url,
                image=c.first_img,
                tags=c.tags[:10],
            )
        )


def build_cards_from_html_digest(html: str, max_cards: int) -> List[Card]:
    p = DigestCardHTMLParser(max_cards=max_cards)
    p.feed(html)
    cards = p.cards

    # If parsing failed (0 cards), fallback: extract anchors (very coarse)
    if cards:
        return cards[:max_cards]

    links = re.findall(r'<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>', html, flags=re.IGNORECASE | re.DOTALL)
    out: List[Card] = []
    for url, txt in links:
        t = norm_space(re.sub(r"<[^>]+>", " ", txt))
        if len(t) < 16:
            continue
        out.append(Card(title=short(t, 180), summary="", source=host_of(url), url=url))
        if len(out) >= max_cards:
            break
    return out[:max_cards]


# ---------------------------
# Source locating
# ---------------------------

def locate_world_politics_sources(repo: Path, date: str) -> Tuple[Optional[Path], Optional[Path]]:
    base = repo / "data" / "world_politics" / "analysis"
    if not base.exists():
        return None, None

    date_files = [p for p in base.glob("*") if date in p.name]

    html_candidates = [p for p in date_files if p.suffix.lower() in (".html", ".htm")]
    json_candidates = [p for p in date_files if p.suffix.lower() == ".json"]

    def score_html(p: Path) -> int:
        n = p.name.lower()
        s = 0
        if "daily_news" in n:
            s += 100
        if "digest" in n:
            s += 30
        return s

    def score_json(p: Path) -> int:
        n = p.name.lower()
        s = 0
        if "view" in n:
            s += 80
        if "daily_summary" in n:
            s += 60
        if "summary" in n:
            s += 20
        return s

    html_candidates.sort(key=lambda p: (score_html(p), p.stat().st_mtime), reverse=True)
    json_candidates.sort(key=lambda p: (score_json(p), p.stat().st_mtime), reverse=True)

    return (html_candidates[0] if html_candidates else None,
            json_candidates[0] if json_candidates else None)


def build_world_politics_section(repo: Path, date: str, max_cards: int) -> Section:
    title = "World Politics"
    try:
        html_src, json_src = locate_world_politics_sources(repo, date)

        cards: List[Card] = []
        notes_parts: List[str] = []

        # 1) Prefer HTML digest -> news-like cards
        if html_src and html_src.exists():
            notes_parts.append(f"source_html={html_src.as_posix()}")
            html_txt = read_text_safe(html_src)
            cards = build_cards_from_html_digest(html_txt, max_cards=max_cards)

        # 2) Fallback to JSON if HTML gives nothing
        if not cards and json_src and json_src.exists():
            notes_parts.append(f"source_json={json_src.as_posix()}")
            obj = read_json_safe(json_src)
            cards = build_cards_from_json(obj, max_cards=max_cards)

        if cards:
            status = "ok"
        else:
            status = "na"
            if not html_src and not json_src:
                notes_parts.append("no_date_matched_sources_found_in=data/world_politics/analysis")
            else:
                notes_parts.append("no_cards_extracted_from_sources")

        notes = "; ".join(notes_parts) if notes_parts else None
        return Section(id="world_politics", title=title, status=status, cards=cards, notes=notes)

    except Exception as e:
        return Section(
            id="world_politics",
            title=title,
            status="error",
            cards=[],
            notes=f"exception={type(e).__name__}: {e}",
        )


# ---------------------------
# Output paths
# ---------------------------

def view_output_path(repo: Path, date: str) -> Path:
    return repo / "data" / "digest" / "view" / f"{date}.json"


def detect_latest_date(repo: Path) -> Optional[str]:
    base = repo / "data" / "world_politics" / "analysis"
    if not base.exists():
        return None

    candidates: List[Tuple[str, Path]] = []
    for p in base.glob("*"):
        d = extract_date_from_filename(p.name)
        if d:
            candidates.append((d, p))

    if not candidates:
        return None

    candidates.sort(key=lambda t: (t[1].stat().st_mtime, t[0]), reverse=True)
    return candidates[0][0]


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Build Digest ViewModel v1 JSON (World Politics first).")
    ap.add_argument(
        "--date",
        help="Target date in YYYY-MM-DD. If omitted, tries to detect latest date from data/world_politics/analysis filenames.",
        default=None,
    )
    ap.add_argument(
        "--section",
        help="Section id to build. Default: world_politics",
        default=DEFAULT_SECTION_ID,
    )
    ap.add_argument("--max-cards", type=int, default=12, help="Max cards per section (default: 12).")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    repo = find_repo_root(Path(__file__).resolve())

    date = args.date
    if date is None:
        date = detect_latest_date(repo)
        if date is None:
            raise SystemExit(
                "[ERROR] --date not provided and cannot detect date from data/world_politics/analysis. "
                "Provide --date YYYY-MM-DD."
            )
    date = validate_date(date)

    section_id = (args.section or DEFAULT_SECTION_ID).strip()
    if section_id != "world_politics":
        sections = [
            Section(
                id=section_id,
                title=section_id.replace("_", " ").title(),
                status="na",
                cards=[],
                notes="section_not_implemented_yet (world_politics is implemented first)",
            )
        ]
    else:
        sections = [build_world_politics_section(repo, date=date, max_cards=args.max_cards)]

    view_model: Dict[str, Any] = {
        "version": VERSION,
        "date": date,
        "sections": [s.to_dict() for s in sections],
        "meta": {
            "generated_at": iso_now_local(),
            "generator": "digest",
            "source": "analyzer",
        },
    }

    out_path = view_output_path(repo, date)
    ensure_dir(out_path.parent)
    out_path.write_text(json.dumps(view_model, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] wrote: {out_path.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
