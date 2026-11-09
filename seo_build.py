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
    "how-to-create-your-own-attribution-model": ("2021-07-08", "2026-11-09"),
    "how-i-helped-na-kd-create-a-custom-attribution-model-facebook-case-study": ("2021-07-09", "2023-01-23"),
    "how-i-helped-unisport-increase-their-sales-with-segmentation-analysis": ("2021-07-09", "2021-07-09"),
    "how-to-use-facebook-lead-ads-to-generate-quality-low-cost-leads-a-zopto-case-study": ("2021-07-09", "2021-07-09"),
    "creating-a-marketing-mix-model-with-lightweightmmm-a-step-by-step-guide": ("2023-11-12", "2023-11-12"),
    "creating-a-marketing-mix-model-with-meta-robyn-a-step-by-step-guide": ("2023-11-12", "2023-11-12"),
    "unleashing-the-power-of-causal-impact-in-marketing-analytics": ("2023-11-13", "2023-11-13"),
    "unveiling-the-power-of-meta-geolift-a-guide-to-geolift-experiments-in-marketing": ("2023-11-13", "2026-11-09"),
    "crafting-a-robust-marketing-mix-model-with-pymc-marketing": ("2023-12-17", "2023-12-17"),
}

# Search titles and descriptions for blog posts, written for the queries each post
# gets impressions for in Search Console. The on-page heading is left unchanged.
POST_META = {
    "unveiling-the-power-of-meta-geolift-a-guide-to-geolift-experiments-in-marketing": (
        "Meta GeoLift Guide: How to Run a Geo Lift Test in R",
        "Step-by-step guide to Meta GeoLift: set test goals, prepare market data, run a power "
        "analysis, launch the geo lift test in R and read the incremental lift.",
    ),
    "how-to-create-your-own-attribution-model": (
        "How to Create a Custom Attribution Model (Shapley & Markov)",
        "Build a custom attribution model from your own data: collect touchpoints, set an "
        "attribution window, apply Shapley value and Markov chain models, then validate with lift tests.",
    ),
    "crafting-a-robust-marketing-mix-model-with-pymc-marketing": (
        "PyMC-Marketing MMM Tutorial: Build a Bayesian Marketing Mix Model",
        "Step-by-step PyMC-Marketing tutorial: prepare data, set custom priors, fit a Bayesian "
        "marketing mix model with adstock and saturation, and check the results.",
    ),
    "creating-a-marketing-mix-model-with-lightweightmmm-a-step-by-step-guide": (
        "Google LightweightMMM Tutorial: Build a Marketing Mix Model in Python",
        "Build a marketing mix model with Google's LightweightMMM in Python: prepare and scale "
        "data, train the model, read media contributions and optimise the budget.",
    ),
    "creating-a-marketing-mix-model-with-meta-robyn-a-step-by-step-guide": (
        "Meta Robyn MMM Tutorial: Build a Marketing Mix Model in R",
        "Step-by-step guide to building a marketing mix model with Meta's Robyn in R, from data "
        "preparation and hyperparameters to model selection and budget allocation.",
    ),
    "unleashing-the-power-of-causal-impact-in-marketing-analytics": (
        "CausalImpact for Marketing: Measure Campaign Impact in R",
        "How to use Google's CausalImpact R package to measure the incremental effect of a "
        "marketing campaign or launch when you cannot run a randomised test.",
    ),
}

# "Go deeper" links from each post to the matching book chapter.
BOOK_LINKS = {
    "unveiling-the-power-of-meta-geolift-a-guide-to-geolift-experiments-in-marketing": [
        ("geo", "Geo experiments"), ("lift", "Reading platform lift studies")],
    "how-to-create-your-own-attribution-model": [
        ("attribution", "Attribution and its limits"), ("triangulation", "Triangulation: deciding under contradictory evidence")],
    "how-i-helped-na-kd-create-a-custom-attribution-model-facebook-case-study": [
        ("attribution", "Attribution and its limits"), ("lift", "Reading platform lift studies")],
    "crafting-a-robust-marketing-mix-model-with-pymc-marketing": [
        ("bayesmmm", "Bayesian MMM in practice"), ("validation", "Validating and calibrating MMM")],
    "creating-a-marketing-mix-model-with-lightweightmmm-a-step-by-step-guide": [
        ("mmm", "Marketing mix modeling end to end"), ("curves", "Response curves and budget optimization")],
    "creating-a-marketing-mix-model-with-meta-robyn-a-step-by-step-guide": [
        ("mmm", "Marketing mix modeling end to end"), ("validation", "Validating and calibrating MMM")],
    "unleashing-the-power-of-causal-impact-in-marketing-analytics": [
        ("quasi", "Quasi-experiments: DiD, CausalImpact and synthetic control")],
    "how-i-helped-unisport-increase-their-sales-with-segmentation-analysis": [
        ("segmentation", "Segmentation")],
    "how-to-use-facebook-lead-ads-to-generate-quality-low-cost-leads-a-zopto-case-study": [
        ("social", "Paid social and creative fatigue")],
}

