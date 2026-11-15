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
        "Christos Visvardis | Marketing Science & Measurement Expert",
        "Marketing scientist (ex-Facebook / Meta, TikTok) specialising in marketing mix modeling, "
        "incrementality testing, attribution and causal inference. Author of Practical Marketing Science.",
    ),
    "about.html": (
        "About Christos Visvardis | Marketing Science & Measurement",
        "Christos Visvardis: 15+ years in marketing science and analytics at Facebook / Meta, TikTok, "
        "Cheapflights and MindGeek, and as an independent marketing scientist.",
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
    "google-meridian-mmm-tutorial": ("2026-11-15", "2026-11-15"),
    "meridian-geox-geo-experiment-tutorial": ("2026-11-15", "2026-11-15"),
    "ab-tests-that-hold-up": ("2026-11-15", "2026-11-15"),
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
    "google-meridian-mmm-tutorial": (
        "Google Meridian MMM Tutorial: Build a Marketing Mix Model in Python",
        "Step-by-step Google Meridian tutorial: load geo-level data, set ROI priors, fit the Bayesian MMM, "
        "check convergence and fit, read ROI and response curves, and optimise the budget.",
    ),
    "meridian-geox-geo-experiment-tutorial": (
        "Meridian GeoX Tutorial: How to Run a Geo Experiment in Python",
        "How to design and analyse a geo experiment with Google's Meridian GeoX: pick treatment regions, "
        "check the MDE and budget, measure lift and iCPD, and calibrate Meridian with the result.",
    ),
    "ab-tests-that-hold-up": (
        "A/B Tests That Hold Up: Seven Rules for Trustworthy Experiments",
        "How to design, run and read A/B tests you can trust: a written plan, power and the MDE, "
        "no peeking, multiple comparisons, CUPED and the checks that catch broken tests.",
    ),
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
    "google-meridian-mmm-tutorial": [
        ("bayesmmm", "Bayesian MMM in practice"), ("validation", "Validating and calibrating MMM"),
        ("curves", "Response curves and budget optimization")],
    "meridian-geox-geo-experiment-tutorial": [
        ("geo", "Geo experiments"), ("validation", "Validating and calibrating MMM")],
    "ab-tests-that-hold-up": [
        ("abtests", "A/B tests that hold up"), ("geo", "Geo experiments")],
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
    "jobTitle": "Marketing Science & Measurement Expert",
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


# Images that lived on the old WordPress server (now gone). Each is replaced by a file in
# assets/blog/: two recovered from the Internet Archive, the code outputs regenerated by
# running the post's own code, and three drawn as illustrations.
# old upload path -> (new file, alt text, caption)
IMAGE_MAP = {
    "2023/12/image-1024x602.png": ("pymc-marketing-components.png",
        "PyMC-Marketing posterior predictive model components: channel, control, seasonality and intercept contributions over time",
        "An example channel contribution plot"),
    "2023/12/image-1-1024x602.png": ("pymc-marketing-posterior-predictive.png",
        "PyMC-Marketing posterior predictive check: observed sales against the model's predictions with credible intervals",
        "Compare the model against the actual data."),
    "2023/11/image-1.png": ("lightweightmmm-media-posteriors.png",
        "LightweightMMM posterior distributions of the media effect for each channel",
        "Posterior distributions of the media effects"),
    "2023/11/image-2.png": ("lightweightmmm-model-fit.png",
        "LightweightMMM model fit: true and predicted KPI on the training data",
        "Our model's fit to the training data"),
    "2023/11/image-3.png": ("lightweightmmm-out-of-sample.png",
        "LightweightMMM out-of-sample predictions against the held-out KPI",
        "Model predictions on unseen data"),
    "2023/11/image-4-1024x370.png": ("lightweightmmm-baseline-contribution.png",
        "LightweightMMM stacked area chart of baseline and channel contributions over time",
        "Estimated media &amp; baseline contribution over time"),
    "2023/11/image-5.png": ("lightweightmmm-media-contribution.png",
        "LightweightMMM media contribution percentage by channel with credibility intervals",
        "Estimated media contributions with their respective credibility intervals"),
    "2023/11/image-6.png": ("lightweightmmm-budget-optimisation.png",
        "LightweightMMM budget allocation before and after optimisation, and the predicted KPI for each",
        "Pre/post optimization budget allocation comparison for each channel and pre/post optimization predicted target variable comparison"),
    "2023/11/image-7-916x1024.png": ("robyn-one-pager.png",
        "Meta Robyn model one-pager: response decomposition, actual vs predicted, ROI, adstock, response curves and residuals",
        "A Meta Robyn one-pager example"),
    "2023/11/image-8-1024x731.png": ("causal-impact-plot.png",
        "CausalImpact plot with original, pointwise and cumulative panels around the intervention",
        "An example Causal Impact plot"),
    "2023/11/image-13.png": ("geolift-pretest-geoplot.png",
        "GeoPlot of the pre-test data: daily outcome for each location",
        "Pre-test data: the daily outcome for every location"),
    "2023/11/image-10.png": ("geolift-test-geoplot.png",
        "GeoPlot of the test data with the campaign start at day 91 marked",
        "Test data for every location, with the campaign start (day 91) marked"),
    "2023/11/image-11.png": ("geolift-lift.png",
        "GeoLift lift plot: test markets against their synthetic control, with the treatment period shaded",
        "The test markets (Chicago and Portland) against their synthetic control"),
    "2023/11/image-12.png": ("geolift-att.png",
        "GeoLift average treatment effect on the treated (ATT) per day, with the treatment period shaded",
        "Average effect per day in the test markets (ATT)"),
    "2021/07/image-1024x481.png": ("shapley-attribution-outline.png",
        "Illustration of Shapley value attribution: example conversion paths and each channel's share of credit",
        "An outline of the Shapley Value Model for Data Driven Attribution. Each color represents a different channel in the conversion path. (Illustrative numbers, not NA-KD data.)"),
    "2023/01/Facebook-Conversion-Lift-1024x505.png": ("conversion-lift-test.png",
        "Diagram of a conversion lift test: the audience is randomly split into a test group that sees ads and a control group that doesn't",
        "How a conversion lift test works (illustrative numbers)"),
    "2021/07/lead-ad-1-527x1024.gif": ("lead-ad-form-mobile.png",
        "Illustration of a lead ad on mobile: the ad in the feed and the pre-filled form that opens in the app",
        "Illustration of a lead ad on a mobile device: the form opens in the app with the person's details pre-filled"),
}
FIGURE = re.compile(r'<figure[^>]*>(?:(?!</figure>).)*?</figure>', re.S)
OLD_UPLOAD = re.compile(r'https?://(?:www\.)?visvardis\.com/wp-content/uploads/([^"\s]+)')

# Small fixes to code blocks that came out wrong in the WordPress import.
CODE_FIXES = {
    "crafting-a-robust-marketing-mix-model-with-pymc-marketing": [
        ("<code><code>X = data.drop('sales', axis=1) y = data&#91;'sales'] mmm.fit(X, y)</code></code>",
         "<code>X = data.drop('sales', axis=1)\ny = data&#91;'sales']\nmmm.fit(X, y)</code>"),
        ("<code><code>my_model_config = {**default_model_config, **custom_beta_channel_prior}</code></code>",
         "<code>my_model_config = {**default_model_config, **custom_beta_channel_prior}</code>"),
    ],
    "creating-a-marketing-mix-model-with-lightweightmmm-a-step-by-step-guide": [
        ("fig_size=(30,10)", "fig_size=(16,6)"),
        ("<code>n_time_periods = 10\n", "<code>prices = jnp.ones(mmm.n_media_channels)  # cost per unit of media, 1 if media is spend\nn_time_periods = 10\n"),
        ("<code>plot.plot_pre_post_budget_allocation_comparison(",
         "<code>optimal_buget_allocation = prices * solution.x\nprevious_budget_allocation = prices * previous_media_allocation\n\nplot.plot_pre_post_budget_allocation_comparison("),
    ],
}


def fix_blog_media(path: Path) -> None:
    s = path.read_text(encoding="utf-8")

    def figure(m: re.Match) -> str:
        u = OLD_UPLOAD.search(m.group(0))
        if not u or u.group(1) not in IMAGE_MAP:
            return m.group(0)
        name, alt, cap = IMAGE_MAP[u.group(1)]
        return ('<figure class="wp-block-image size-large">'
                f'<img src="../assets/blog/{name}" alt="{esc(alt)}" loading="lazy"/>'
                f'<figcaption class="wp-element-caption">{cap}</figcaption></figure>')

    s = FIGURE.sub(figure, s)
    for old, new in CODE_FIXES.get(path.stem, []):
        if old in s and new not in s:
            s = s.replace(old, new)
    path.write_text(s, encoding="utf-8")


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


# Topic tag shown on each article card (blog page and home page).
CARD_TAGS = {
    "google-meridian-mmm-tutorial": "MMM",
    "meridian-geox-geo-experiment-tutorial": "Experiments",
    "ab-tests-that-hold-up": "Experiments",
    "crafting-a-robust-marketing-mix-model-with-pymc-marketing": "MMM",
    "creating-a-marketing-mix-model-with-lightweightmmm-a-step-by-step-guide": "MMM",
    "creating-a-marketing-mix-model-with-meta-robyn-a-step-by-step-guide": "MMM",
    "unleashing-the-power-of-causal-impact-in-marketing-analytics": "Causal inference",
    "unveiling-the-power-of-meta-geolift-a-guide-to-geolift-experiments-in-marketing": "Experiments",
    "how-to-create-your-own-attribution-model": "Attribution",
    "how-i-helped-na-kd-create-a-custom-attribution-model-facebook-case-study": "Case study",
    "how-i-helped-unisport-increase-their-sales-with-segmentation-analysis": "Case study",
    "how-to-use-facebook-lead-ads-to-generate-quality-low-cost-leads-a-zopto-case-study": "Case study",
}
ARTICLE_CARD = re.compile(r'<article class="blog-card">.*?</article>', re.S)


def tag_cards(path: Path) -> None:
    """Put one topic tag at the top of each article card (replacing any old one)."""
    def repl(m: re.Match) -> str:
        card = re.sub(r'\s*<span class="card-tag">[^<]*</span>', "", m.group(0))
        slug = re.search(r'href="blog/([^"]+)\.html"', card)
        tag = CARD_TAGS.get(slug.group(1)) if slug else None
        if not tag:
            return card
        span = f'\n                        <span class="card-tag">{esc(tag)}</span>'
        date = re.search(r'<p class="card-date">[^<]*</p>', card)
        at = date.end() if date else len('<article class="blog-card">')
        return card[:at] + span + card[at:]
    s = path.read_text(encoding="utf-8")
    path.write_text(ARTICLE_CARD.sub(repl, s), encoding="utf-8")


# The same footer on every page (outside the book), with links to the main pages.
def footer_html(prefix: str) -> str:
    links = [("about.html", "About"), ("portfolio.html", "Portfolio"), ("blog.html", "Blog"),
             (f"{BOOK_DIR}/index.html", "Book")]
    inner = "".join(f'<a href="{prefix}{href}">{label}</a>' for href, label in links)
    inner += ('<a href="https://www.linkedin.com/in/cvis/" target="_blank" rel="noopener">LinkedIn</a>'
              '<a href="https://github.com/christosvis" target="_blank" rel="noopener">GitHub</a>')
    return ("<footer>\n            <div class=\"footer-grid\">\n"
            f"                <p>&copy; {date.today().year} Christos Visvardis</p>\n"
            f'                <nav class="footer-links" aria-label="Footer">{inner}</nav>\n'
            "            </div>\n        </footer>")


# Set the colour theme before the page is drawn, so dark-mode visitors get no white flash.
THEME_BLOCK = re.compile(r"\s*<!-- theme:start -->.*?<!-- theme:end -->", re.S)
THEME_SNIPPET = (
    "\n<!-- theme:start -->\n<script>(function(){try{var t=localStorage.getItem('theme');"
    "if(!t){t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light'}"
    "document.documentElement.setAttribute('data-theme',t)}catch(e){}})();</script>\n<!-- theme:end -->"
)


def site_pages() -> list[Path]:
    return [p for p in sorted(ROOT.rglob("*.html"))
            if ".git" not in p.parts and BOOK_DIR not in p.parts]


def add_theme_and_footer() -> int:
    n = 0
    for path in site_pages():
        s = THEME_BLOCK.sub("", path.read_text(encoding="utf-8"))
        i = s.find("<head>")
        if i < 0:
            continue
        i += len("<head>")
        s = s[:i] + THEME_SNIPPET + s[i:]
        prefix = "../" * (len(path.relative_to(ROOT).parts) - 1)
        if path.name == "404.html":
            prefix = "/"
        s = re.sub(r"<footer>.*?</footer>", lambda m: footer_html(prefix), s, count=1, flags=re.S)
        path.write_text(s, encoding="utf-8")
        n += 1
    return n


def main() -> None:
    sitemap: list[tuple[str, str]] = []
    update_cards(ROOT / "blog.html")
    update_cards(ROOT / "index.html")
    tag_cards(ROOT / "blog.html")
    tag_cards(ROOT / "index.html")

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
        fix_blog_media(path)
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
    add_theme_and_footer()  # runs after analytics so the theme script is the first thing in <head>
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
