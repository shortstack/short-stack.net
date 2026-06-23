import datetime as dt
from ssnet.postfile import Post
from ssnet.render import (render_markdown, decorate_images, decorate_links,
                          render_body, excerpt)


def mkpost(body, fmt="markdown"):
    return Post(title="t", date=dt.datetime(2008, 1, 1, tzinfo=dt.timezone.utc),
                slug="s", body=body, format=fmt)


def test_render_markdown():
    assert "<strong>hi</strong>" in render_markdown("**hi**")


def test_external_links_open_new_tab():
    out = decorate_links('<a href="https://x.com">x</a> <a href="/local/">l</a>')
    assert 'target="_blank"' in out and 'rel="noopener noreferrer"' in out
    # internal link untouched
    assert '<a href="/local/">l</a>' in out


def test_render_body_decorates_external_links():
    out = render_body(mkpost("see [x](https://example.com)"))
    assert 'href="https://example.com"' in out and 'target="_blank"' in out


def test_decorate_images_adds_attrs():
    out = decorate_images('<img src="/content/images/x.jpg">')
    assert 'class="post-img"' in out
    assert 'data-original="/content/images/x.jpg"' in out
    assert 'loading="lazy"' in out


def test_render_body_markdown_decorates():
    out = render_body(mkpost("![](/content/images/x.jpg)"))
    assert "post-img" in out


def test_render_body_html_passthrough():
    out = render_body(mkpost("<p>raw</p>", fmt="html"))
    assert "<p>raw</p>" in out


def test_excerpt_truncates():
    e = excerpt(mkpost("word " * 100), length=40)
    assert len(e) <= 60 and e.endswith("…")
