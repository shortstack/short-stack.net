from __future__ import annotations
import markdown as _markdown
from bs4 import BeautifulSoup

from ssnet.postfile import Post

_MD_EXT = ["extra", "sane_lists", "nl2br"]


def render_markdown(text: str) -> str:
    return _markdown.markdown(text, extensions=_MD_EXT)


def decorate_images(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for img in soup.find_all("img"):
        src = img.get("src", "")
        img["data-original"] = src
        classes = img.get("class", [])
        if "post-img" not in classes:
            classes = classes + ["post-img"]
        img["class"] = classes
        if not img.get("loading"):
            img["loading"] = "lazy"
    return str(soup)


def decorate_links(html: str) -> str:
    """Open external links (absolute http/https) in a new tab."""
    soup = BeautifulSoup(html, "html.parser")
    for a in soup.find_all("a"):
        href = a.get("href", "")
        if href.startswith(("http://", "https://")) and not a.get("target"):
            a["target"] = "_blank"
            a["rel"] = "noopener noreferrer"
    return str(soup)


def render_body(post: Post) -> str:
    html = post.body if post.format == "html" else render_markdown(post.body)
    return decorate_links(decorate_images(html))


def excerpt(post: Post, length: int = 240) -> str:
    text = BeautifulSoup(render_body(post), "html.parser").get_text(" ", strip=True)
    if len(text) <= length:
        return text
    return text[:length].rsplit(" ", 1)[0] + "…"
