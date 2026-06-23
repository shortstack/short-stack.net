#!/usr/bin/env python3
from __future__ import annotations
import json
import sys
import datetime as dt
from collections import defaultdict
from pathlib import Path

from ssnet.postfile import Post, dump_post, Page, dump_page
from ssnet.convert import html_to_markdown, clean_tags, make_filename, rewrite_ghost_urls


# Ghost pages to keep, with how they map into the static site.
PAGE_SPEC = {
    "girl":     {"nav": "whoami",  "nav_order": 1, "parent": None},
    "contact":  {"nav": "contact", "nav_order": 2, "parent": None},
    "concerts": {"nav": None,      "nav_order": 100, "parent": "girl"},
}


def migrate_pages(data: dict, outdir: Path) -> int:
    outdir.mkdir(exist_ok=True)
    by_slug = {p["slug"]: p for p in data["posts"] if p.get("type") == "page"}
    n = 0
    for slug, spec in PAGE_SPEC.items():
        p = by_slug.get(slug)
        if not p:
            print(f"  WARN: page '{slug}' not found in export")
            continue
        body = rewrite_ghost_urls(p.get("html") or "")
        # girl links to the concerts page, which now nests under /girl/
        body = body.replace('href="/concerts/"', 'href="/girl/concerts/"')
        body = body.replace('href="/concerts"', 'href="/girl/concerts/"')
        page = Page(
            title=p.get("title") or slug,
            slug=slug,
            body=body,
            format="html",
            nav=spec["nav"],
            nav_order=spec["nav_order"],
            parent=spec["parent"],
        )
        dump_page(page, outdir / f"{slug}.txt")
        n += 1
    return n


def load_data(path: str) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))["db"][0]["data"]


def tag_map(data: dict) -> dict:
    names = {t["id"]: t["name"] for t in data.get("tags", [])}
    by_post: dict[str, list] = defaultdict(list)
    for row in data.get("posts_tags", []):
        nm = names.get(row["tag_id"])
        if nm:
            by_post[row["post_id"]].append((row.get("sort_order", 0), nm))
    return {pid: [n for _, n in sorted(v)] for pid, v in by_post.items()}


def main() -> int:
    export = sys.argv[1] if len(sys.argv) > 1 else "ghost_export.json"
    outdir = Path("posts")
    outdir.mkdir(exist_ok=True)
    data = load_data(export)
    tags = tag_map(data)

    seen: set[str] = set()
    written = 0
    skipped_no_date = 0
    for p in data["posts"]:
        if p.get("status") != "published" or p.get("type") != "post":
            continue
        if not p.get("published_at"):
            skipped_no_date += 1
            continue
        date = dt.datetime.fromisoformat(p["published_at"].replace("Z", "+00:00"))
        html = p.get("html") or ""
        body = html_to_markdown(html) if html else rewrite_ghost_urls(p.get("plaintext") or "")
        slug = p.get("slug") or f"post-{p['id'][:8]}"
        fname = make_filename(date, slug)
        suffix = 2
        while fname in seen:
            fname = make_filename(date, f"{slug}-{suffix}")
            suffix += 1
        seen.add(fname)
        post = Post(
            title=p.get("title") or "(untitled)",
            date=date,
            slug=fname[11:-4],  # strip "YYYY-MM-DD-" prefix and ".txt"
            body=body,
            tags=clean_tags(tags.get(p["id"], [])),
            feature_image=rewrite_ghost_urls(p["feature_image"]) if p.get("feature_image") else None,
            format="markdown",
            favorite=bool(p.get("featured")),
        )
        dump_post(post, outdir / fname)
        written += 1

    favs = sum(1 for p in data["posts"]
               if p.get("status") == "published" and p.get("type") == "post" and p.get("featured"))
    npages = migrate_pages(data, Path("pages"))
    print(f"wrote {written} posts ({favs} favorites) to {outdir}/ "
          f"(skipped {skipped_no_date} with no published_at)")
    print(f"wrote {npages} pages to pages/")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
