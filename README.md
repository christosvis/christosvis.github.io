# christosvis.github.io


## SEO

After changing pages, regenerating the blog or re-copying the book, run:

    python3 seo_build.py

It rewrites the SEO block (description, canonical, social tags, structured data)
in every page and regenerates `sitemap.xml`. `_redirects` sends old WordPress
URLs to the new blog pages and `404.html` makes unknown URLs return a real 404.
