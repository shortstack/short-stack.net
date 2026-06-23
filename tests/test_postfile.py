import datetime as dt
from pathlib import Path
from ssnet.postfile import Post, post_to_text, load_post, dump_post, load_all_posts


def make(slug="hello", when="2008-07-14T03:21:00+00:00"):
    return Post(
        title="Hello, World",
        date=dt.datetime.fromisoformat(when),
        slug=slug,
        body="hi there\n\n![](/content/images/2008/07/x.jpg)",
        tags=["caylin"],
        feature_image=None,
        format="markdown",
    )


def test_roundtrip(tmp_path):
    p = make()
    path = tmp_path / "post.txt"
    dump_post(p, path)
    loaded = load_post(path)
    assert loaded.title == p.title
    assert loaded.slug == "hello"
    assert loaded.tags == ["caylin"]
    assert loaded.body.strip() == p.body.strip()
    assert loaded.date == p.date


def test_url_and_year():
    p = make()
    assert p.url == "/hello/"
    assert p.year == 2008


def test_favorite_roundtrip(tmp_path):
    p = make()
    p.favorite = True
    path = tmp_path / "f.txt"
    dump_post(p, path)
    assert load_post(path).favorite is True
    # default is False
    p2 = make(slug="x")
    dump_post(p2, tmp_path / "x.txt")
    assert load_post(tmp_path / "x.txt").favorite is False


def test_page_roundtrip_and_nesting(tmp_path):
    from ssnet.postfile import Page, dump_page, load_page
    pg = Page(title="concerts", slug="concerts", body="<p>x</p>", format="html",
              parent="girl", nav=None)
    path = tmp_path / "c.txt"
    dump_page(pg, path)
    loaded = load_page(path)
    assert loaded.slug == "concerts" and loaded.parent == "girl"
    assert loaded.url == "/girl/concerts/"
    assert loaded.out_dir == "girl/concerts"
    assert loaded.nav is None


def test_load_all_sorted_newest_first(tmp_path):
    dump_post(make(slug="old", when="2005-01-01T00:00:00+00:00"), tmp_path / "a.txt")
    dump_post(make(slug="new", when="2020-01-01T00:00:00+00:00"), tmp_path / "b.txt")
    posts = load_all_posts(tmp_path)
    assert [p.slug for p in posts] == ["new", "old"]
