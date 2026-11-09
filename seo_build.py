#!/usr/bin/env python3
"""Add SEO tags to every page and regenerate sitemap.xml.

Run from the repo root after changing pages, regenerating the blog
(generate_blog_pages.py) or re-copying the book:

    python3 seo_build.py

It is safe to run repeatedly: each page gets one block between
<!-- seo:start --> and <!-- seo:end --> that is replaced on every run.
"""
from __future__ import annotations

import html
import json
import re
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent
BASE = "https://visvardis.com"
SITE_NAME = "Christos Visvardis"
AUTHOR = "Christos Visvardis"
TODAY = date.today().isoformat()
BOOK_DIR = "practical-marketing-science-book"
BOOK_TITLE = "Practical Marketing Science"
SAME_AS = ["https://www.linkedin.com/in/cvis/", "https://github.com/christosvis"]

# Hand-written titles and descriptions for the main pages.
PAGES = {
    "index.html": (
        "Christos Visvardis | Marketing Science & Measurement Consultant",
        "Marketing science consultant (ex-Meta, TikTok) specialising in marketing mix "
        "modeling, attribution, incrementality testing and causal inference.",
    ),
    "blog.html": (
        "Blog: Marketing Mix Modeling, Attribution & Causal Inference | Christos Visvardis",
        "Articles and case studies on marketing mix modeling, attribution, geo experiments, "
        "Causal Impact and marketing measurement by Christos Visvardis.",
    ),
    "portfolio.html": (
        "Portfolio: Marketing Science Projects & Tools | Christos Visvardis",
        "Marketing science projects: MMM with Robyn, Meridian and PyMC, GeoLift tests, "
        "budget optimisers, attribution models, forecasting and LTV apps.",
    ),
}

# Original publish / last-modified dates of the blog posts (from the WordPress export).
POST_DATES = {
    "how-to-create-your-own-attribution-model": ("2021-07-08", "2024-12-17"),
    "how-i-helped-na-kd-create-a-custom-attribution-model-facebook-case-study": ("2021-07-09", "2023-01-23"),
    "how-i-helped-unisport-increase-their-sales-with-segmentation-analysis": ("2021-07-09", "2021-07-09"),
    "how-to-use-facebook-lead-ads-to-generate-quality-low-cost-leads-a-zopto-case-study": ("2021-07-09", "2021-07-09"),
    "creating-a-marketing-mix-model-with-lightweightmmm-a-step-by-step-guide": ("2023-11-12", "2023-11-12"),
    "creating-a-marketing-mix-model-with-meta-robyn-a-step-by-step-guide": ("2023-11-12", "2023-11-12"),
    "unleashing-the-power-of-causal-impact-in-marketing-analytics": ("2023-11-13", "2023-11-13"),
    "unveiling-the-power-of-meta-geolift-a-guide-to-geolift-experiments-in-marketing": ("2023-11-13", "2024-09-04"),
    "crafting-a-robust-marketing-mix-model-with-pymc-marketing": ("2023-12-17", "2023-12-17"),
}

SEO_BLOCK = re.compile(r"\s*<!-- seo:start -->.*?<!-- seo:end -->", re.S)
OLD_TAGS = re.compile(
    r'\s*<meta\s+(?:name|property)="(?:description|og:[^"]+|twitter:[^"]+)"\s+content="[^"]*"\s*/?>',
    re.S,
)
OLD_CANONICAL = re.compile(r'\s*<link\s+rel="canonical"[^>]*>')
TITLE = re.compile(r"<title>(.*?)</title>", re.S)


def text_of(fragment: str) -> str:
    fragment = re.sub(r"<(script|style)\b.*?</\1>", " ", fragment, flags=re.S)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    return re.sub(r"\s+", " ", html.unescape(fragment)).strip()


def clip(text: str, limit: int = 158) -> str:
    text = re.sub(r"(\.\.\.|…)$", "", text.strip()).strip()
    if len(text) <= limit:
        return text
    window = text[:limit]
    end = max(window.rfind(". "), window.rfind("? "), window.rfind("! "))
    if end >= 90:  # end on a full sentence when one fits
        return window[: end + 1]
    cut = text[: limit - 1].rsplit(" ", 1)[0].rstrip(",;:-–—. ")
    return cut + "…"


def url_for(rel: str) -> str:
    if rel == "index.html":
        return BASE + "/"
    if rel == f"{BOOK_DIR}/index.html":
        return f"{BASE}/{BOOK_DIR}/"
    return f"{BASE}/{rel[:-5]}"  # Cloudflare Pages serves pages without ".html"


def esc(value: str) -> str:
    return html.escape(value, quote=True)


def block(title: str, desc: str, url: str, og_type: str, ld: list[dict] | None = None) -> str:
    lines = [
        "<!-- seo:start -->",
        f'<meta name="description" content="{esc(desc)}">',
        f'<link rel="canonical" href="{url}">',
        f'<meta property="og:site_name" content="{SITE_NAME}">',
        f'<meta property="og:type" content="{og_type}">',
        f'<meta property="og:title" content="{esc(title)}">',
        f'<meta property="og:description" content="{esc(desc)}">',
        f'<meta property="og:url" content="{url}">',
        '<meta name="twitter:card" content="summary">',
        f'<meta name="twitter:title" content="{esc(title)}">',
        f'<meta name="twitter:description" content="{esc(desc)}">',
    ]
    for item in ld or []:
        data = json.dumps(item, ensure_ascii=False, indent=None).replace("</", "<\\/")
        lines.append(f'<script type="application/ld+json">{data}</script>')
    lines.append("<!-- seo:end -->")
    return "\n" + "\n".join(lines)


