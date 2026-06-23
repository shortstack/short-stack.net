from __future__ import annotations
import re
import datetime as dt

from markdownify import markdownify as _md

_CARD_COMMENT = re.compile(r"<!--\s*/?kg-card[^>]*-->", re.IGNORECASE)
_BLANKLINES = re.compile(r"\n{3,}")


def clean_tags(names: list[str]) -> list[str]:
    return [n for n in names if n and not n.startswith("#")]


def rewrite_ghost_urls(text: str) -> str:
    return text.replace("__GHOST_URL__", "")


def strip_ghost_card_comments(html: str) -> str:
    return _CARD_COMMENT.sub("", html)


def html_to_markdown(html: str) -> str:
    html = strip_ghost_card_comments(html)
    text = _md(html, heading_style="ATX", strip=["script", "style"])
    text = rewrite_ghost_urls(text)
    return _BLANKLINES.sub("\n\n", text).strip()


def make_filename(date: dt.datetime, slug: str) -> str:
    return f"{date:%Y-%m-%d}-{slug}.txt"
