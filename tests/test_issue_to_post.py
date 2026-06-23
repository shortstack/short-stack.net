import datetime as dt
import os
from pathlib import Path
import issue_to_post
from issue_to_post import slugify, unique_slug, parse_tags, is_favorite, find_image_urls, ext_from, rehost_images


def test_slugify():
    assert slugify("Crossfit Day 1: Aftermath!") == "crossfit-day-1-aftermath"
    assert slugify("  Hello,  World  ") == "hello-world"
    assert slugify("***") == ""


def test_unique_slug():
    taken = {"hello", "hello-2"}
    assert unique_slug("hello", taken) == "hello-3"
    assert unique_slug("fresh", taken) == "fresh"
    assert unique_slug("", taken) == "post"


def test_parse_tags():
    assert parse_tags("crossfit, life ,, update") == ["crossfit", "life", "update"]
    assert parse_tags("") == []
    assert parse_tags("   ") == []


def test_is_favorite():
    assert is_favorite("yes") is True
    assert is_favorite("YES") is True
    assert is_favorite("no") is False
    assert is_favorite("") is False


def test_find_image_urls():
    body = (
        "![a](https://github.com/user-attachments/assets/abc)\n"
        '<img src="https://user-images.githubusercontent.com/1/x.png">\n'
        "![ext](https://example.com/not-github.png)\n"
        "![dup](https://github.com/user-attachments/assets/abc)"
    )
    urls = find_image_urls(body)
    assert urls == [
        "https://github.com/user-attachments/assets/abc",
        "https://user-images.githubusercontent.com/1/x.png",
    ]


def test_ext_from():
    assert ext_from("https://x/y.JPG", "") == ".jpg"
    assert ext_from("https://github.com/user-attachments/assets/abc", "image/png") == ".png"
    assert ext_from("https://x/y", "") == ".png"


def test_rehost_images_writes_and_rewrites(tmp_path):
    calls = []

    def fake_fetch(url, token):
        calls.append((url, token))
        return (b"IMGDATA", "image/png")

    body = "see ![pic](https://github.com/user-attachments/assets/abc) end"
    when = dt.datetime(2026, 6, 22, tzinfo=dt.timezone.utc)
    out = tmp_path / "content" / "images"
    new_body, count, warns = rehost_images(body, "my-post", when, "tok", out, fetch=fake_fetch)

    assert count == 1 and warns == []
    assert "/content/images/2026/06/my-post-1.png" in new_body
    assert "github.com" not in new_body
    assert (out / "2026" / "06" / "my-post-1.png").read_bytes() == b"IMGDATA"
    assert calls == [("https://github.com/user-attachments/assets/abc", "tok")]


def test_rehost_images_download_failure_keeps_url(tmp_path):
    def boom(url, token):
        raise RuntimeError("403")

    body = "![x](https://github.com/user-attachments/assets/zzz)"
    when = dt.datetime(2026, 6, 22, tzinfo=dt.timezone.utc)
    new_body, count, warns = rehost_images(body, "p", when, None,
                                           tmp_path / "ci", fetch=boom)
    assert count == 0 and len(warns) == 1
    assert "github.com/user-attachments/assets/zzz" in new_body  # untouched


def test_noauth_redirect_strips_authorization():
    import io
    import urllib.request
    from issue_to_post import _NoAuthRedirect
    req = urllib.request.Request("https://github.com/x", headers={"User-Agent": "b"})
    req.add_header("Authorization", "Bearer secret")
    new = _NoAuthRedirect().redirect_request(
        req, io.BytesIO(b""), 302, "Found", {}, "https://signed.s3.example/obj")
    assert new is not None
    hdrs = {k.lower(): v for k, v in new.headers.items()}
    unredir = {k.lower(): v for k, v in new.unredirected_hdrs.items()}
    assert "authorization" not in hdrs
    assert "authorization" not in unredir


def test_main_writes_post_and_outputs(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "posts").mkdir()
    (tmp_path / "pages").mkdir()
    monkeypatch.setattr(issue_to_post, "_http_get",
                        lambda url, token: (b"IMG", "image/png"))
    out_file = tmp_path / "ghout"
    env = {
        "POST_TITLE": "Crossfit Day 1",
        "POST_TAGS": "crossfit, life",
        "POST_FAVORITE": "yes",
        "POST_BODY": "hi ![p](https://github.com/user-attachments/assets/abc)",
        "NOW_ISO": "2026-06-22T15:30:00Z",
        "GITHUB_TOKEN": "tok",
        "GITHUB_OUTPUT": str(out_file),
    }
    for k, v in env.items():
        monkeypatch.setenv(k, v)

    rc = issue_to_post.main()
    assert rc == 0

    post = tmp_path / "posts" / "2026-06-22-crossfit-day-1.txt"
    text = post.read_text()
    assert "title: Crossfit Day 1" in text
    assert "favorite: true" in text
    assert "tags:" in text and "crossfit" in text
    assert "/content/images/2026/06/crossfit-day-1-1.png" in text
    assert (tmp_path / "content" / "images" / "2026" / "06"
            / "crossfit-day-1-1.png").exists()
    outputs = out_file.read_text()
    assert "slug=crossfit-day-1" in outputs
    assert "url=/crossfit-day-1/" in outputs


def test_rehost_images_prefix_collision(tmp_path):
    import datetime as dt
    from issue_to_post import rehost_images
    seq = iter([(b"A", "image/png"), (b"B", "image/png")])

    def fake_fetch(url, token):
        return next(seq)

    # second URL contains the first as a prefix
    short = "https://github.com/user-attachments/assets/abc"
    long = "https://github.com/user-attachments/assets/abcdef"
    body = f"![a]({short}) and ![b]({long})"
    when = dt.datetime(2026, 6, 22, tzinfo=dt.timezone.utc)
    new_body, count, warns = rehost_images(body, "p", when, None,
                                           tmp_path / "ci", fetch=fake_fetch)
    assert count == 2 and warns == []
    assert "![a](/content/images/2026/06/p-1.png) and ![b](/content/images/2026/06/p-2.png)" == new_body


def test_main_blank_title_fails(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "posts").mkdir()
    (tmp_path / "pages").mkdir()
    monkeypatch.setenv("POST_TITLE", "")
    monkeypatch.setenv("POST_BODY", "something")
    monkeypatch.setenv("NOW_ISO", "2026-06-22T00:00:00Z")
    assert issue_to_post.main() != 0