RELATED_BLOCK = re.compile(r"\s*<!-- book-links:start -->.*?<!-- book-links:end -->", re.S)


def add_book_links(path: Path) -> None:
    s = RELATED_BLOCK.sub("", path.read_text(encoding="utf-8"))
    links = BOOK_LINKS.get(path.stem)
    if links:
        items = "".join(
            f'<li><a href="../{BOOK_DIR}/{ch}.html">{esc(label)}</a></li>' for ch, label in links
        )
        box = (
            "\n<!-- book-links:start -->\n"
            '<aside class="book-links" style="margin-top:2.5rem;padding:1.25rem 1.5rem;'
            'border:2px solid var(--border-color);border-radius:8px;">'
            f'<p style="margin:0 0 .5rem;font-weight:700;">Go deeper in my free book, '
            f'<a href="../{BOOK_DIR}/index.html">{BOOK_TITLE}</a></p>'
            f'<ul style="margin:0;padding-left:1.2rem;">{items}</ul></aside>\n'
            "<!-- book-links:end -->"
        )
        marker = '<a href="../blog.html" class="back-link"'
        i = s.find(marker)
        if i < 0:
            raise ValueError(f"{path}: no back-link to anchor book links")
        line_start = s.rfind("\n", 0, i)
        s = s[:line_start] + box + s[line_start:]
    path.write_text(s, encoding="utf-8")


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


CARD = re.compile(r'(<article class="blog-card">\s*<h3>)(.*?)(</h3>\s*<p>)(.*?)(</p>\s*<a href="blog/([^"]+)\.html")', re.S)


def update_cards(path: Path) -> None:
    """Use the new post titles and descriptions on the blog and home page cards."""
    def repl(m: re.Match) -> str:
        meta = POST_META.get(m.group(6))
        if not meta:
            return m.group(0)
        return m.group(1) + esc(meta[0]) + m.group(3) + esc(meta[1]) + m.group(5)
    s = path.read_text(encoding="utf-8")
    path.write_text(CARD.sub(repl, s), encoding="utf-8")


def main() -> None:
    sitemap: list[tuple[str, str]] = []
    update_cards(ROOT / "blog.html")
    update_cards(ROOT / "index.html")

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
        add_book_links(path)
        slug = path.stem
        new_title, new_desc = POST_META.get(slug, (None, None))
        s = path.read_text(encoding="utf-8")
        if new_title:  # keep the visible heading in line with the search title
            s = re.sub(r"(<h1[^>]*>).*?(</h1>)", lambda m: m.group(1) + esc(new_title) + m.group(2), s, count=1, flags=re.S)
            path.write_text(s, encoding="utf-8")
        h1 = re.search(r"<h1[^>]*>(.*?)</h1>", s, re.S)
        headline = text_of(h1.group(1)) if h1 else text_of(TITLE.search(s).group(1))
        desc = new_desc or clip(existing_description(s) or text_of(s.split("<body", 1)[-1]))
        if not new_title:
            new_title = f"{headline} - {SITE_NAME}"
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
        apply(path, new_title, desc, "article", ld)
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
    tagged = add_analytics()
    print(f"Updated {len(sitemap)} pages and sitemap.xml; GA4 tag on {tagged} pages")


# Google Analytics 4. Every HTML page gets this block straight after <head>.
GA4_ID = "G-0VCH9LPNYB"
GA_BLOCK = re.compile(r"\s*<!-- ga4:start -->.*?<!-- ga4:end -->", re.S)


def add_analytics() -> int:
    tag = (
        "\n<!-- ga4:start -->\n"
        f'<script async src="https://www.googletagmanager.com/gtag/js?id={GA4_ID}"></script>\n'
        "<script>\n"
        "  window.dataLayer = window.dataLayer || [];\n"
        "  function gtag(){dataLayer.push(arguments);}\n"
        "  gtag('js', new Date());\n"
        f"  gtag('config', '{GA4_ID}');\n"
        "</script>\n"
        "<!-- ga4:end -->"
    )
    count = 0
    for path in sorted(ROOT.rglob("*.html")):
        if ".git" in path.parts:
            continue
        s = GA_BLOCK.sub("", path.read_text(encoding="utf-8"))
        i = s.find("<head>")
        if i < 0:
            continue
        i += len("<head>")
        path.write_text(s[:i] + tag + s[i:], encoding="utf-8")
        count += 1
    return count


if __name__ == "__main__":
    main()