PERSON = {
    "@type": "Person",
    "@id": f"{BASE}/#person",
    "name": AUTHOR,
    "url": BASE + "/",
    "jobTitle": "Marketing Science, Measurement and Analytics Expert",
    "knowsAbout": [
        "Marketing Mix Modeling",
        "Marketing Attribution",
        "Incrementality Testing",
        "Causal Inference",
        "Geo Experiments",
    ],
    "sameAs": SAME_AS,
}


def apply(path: Path, title: str | None, desc: str, og_type: str, ld=None) -> str:
    s = path.read_text(encoding="utf-8")
    s = SEO_BLOCK.sub("", s)
    head, sep, rest = s.partition("</head>")
    head = OLD_TAGS.sub("", head)
    head = OLD_CANONICAL.sub("", head)
    m = TITLE.search(head)
    if not m:
        raise ValueError(f"{path}: no <title>")
    if title:
        head = head[: m.start()] + f"<title>{esc(title)}</title>" + head[m.end():]
        m = TITLE.search(head)
    final_title = text_of(m.group(1))
    url = url_for(path.relative_to(ROOT).as_posix())
    head = head[: m.end()] + block(final_title, desc, url, og_type, ld) + head[m.end():]
    path.write_text(head + sep + rest, encoding="utf-8")
    return url


def existing_description(s: str) -> str:
    m = re.search(r'<meta\s+name="description"\s+content="([^"]*)"', s, re.S)
    return text_of(m.group(1)) if m else ""


def book_description(s: str) -> str:
    body = s.split('<section class="normal" id="section-">', 1)[-1]
    m = re.search(r'<div class="decision">(.*?)</div>', body, re.S)
    if m and text_of(m.group(1)):
        return text_of(m.group(1))
    for p in re.findall(r"<p>(.*?)</p>", body, re.S):
        t = text_of(p)
        if len(t) > 60:
            return t
    return ""


def main() -> None:
    sitemap: list[tuple[str, str]] = []

    # Main pages
    for rel, (title, desc) in PAGES.items():
        ld = None
        if rel == "index.html":
            ld = [{
                "@context": "https://schema.org",
                "@graph": [
                    PERSON,
                    {"@type": "WebSite", "@id": f"{BASE}/#website", "url": BASE + "/",
                     "name": SITE_NAME, "publisher": {"@id": f"{BASE}/#person"}},
                ],
            }]
        sitemap.append((apply(ROOT / rel, title, desc, "website", ld), TODAY))

    # Blog posts
    for path in sorted((ROOT / "blog").glob("*.html")):
        s = path.read_text(encoding="utf-8")
        slug = path.stem
        desc = clip(existing_description(s) or text_of(s.split("<body", 1)[-1]))
        title = text_of(TITLE.search(s).group(1))
        headline = re.sub(r"\s+-\s+Christos Visvardis$", "", title)
        published, modified = POST_DATES.get(slug, (TODAY, TODAY))
        url = url_for(f"blog/{slug}.html")
        ld = [{
            "@context": "https://schema.org",
            "@type": "BlogPosting",
            "headline": headline[:110],
            "description": desc,
            "datePublished": published,
            "dateModified": modified,
            "url": url,
            "mainEntityOfPage": url,
            "author": {"@type": "Person", "name": AUTHOR, "url": BASE + "/"},
        }]
        apply(path, None, desc, "article", ld)
        sitemap.append((url, modified))

    # Book chapters
    book = ROOT / BOOK_DIR
    for path in sorted(book.glob("*.html")):
        if path.name == "404.html":
            continue
        s = path.read_text(encoding="utf-8")
        ld = None
        if path.name == "index.html":
            desc = clip(
                "Practical Marketing Science: a free online field guide to measuring what "
                "marketing actually does, from A/B and geo tests to MMM, attribution, LTV and pricing."
            )
            ld = [{
                "@context": "https://schema.org",
                "@type": "Book",
                "name": BOOK_TITLE,
                "alternativeHeadline": "A field guide to measuring what marketing actually does",
                "author": {"@type": "Person", "name": AUTHOR, "url": BASE + "/"},
                "url": f"{BASE}/{BOOK_DIR}/",
                "inLanguage": "en",
                "isAccessibleForFree": True,
                "bookFormat": "https://schema.org/EBook",
            }]
        else:
            desc = clip(book_description(s) or existing_description(s))
        url = apply(path, None, desc, "book" if path.name == "index.html" else "article", ld)
        sitemap.append((url, TODAY))

    xml = ['<?xml version="1.0" encoding="UTF-8"?>',
           '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, lastmod in sitemap:
        xml.append(f"  <url><loc>{loc}</loc><lastmod>{lastmod}</lastmod></url>")
    xml.append("</urlset>")
    (ROOT / "sitemap.xml").write_text("\n".join(xml) + "\n", encoding="utf-8")
    print(f"Updated {len(sitemap)} pages and sitemap.xml")


if __name__ == "__main__":
    main()
