import datetime as dt
from ssnet.convert import (
    clean_tags, rewrite_ghost_urls, strip_ghost_card_comments,
    html_to_markdown, make_filename,
)


def test_clean_tags_drops_internal():
    assert clean_tags(["twitter", "#Import 2023", "caylin"]) == ["twitter", "caylin"]


def test_rewrite_ghost_urls():
    assert rewrite_ghost_urls("see __GHOST_URL__/content/images/a.jpg") == \
        "see /content/images/a.jpg"


def test_strip_card_comments():
    h = "<!--kg-card-begin: markdown--><p>hi</p><!--kg-card-end: markdown-->"
    assert strip_ghost_card_comments(h) == "<p>hi</p>"


def test_html_to_markdown_basic_and_url():
    h = '<p>hello</p><p><img src="__GHOST_URL__/content/images/2008/07/x.jpg"></p>'
    out = html_to_markdown(h)
    assert "hello" in out
    assert "/content/images/2008/07/x.jpg" in out
    assert "__GHOST_URL__" not in out


def test_make_filename():
    d = dt.datetime(2008, 7, 14, 3, 21, tzinfo=dt.timezone.utc)
    assert make_filename(d, "my-slug") == "2008-07-14-my-slug.txt"
