from __future__ import annotations
import datetime as dt
import zoneinfo
from dataclasses import dataclass, field
from pathlib import Path

import frontmatter

# Posts authored on/after this date are written in UTC; everything older was
# written in the author's local Eastern time (stored as wall-clock with a
# +00:00 offset), so its displayed time gets a DST-correct EST/EDT label.
_UTC_CUTOFF = dt.date(2026, 6, 23)
_EASTERN = zoneinfo.ZoneInfo("America/New_York")


@dataclass
class Post:
    title: str
    date: dt.datetime
    slug: str
    body: str
    tags: list[str] = field(default_factory=list)
    feature_image: str | None = None
    format: str = "markdown"
    favorite: bool = False

    @property
    def year(self) -> int:
        return self.date.year

    @property
    def tz_label(self) -> str:
        """Timezone abbreviation to show next to the time.

        UTC for posts on/after the cutoff (and all future posts); DST-correct
        EST/EDT for older posts, whose stored wall-clock is Eastern local time.
        """
        if self.date.date() >= _UTC_CUTOFF:
            return "UTC"
        return self.date.replace(tzinfo=_EASTERN).tzname()

    @property
    def url(self) -> str:
        return f"/{self.slug}/"


@dataclass
class Page:
    title: str
    slug: str
    body: str
    format: str = "html"
    nav: str | None = None          # nav label; None = not in nav
    nav_order: int = 100
    parent: str | None = None       # parent page slug, for nesting

    @property
    def url(self) -> str:
        return f"/{self.parent}/{self.slug}/" if self.parent else f"/{self.slug}/"

    @property
    def out_dir(self) -> str:
        return f"{self.parent}/{self.slug}" if self.parent else self.slug


def _parse_date(v) -> dt.datetime:
    if isinstance(v, dt.datetime):
        d = v
    elif isinstance(v, dt.date):
        d = dt.datetime(v.year, v.month, v.day)
    else:
        d = dt.datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    if d.tzinfo is None:
        d = d.replace(tzinfo=dt.timezone.utc)
    return d


def load_post(path) -> Post:
    fm = frontmatter.load(str(path))
    m = fm.metadata
    return Post(
        title=m.get("title") or "(untitled)",
        date=_parse_date(m["date"]),
        slug=str(m["slug"]),
        body=fm.content,
        tags=list(m.get("tags") or []),
        feature_image=(m.get("feature_image") or None),
        format=m.get("format", "markdown"),
        favorite=bool(m.get("favorite", False)),
    )


def post_to_text(post: Post) -> str:
    meta = {
        "title": post.title,
        "date": post.date.isoformat(),
        "slug": post.slug,
        "tags": post.tags,
        "feature_image": post.feature_image or "",
        "format": post.format,
        "favorite": post.favorite,
    }
    return frontmatter.dumps(frontmatter.Post(post.body, **meta))


def dump_post(post: Post, path) -> None:
    Path(path).write_text(post_to_text(post), encoding="utf-8")


def load_all_posts(posts_dir) -> list[Post]:
    posts = [load_post(p) for p in sorted(Path(posts_dir).glob("*.txt"))]
    posts.sort(key=lambda p: p.date, reverse=True)
    return posts


def load_page(path) -> Page:
    fm = frontmatter.load(str(path))
    m = fm.metadata
    return Page(
        title=m.get("title") or "",
        slug=str(m["slug"]),
        body=fm.content,
        format=m.get("format", "html"),
        nav=(m.get("nav") or None),
        nav_order=int(m.get("nav_order", 100)),
        parent=(m.get("parent") or None),
    )


def page_to_text(page: Page) -> str:
    meta = {
        "title": page.title,
        "slug": page.slug,
        "format": page.format,
        "nav": page.nav or "",
        "nav_order": page.nav_order,
        "parent": page.parent or "",
    }
    return frontmatter.dumps(frontmatter.Post(page.body, **meta))


def dump_page(page: Page, path) -> None:
    Path(path).write_text(page_to_text(page), encoding="utf-8")


def load_all_pages(pages_dir) -> list[Page]:
    d = Path(pages_dir)
    if not d.is_dir():
        return []
    return [load_page(p) for p in sorted(d.glob("*.txt"))]
