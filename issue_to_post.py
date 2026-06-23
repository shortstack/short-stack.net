#!/usr/bin/env python3
"""Turn a parsed GitHub Issue Form into a published post (posts/*.txt + images)."""
from __future__ import annotations
import re
import urllib.parse
import urllib.request
from pathlib import Path


def slugify(title: str) -> str:
    s = title.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    return s.strip("-")


def unique_slug(base: str, taken) -> str:
    base = base or "post"
    if base not in taken:
        return base
    n = 2
    while f"{base}-{n}" in taken:
        n += 1
    return f"{base}-{n}"


def parse_tags(raw: str) -> list[str]:
    return [t.strip() for t in (raw or "").split(",") if t.strip()]


def is_favorite(raw: str) -> bool:
    return (raw or "").strip().lower() == "yes"


_GH_HOSTS = ("github.com/user-attachments/", "githubusercontent.com")
_MD_IMG = re.compile(r"!\[[^\]]*\]\(\s*(\S+?)\s*(?:\"[^\"]*\")?\s*\)")
_HTML_IMG = re.compile(r'<img[^>]+src="([^"]+)"', re.I)


def find_image_urls(body: str) -> list[str]:
    found = _MD_IMG.findall(body) + _HTML_IMG.findall(body)
    out: list[str] = []
    for u in found:
        if any(h in u for h in _GH_HOSTS) and u not in out:
            out.append(u)
    return out


def ext_from(url: str, content_type: str) -> str:
    path = urllib.parse.urlparse(url).path
    m = re.search(r"\.(png|jpe?g|gif|webp)$", path, re.I)
    if m:
        return "." + m.group(1).lower().replace("jpeg", "jpg")
    ct = (content_type or "").lower()
    for key, ext in (("png", ".png"), ("jpeg", ".jpg"), ("jpg", ".jpg"),
                     ("gif", ".gif"), ("webp", ".webp")):
        if key in ct:
            return ext
    return ".png"


class _NoAuthRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        new = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new is not None:
            new.headers = {k: v for k, v in new.headers.items()
                           if k.lower() != "authorization"}
        return new


def _http_get(url: str, token=None) -> tuple[bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": "ssnet-blog-bot"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    opener = urllib.request.build_opener(_NoAuthRedirect())
    with opener.open(req, timeout=30) as r:
        return r.read(), r.headers.get("Content-Type", "")


def rehost_images(body, slug, when, token, out_root, fetch=None):
    fetch = fetch or _http_get
    out_root = Path(out_root)
    warnings = []
    mapping = {}            # url -> new path, built in find order (for numbering)
    count = 0
    for url in find_image_urls(body):
        try:
            data, ctype = fetch(url, token)
        except Exception as e:  # noqa: BLE001 - report, keep original URL
            warnings.append(f"failed to download {url}: {e}")
            continue
        count += 1
        ext = ext_from(url, ctype)
        rel = f"{when:%Y}/{when:%m}/{slug}-{count}{ext}"
        dest = out_root / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        mapping[url] = f"/content/images/{rel}"
    new_body = body
    for url in sorted(mapping, key=len, reverse=True):   # longest first → no substring clobber
        new_body = new_body.replace(url, mapping[url])
    return new_body, count, warnings


import datetime as dt
import os
import sys

from ssnet.postfile import Post, dump_post, load_all_posts, load_all_pages
from ssnet.site import RESERVED_SLUGS


def _taken_slugs() -> set:
    taken = set(RESERVED_SLUGS)
    taken |= {p.slug for p in load_all_posts("posts")}
    taken |= {pg.slug for pg in load_all_pages("pages")}
    return taken


def main() -> int:
    title = (os.environ.get("POST_TITLE") or "").strip()
    body = (os.environ.get("POST_BODY") or "").strip()
    if not title or not body:
        print("ERROR: title and body are required", file=sys.stderr)
        return 1

    now_iso = os.environ.get("NOW_ISO") or dt.datetime.now(dt.timezone.utc).isoformat()
    when = dt.datetime.fromisoformat(now_iso.replace("Z", "+00:00"))
    token = os.environ.get("GITHUB_TOKEN")

    slug = unique_slug(slugify(title), _taken_slugs())
    new_body, img_count, warnings = rehost_images(
        body, slug, when, token, Path("content/images"))

    post = Post(title=title, date=when, slug=slug, body=new_body,
                tags=parse_tags(os.environ.get("POST_TAGS", "")),
                feature_image=None, format="markdown",
                favorite=is_favorite(os.environ.get("POST_FAVORITE", "")))
    dump_post(post, Path("posts") / f"{when:%Y-%m-%d}-{slug}.txt")

    url = f"/{slug}/"
    gho = os.environ.get("GITHUB_OUTPUT")
    if gho:
        with open(gho, "a", encoding="utf-8") as f:
            f.write(f"slug={slug}\nurl={url}\nimage_count={img_count}\n")
            f.write(f"warnings={' | '.join(warnings)}\n")
    print(f"wrote posts/{when:%Y-%m-%d}-{slug}.txt "
          f"(images: {img_count}, warnings: {len(warnings)})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
