from __future__ import annotations
import json
import shutil
from collections import defaultdict
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from feedgen.feed import FeedGenerator

from ssnet.postfile import load_all_posts, load_all_pages
from ssnet.render import render_body, excerpt


def _write(path: Path, html: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")


def _chunk(seq, size):
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


# Top-level path segments the generator owns; a post slug must not shadow them.
RESERVED_SLUGS = {"archive", "tag", "page", "search", "content", "favorites"}


def build_site(config, posts_dir="posts", out_dir="site",
               templates_dir="templates", static_dir="static",
               pages_dir="pages") -> dict:
    posts = load_all_posts(posts_dir)
    pages = load_all_pages(pages_dir)
    # top-level page slugs are also reserved against post slugs
    page_top_slugs = {pg.slug for pg in pages if not pg.parent}
    clashes = sorted({p.slug for p in posts} & (RESERVED_SLUGS | page_top_slugs))
    if clashes:
        raise ValueError(f"post slug(s) collide with reserved paths: {clashes}")
    out = Path(out_dir)
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    env = Environment(
        loader=FileSystemLoader(templates_dir),
        autoescape=select_autoescape(["html"]),
    )
    site = {k: v for k, v in config.items() if k != "aws"}
    # nav = page links + external links from config, interleaved by nav_order
    nav_items = [
        {"url": pg.url, "label": pg.nav, "order": pg.nav_order, "external": False}
        for pg in pages if pg.nav
    ]
    for nl in config.get("nav_links", []):
        nav_items.append({"url": nl["url"], "label": nl["label"],
                          "order": nl.get("nav_order", 100), "external": True})
    nav_items.sort(key=lambda x: x["order"])
    site["nav_pages"] = nav_items

    # attach derived fields used by list templates
    for p in posts:
        p.excerpt = excerpt(p)  # type: ignore[attr-defined]

    per = int(config.get("posts_per_page", 25))
    feed_pages = list(_chunk(posts, per)) or [[]]
    total = len(feed_pages)
    idx_tpl = env.get_template("index.html")
    for n, chunk in enumerate(feed_pages, start=1):
        prev_url = ("/" if n == 2 else f"/page/{n-1}/") if n > 1 else None
        next_url = f"/page/{n+1}/" if n < total else None
        html = idx_tpl.render(site=site, posts=chunk, page=n, total_pages=total,
                              prev_url=prev_url, next_url=next_url)
        _write(out / "index.html" if n == 1 else out / "page" / str(n) / "index.html", html)

    post_tpl = env.get_template("post.html")
    for p in posts:
        html = post_tpl.render(site=site, post=p, body_html=render_body(p))
        _write(out / p.slug / "index.html", html)

    # standalone pages (girl, concerts, contact) — concerts nests under girl
    page_tpl = env.get_template("page.html")
    for pg in pages:
        html = page_tpl.render(site=site, page=pg, body_html=render_body(pg))
        _write(out / pg.out_dir / "index.html", html)

    # archives
    by_year = defaultdict(list)
    for p in posts:
        by_year[p.year].append(p)
    years = [{"year": y, "count": len(v)} for y, v in sorted(by_year.items(), reverse=True)]
    _write(out / "archive" / "index.html",
           env.get_template("archive.html").render(site=site, years=years))
    yr_tpl = env.get_template("archive_year.html")
    for y, plist in by_year.items():
        _write(out / "archive" / str(y) / "index.html",
               yr_tpl.render(site=site, year=y, posts=plist))

    # tags
    by_tag = defaultdict(list)
    for p in posts:
        for t in p.tags:
            by_tag[t].append(p)
    tag_tpl = env.get_template("tag.html")
    for t, plist in by_tag.items():
        _write(out / "tag" / t / "index.html",
               tag_tpl.render(site=site, tag=t, posts=plist))

    # favorites listing
    favs = [p for p in posts if p.favorite]
    _write(out / "favorites" / "index.html",
           env.get_template("favorites.html").render(site=site, posts=favs))

    # search page + index
    _write(out / "search" / "index.html",
           env.get_template("search.html").render(site=site))
    index = [{"title": p.title, "url": p.url, "date": p.date.strftime("%Y-%m-%d"),
              "text": p.excerpt} for p in posts]
    _write(out / "search-index.json", json.dumps(index, ensure_ascii=False))

    # rss
    fg = FeedGenerator()
    fg.title(config["site_title"])
    fg.link(href=config["base_url"], rel="alternate")
    fg.description(config.get("site_description", ""))
    fg.id(config["base_url"])
    for p in posts[: int(config.get("rss_count", 50))]:
        fe = fg.add_entry(order="append")   # keep our newest-first order
        fe.id(config["base_url"] + p.url)
        fe.title(p.title)
        fe.link(href=config["base_url"] + p.url)
        fe.published(p.date)
        fe.description(p.excerpt)
    fg.rss_file(str(out / "rss.xml"))

    # 404
    _write(out / "404.html",
           "<!doctype html><meta charset=utf-8><title>404</title>"
           "<body style='background:#0b0e14;color:#cdd6f4;font-family:monospace;"
           "text-align:center;padding:4rem'>$ 404 — not found. "
           "<a style='color:#89b4fa' href='/'>cd /</a></body>")

    # static
    for f in Path(static_dir).iterdir():
        if f.is_file():
            shutil.copy(f, out / f.name)

    return {"posts": len(posts), "feed_pages": total, "static_pages": len(pages),
            "favorites": sum(1 for p in posts if p.favorite),
            "tags": len(by_tag), "years": len(by_year)}
