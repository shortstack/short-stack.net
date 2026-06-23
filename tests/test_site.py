import datetime as dt
import json
from pathlib import Path
from ssnet.postfile import Post, dump_post
from ssnet.site import build_site

CFG = {
    "site_title": "T", "site_description": "d", "base_url": "https://x",
    "author": "A", "posts_per_page": 2, "rss_count": 10, "aws": {},
}


def seed(posts_dir, n):
    for i in range(n):
        dump_post(Post(
            title=f"Post {i}",
            date=dt.datetime(2010 + i % 3, 1, 1, tzinfo=dt.timezone.utc),
            slug=f"post-{i}", body=f"body {i}", tags=["twitter"] if i % 2 else ["food"],
        ), Path(posts_dir) / f"p{i}.txt")


def test_build_creates_pages(tmp_path):
    pd = tmp_path / "posts"
    pd.mkdir()
    seed(pd, 5)
    out = tmp_path / "site"
    counts = build_site(CFG, posts_dir=pd, out_dir=out,
                        templates_dir="templates", static_dir="static",
                        pages_dir=tmp_path / "nopages")
    assert counts["posts"] == 5
    assert (out / "index.html").exists()
    assert (out / "page" / "2" / "index.html").exists()       # 5 posts / 2 per page = 3 pages
    assert (out / "post-0" / "index.html").exists()
    assert (out / "archive" / "index.html").exists()
    assert (out / "archive" / "2010" / "index.html").exists()
    assert (out / "tag" / "food" / "index.html").exists()
    assert (out / "rss.xml").exists()
    assert (out / "404.html").exists()
    assert (out / "style.css").exists()
    idx = json.loads((out / "search-index.json").read_text())
    assert len(idx) == 5 and "title" in idx[0] and "url" in idx[0]


def test_year_slug_post_does_not_collide_with_archive(tmp_path):
    pd = tmp_path / "posts"
    pd.mkdir()
    dump_post(Post(title="2010 recap",
                   date=dt.datetime(2010, 12, 31, tzinfo=dt.timezone.utc),
                   slug="2010", body="the year in review"),
              pd / "recap.txt")
    out = tmp_path / "site"
    build_site(CFG, posts_dir=pd, out_dir=out,
               templates_dir="templates", static_dir="static",
               pages_dir=tmp_path / "nopages")
    # post lives at /2010/, year archive at /archive/2010/ — both present
    assert "the year in review" in (out / "2010" / "index.html").read_text()
    assert (out / "archive" / "2010" / "index.html").exists()


def test_reserved_slug_raises(tmp_path):
    import pytest
    pd = tmp_path / "posts"
    pd.mkdir()
    dump_post(Post(title="x", date=dt.datetime(2010, 1, 1, tzinfo=dt.timezone.utc),
                   slug="search", body="b"), pd / "x.txt")
    with pytest.raises(ValueError):
        build_site(CFG, posts_dir=pd, out_dir=tmp_path / "s",
                   templates_dir="templates", static_dir="static",
                   pages_dir=tmp_path / "nopages")


def test_favorite_heart_and_pages(tmp_path):
    from ssnet.postfile import Page, dump_page
    pd = tmp_path / "posts"
    pd.mkdir()
    dump_post(Post(title="Fave", date=dt.datetime(2011, 1, 1, tzinfo=dt.timezone.utc),
                   slug="fave", body="b", favorite=True), pd / "f.txt")
    dump_post(Post(title="Plain", date=dt.datetime(2011, 1, 2, tzinfo=dt.timezone.utc),
                   slug="plain", body="b"), pd / "p.txt")
    pgd = tmp_path / "pages"
    pgd.mkdir()
    dump_page(Page(title="whoami", slug="girl", body="<p>me</p>", format="html",
                   nav="whoami", nav_order=1), pgd / "girl.txt")
    dump_page(Page(title="concerts", slug="concerts", body="<p>shows</p>",
                   format="html", parent="girl"), pgd / "concerts.txt")
    out = tmp_path / "site"
    counts = build_site(CFG, posts_dir=pd, out_dir=out, templates_dir="templates",
                        static_dir="static", pages_dir=pgd)
    assert counts["favorites"] == 1 and counts["static_pages"] == 2
    # favorite heart shows on the favorite's post page, not the plain one
    # (use the exact heart class so the nav's .navfav doesn't false-match)
    assert 'class="fav"' in (out / "fave" / "index.html").read_text()
    assert 'class="fav"' not in (out / "plain" / "index.html").read_text()
    # /favorites/ page lists the favorite (and only it); nav has the heart link
    favs_html = (out / "favorites" / "index.html").read_text()
    assert "/fave/" in favs_html and "/plain/" not in favs_html
    assert 'class="navfav"' in favs_html and 'href="/favorites/"' in favs_html
    # pages built; concerts nests under girl; whoami in nav
    assert (out / "girl" / "index.html").exists()
    assert (out / "girl" / "concerts" / "index.html").exists()
    assert "/girl/" in (out / "girl" / "index.html").read_text()  # nav link


def test_external_nav_links_interleaved(tmp_path):
    from ssnet.postfile import Page, dump_page
    pd = tmp_path / "posts"
    pd.mkdir()
    dump_post(Post(title="p", date=dt.datetime(2011, 1, 1, tzinfo=dt.timezone.utc),
                   slug="p", body="b"), pd / "p.txt")
    pgd = tmp_path / "pages"
    pgd.mkdir()
    dump_page(Page(title="whoami", slug="girl", body="x", nav="whoami", nav_order=1),
              pgd / "girl.txt")
    dump_page(Page(title="contact", slug="contact", body="x", nav="contact", nav_order=5),
              pgd / "contact.txt")
    cfg = dict(CFG)
    cfg["nav_links"] = [
        {"label": "art", "url": "https://art.example", "nav_order": 3},
        {"label": "portfolio", "url": "https://port.example", "nav_order": 2},
    ]
    out = tmp_path / "site"
    build_site(cfg, posts_dir=pd, out_dir=out, templates_dir="templates",
               static_dir="static", pages_dir=pgd)
    nav = (out / "index.html").read_text()
    # external links present, open in new tab, and ordered whoami<portfolio<art<contact
    assert 'href="https://art.example" target="_blank"' in nav
    order = [nav.index(s) for s in ("whoami", "https://port.example",
                                    "https://art.example", ">contact<")]
    assert order == sorted(order)
