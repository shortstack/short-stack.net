# short-stack.net

The static-site engine behind **[short-stack.net](https://short-stack.net)** — a
self-owned blog migrated off Ghost. Posts and pages are plain `.txt` files
(front matter + Markdown); a small Python generator renders them into a terminal-
themed static site hosted on **S3 + CloudFront**, with images served from a separate
S3 bucket.

**Stack:** Python (Jinja2 · python-markdown · markdownify · python-frontmatter ·
BeautifulSoup · feedgen) → static HTML → S3 + CloudFront. No database, no runtime.

```
posts/  pages/  →  build.py  →  site/  →  publish.py  →  S3 + CloudFront
```

---

## ✍️ Authoring Guide

Everything you need to **write, edit, and publish** posts and pages.

> **TL;DR** — drop a `.txt` file in `posts/`, run `python publish.py`. Done.

---

## 📑 Contents

1. [Publish from a GitHub issue](#-publish-from-a-github-issue)
2. [One-time setup](#-one-time-setup)
3. [How the blog is organized](#-how-the-blog-is-organized)
4. [Write a new post](#-write-a-new-post)
5. [Add images to a post](#-add-images-to-a-post)
6. [Mark a post as a favorite ♥](#-mark-a-post-as-a-favorite-)
7. [Edit an existing post](#-edit-an-existing-post)
8. [Create or edit a page](#-create-or-edit-a-page)
9. [Preview locally](#-preview-locally)
10. [Publish to short-stack.net](#-publish-to-short-stacknet)
11. [Field reference](#-field-reference)
12. [Gotchas & rules](#-gotchas--rules)

---

## 🐙 Publish from a GitHub issue

The lazy path — no local files, no terminal:

1. **Issues → New issue → "New blog post."**
2. Fill in **Title**, **Tags** (comma-separated), **Favorite?**, and the **Body** (Markdown). Submit — it auto-gets the `post` label and the rendered issue is your draft preview.
3. When happy, **add the `publish` label.** A GitHub Action turns the issue into `posts/YYYY-MM-DD-slug.txt`, deploys, then comments the live URL and closes the issue.

**Images:** drag-and-drop them straight into the issue body. On publish, the Action downloads each one and re-hosts it to S3 under `content/images/`, rewriting the post to a root-relative `/content/images/...` URL. (This relies on the repo being **public** so GitHub serves the attachments; on a private repo the download 404s and the image falls back to a placeholder — commit the file under `content/images/` and reference it instead.)

---

## 🔧 One-time setup

Only needed the first time on a machine (after cloning the repo).

```bash
cd /path/to/blog            # wherever you cloned it

# 1. Python environment + dependencies
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 2. AWS credentials (only needed to PUBLISH, not to write/preview)
#    Point these at your access-key CSV (id in column 2, secret in column 3).
AK=$(awk -F, 'NR==2{print $2}' /path/to/credentials.csv)
SK=$(awk -F, 'NR==2{print $3}' /path/to/credentials.csv)
aws configure set aws_access_key_id "$AK"     --profile ssnet
aws configure set aws_secret_access_key "$SK" --profile ssnet
aws configure set region us-east-1            --profile ssnet
aws sts get-caller-identity --profile ssnet    # should print your AWS account id
```

> 💡 **Always run `build.py` / `publish.py` from the repo root** (the folder with
> `config.toml`). All paths are relative to it.

---

## 🗂 How the blog is organized

| Folder/File | What it is |
|---|---|
| `posts/` | One `.txt` per blog post — **this is where you write** |
| `pages/` | Standalone pages (whoami / concerts / contact) |
| `content/images/` | *(optional, local)* new images to upload, mirrored to S3 |
| `templates/`, `static/` | Theme (HTML + CSS + JS) — only touch for design changes |
| `build.py` | Generates the site into `site/` (local, no internet) |
| `publish.py` | Uploads images, builds, deploys to S3, refreshes CloudFront |
| `config.toml` | Site title, base URL, bucket names, CloudFront ID |
| `migrate.py` | One-time Ghost import — **you won't need this again** |

A post file is **YAML front matter** (between `---` lines) + a **Markdown body**.

---

## 📝 Write a new post

### Step 1 — create the file

Name it `posts/YYYY-MM-DD-your-slug.txt`. The date prefix keeps posts sorted; the
slug becomes the URL (`/your-slug/`).

```bash
# from the repo root
$EDITOR posts/2026-06-22-hello-again.txt
```

### Step 2 — paste this template and fill it in

```text
---
title: Hello Again
date: '2026-06-22T14:30:00+00:00'
slug: hello-again
tags: [life, update]
feature_image: ''
format: markdown
favorite: false
---
It's been a while. Here's what I've been up to...

## A heading

Regular **Markdown** works — *italics*, [links](https://example.com), lists:

- one
- two

> a blockquote
```

### Step 3 — preview, then publish

```bash
.venv/bin/python build.py          # generate
.venv/bin/python -m http.server -d site 8765   # open http://localhost:8765/
# happy? ship it:
.venv/bin/python publish.py
```

That's it — the post is live at `https://short-stack.net/hello-again/`.

> 🧭 **What goes in `date`?** Any ISO timestamp. Use UTC (`+00:00`). Newer dates
> sort to the top of the feed.

---

## 🖼 Add images to a post

1. Put the image(s) on disk under a **local** `content/images/YYYY/MM/` folder in the
   repo (any subpath you like — it mirrors 1:1 to S3):

   ```bash
   mkdir -p content/images/2026/06
   cp ~/Desktop/sunset.jpg content/images/2026/06/sunset.jpg
   ```

2. Reference it in the post body with a **root-relative** path (no domain):

   ```markdown
   ![a sunset](/content/images/2026/06/sunset.jpg)
   ```

3. `python publish.py` uploads any new images automatically, then deploys.

> 🛟 If an image ever fails to load, the theme shows a tidy
> `[ image no longer available ]` placeholder with the original URL — nothing ever
> renders as a broken icon.

---

## ♥ Mark a post as a favorite

Set `favorite: true` in the front matter:

```text
favorite: true
```

A neon-pink **♥** then appears next to the post everywhere it's listed (feed,
archive, tags) and on the post page itself.

---

## 🛠 Edit an existing post

1. Open the file in `posts/` (filename starts with its date).
2. Change the body or any front-matter field.
3. Rebuild + publish:

   ```bash
   .venv/bin/python publish.py
   ```

> ⚠️ **Renaming the `slug`** changes the post's URL (old link will 404). Keep the
> slug stable unless you mean to move it. Renaming the *file* (not the slug) is
> harmless — the slug field controls the URL, not the filename.

---

## 📄 Create or edit a page

Pages live in `pages/` and sit at the top level (`/slug/`) instead of in the feed.
They support an optional nav link and one level of nesting.

### Page template

```text
---
title: whoami
slug: girl
format: html
nav: whoami
nav_order: 1
parent: ''
---
<p>Write the page body here. <code>format: html</code> means raw HTML;
use <code>format: markdown</code> to write Markdown instead.</p>
```

### Common recipes

| Goal | Front matter |
|---|---|
| Page **in the top nav** | `nav: <label>` and a `nav_order` (lower = further left) |
| Page **not in the nav** | `nav: ''` |
| **Nested** under another page (e.g. `/girl/concerts/`) | `parent: girl` and `slug: concerts` → URL becomes `/<parent>/<slug>/` |
| Write the body in Markdown | `format: markdown` |

> 🔗 To link from one page to a nested page, use its full path, e.g.
> `<a href="/girl/concerts/">concerts</a>`.

After editing a page: `python publish.py`.

---

## 👀 Preview locally

No internet or AWS needed — this just builds and serves the `site/` folder:

```bash
.venv/bin/python build.py
.venv/bin/python -m http.server -d site 8765
# visit http://localhost:8765/
```

Re-run `build.py` after each change and refresh the browser. (Stop the server with
`Ctrl-C`.)

---

## 🚀 Publish to short-stack.net

```bash
.venv/bin/python publish.py
```

This does four things, in order:

1. **Uploads new images** — if a local `content/images/` exists, syncs it to the
   images bucket.
2. **Builds** the site into `site/`.
3. **Deploys** — `aws s3 sync site/ → ssnet-blog-site` (with `--delete`, so removed
   pages disappear).
4. **Invalidates CloudFront** so changes show up immediately.

Runs from **any machine on your Tailscale network** that has the repo, the Python
deps, and the `ssnet` AWS profile configured.

---

## 📋 Field reference

### Post front matter (`posts/*.txt`)

| Field | Required | Example | Notes |
|---|---|---|---|
| `title` | ✅ | `Hello Again` | Shown lowercased by the theme; stored as-is. |
| `date` | ✅ | `'2026-06-22T14:30:00+00:00'` | ISO 8601, UTC. Controls feed order. |
| `slug` | ✅ | `hello-again` | URL = `/<slug>/`. Lowercase, hyphens, no spaces. |
| `tags` | – | `[life, update]` | List. Becomes `/tag/<tag>/` pages. Empty = `[]`. |
| `feature_image` | – | `'/content/images/2026/06/x.jpg'` | Optional banner image. Empty = `''`. |
| `format` | – | `markdown` | `markdown` (default) or `html`. |
| `favorite` | – | `false` | `true` shows the ♥. |

### Page front matter (`pages/*.txt`)

| Field | Required | Example | Notes |
|---|---|---|---|
| `title` | ✅ | `whoami` | Page heading. |
| `slug` | ✅ | `girl` | URL segment. |
| `format` | – | `html` | `html` (default for pages) or `markdown`. |
| `nav` | – | `whoami` | Nav label. Empty `''` = not in nav. |
| `nav_order` | – | `1` | Sort order in nav (lower = first). |
| `parent` | – | `girl` | Nest under another page. Empty `''` = top level. |

---

## ⚠️ Gotchas & rules

- **Run from the repo root.** `build.py`/`publish.py` use paths relative to
  `config.toml`.
- **Slugs must be unique** and can't be one of the reserved names:
  `archive`, `tag`, `page`, `search`, `content`, or an existing page slug
  (`girl`, `concerts`, `contact`). The build will **stop with an error** if a post
  slug collides — rename the slug.
- **Quote the date** (and any value with special characters) in single quotes,
  exactly as shown.
- **Markdown allows raw HTML** inline — handy for the odd `<center>` or `<table>`.
- **Don't hand-edit `site/`** — it's regenerated every build (and git-ignored).
- **Deleting a post:** remove its `.txt` and run `publish.py`; the `--delete` sync
  removes it from the live site.

---

Happy writing. 🩷
