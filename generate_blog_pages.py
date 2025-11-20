import xml.etree.ElementTree as ET
import os
from datetime import datetime
import html

# Configuration
XML_FILE = 'christosvisvardis.WordPress.2025-11-20.xml'
BLOG_DIR = 'blog'
BLOG_INDEX_FILE = 'blog.html'

# Namespaces
NAMESPACES = {
    'wp': 'http://wordpress.org/export/1.2/',
    'content': 'http://purl.org/rss/1.0/modules/content/',
    'excerpt': 'http://wordpress.org/export/1.2/excerpt/',
    'dc': 'http://purl.org/dc/elements/1.1/'
}

def parse_date(date_str):
    # Example: Thu, 20 Nov 2025 13:03:35 +0000
    # Or from wp:post_date: 2021-07-05 18:20:25
    try:
        return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S').strftime('%B %d, %Y')
    except ValueError:
        try:
             return datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %z').strftime('%B %d, %Y')
        except ValueError:
            return date_str

def create_blog_post_html(post):
    template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Christos Visvardis</title>
    <meta name="description" content="{excerpt}">
    <link rel="stylesheet" href="../style.css">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700;800&display=swap" rel="stylesheet">
</head>
<body>
    <div class="container">
        <header>
            <a href="../index.html" class="logo">Christos Visvardis</a>
            <nav>
                <ul>
                    <li><a href="../portfolio.html">Portfolio</a></li>
                    <li><a href="../blog.html" class="active">Blog</a></li>
                    <li>
                        <a href="https://www.linkedin.com/in/cvis/" target="_blank" aria-label="LinkedIn">
                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
                                fill="currentColor">
                                <path
                                    d="M19 0h-14c-2.761 0-5 2.239-5 5v14c0 2.761 2.239 5 5 5h14c2.762 0 5-2.239 5-5v-14c0-2.761-2.238-5-5-5zm-11 19h-3v-11h3v11zm-1.5-12.268c-.966 0-1.75-.79-1.75-1.764s.784-1.764 1.75-1.764 1.75.79 1.75 1.764-.783 1.764-1.75 1.764zm13.5 12.268h-3v-5.604c0-3.368-4-3.113-4 0v5.604h-3v-11h3v1.765c1.396-2.586 7-2.777 7 2.476v6.759z" />
                            </svg>
                        </a>
                    </li>
                    <li>
                        <a href="https://github.com/christosvis" target="_blank" aria-label="GitHub">
                            <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"
                                fill="currentColor">
                                <path
                                    d="M12 0c-6.626 0-12 5.373-12 12 0 5.302 3.438 9.8 8.207 11.387.599.111.793-.261.793-.577v-2.234c-3.338.726-4.033-1.416-4.033-1.416-.546-1.387-1.333-1.756-1.333-1.756-1.089-.745.083-.729.083-.729 1.205.084 1.839 1.237 1.839 1.237 1.07 1.834 2.807 1.304 3.492.997.107-.775.418-1.305.762-1.604-2.665-.305-5.467-1.334-5.467-5.931 0-1.311.469-2.381 1.236-3.221-.124-.303-.535-1.524.117-3.176 0 0 1.008-.322 3.301 1.23.957-.266 1.983-.399 3.003-.404 1.02.005 2.047.138 3.006.404 2.291-1.552 3.297-1.23 3.297-1.23.653 1.653.242 2.874.118 3.176.77.84 1.235 1.911 1.235 3.221 0 4.609-2.807 5.624-5.479 5.921.43.372.823 1.102.823 2.222v3.293c0 .319.192.694.801.576 4.765-1.589 8.199-6.086 8.199-11.386 0-6.627-5.373-12-12-12z" />
                            </svg>
                        </a>
                    </li>
                    <li>
                        <button id="theme-toggle" class="theme-toggle" aria-label="Toggle Dark Mode">
                            <svg class="sun-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" style="display:none;">
                                <path d="M12 18a6 6 0 1 1 0-12 6 6 0 0 1 0 12zm0-2a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM11 1h2v3h-2V1zm0 19h2v3h-2v-3zM3.515 4.929l1.414-1.414L7.05 5.636 5.636 7.05 3.515 4.93zM16.95 18.364l1.414-1.414 2.121 2.121-1.414 1.414-2.121-2.121zm2.121-14.85l1.414 1.415-2.121 2.121-1.414-1.414 2.121-2.121zM5.636 16.95l1.414 1.414-2.121 2.121-1.414-1.414 2.121-2.121zM23 11v2h-3v-2h3zM4 11v2H1v-2h3z" />
                            </svg>
                            <svg class="moon-icon" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                                <path d="M12.3 22h-.1a10.313 10.313 0 0 1-10.2-10.2a10.288 10.288 0 0 1 10.2-10.2c.2 0 .4 0 .6.1a9.843 9.843 0 0 0-8.5 12.2a9.867 9.867 0 0 0 8.6 8c-.2.1-.4.1-.6.1z" />
                            </svg>
                        </button>
                    </li>
                </ul>
            </nav>
        </header>

        <main>
            <article class="blog-post">
                <h1>{title}</h1>
                <div class="post-meta">{date}</div>
                <div class="post-content">
                    {content}
                </div>
                <a href="../blog.html" class="back-link">&larr; Back to Blog</a>
            </article>
        </main>

        <footer>
            <p>&copy; 2025 Christos Visvardis. All rights reserved.</p>
        </footer>
    </div>

    <script src="../script.js"></script>
</body>
</html>"""
    
    return template.format(
        title=post['title'],
        excerpt=post['excerpt'],
        date=post['date'],
        content=post['content']
    )

def main():
    tree = ET.parse(XML_FILE)
    root = tree.getroot()
    
    posts = []
    
    for item in root.findall('.//item'):
        post_type = item.find('wp:post_type', NAMESPACES).text
        status = item.find('wp:status', NAMESPACES).text
        
        if post_type == 'post' and status == 'publish':
            title = item.find('title').text
            if not title:
                continue
                
            content = item.find('content:encoded', NAMESPACES).text or ''
            excerpt = item.find('excerpt:encoded', NAMESPACES).text or ''
            post_date = item.find('wp:post_date', NAMESPACES).text
            slug = item.find('wp:post_name', NAMESPACES).text
            
            if not slug:
                # Fallback slug generation
                slug = title.lower().replace(' ', '-').replace(':', '').replace('/', '')
            
            # Clean up content
            import re
            # Remove WordPress block comments
            content = re.sub(r'<!-- /?wp:.*? -->', '', content)
            # Remove empty class attributes
            content = re.sub(r' class=""', '', content)
            # Remove multiple newlines
            content = re.sub(r'\n\s*\n', '\n', content)
            
            # Create excerpt if empty
            if not excerpt:
                # Strip HTML tags for excerpt
                clean_text = re.sub('<[^<]+?>', '', content)
                excerpt = clean_text[:150] + '...' if len(clean_text) > 150 else clean_text
            
            formatted_date = parse_date(post_date)
            
            post_data = {
                'title': title,
                'content': content.strip(),
                'excerpt': excerpt.replace('"', '&quot;'),
                'date': formatted_date,
                'slug': slug,
                'link': f'blog/{slug}.html'
            }
            
            posts.append(post_data)
            
            # Write individual blog page
            html_content = create_blog_post_html(post_data)
            file_path = os.path.join(BLOG_DIR, f"{slug}.html")
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_content)
            print(f"Created {file_path}")

    # Update blog.html
    # Sort posts by date (descending) - assuming input order is roughly chronological or we can parse dates
    # For now, let's just reverse them if they are in chronological order in XML, or keep as is.
    # XML usually has oldest first or newest first? Let's assume we want to keep the order found or sort.
    # Let's sort by date just in case.
    posts.sort(key=lambda x: datetime.strptime(x['date'], '%B %d, %Y'), reverse=True)

    blog_grid_html = ""
    for post in posts:
        blog_grid_html += f"""
                    <article class="blog-card">
                        <h3>{post['title']}</h3>
                        <p>{post['excerpt']}</p>
                        <a href="{post['link']}" class="read-more">Read Article &rarr;</a>
                    </article>"""

    # Read existing blog.html
    with open(BLOG_INDEX_FILE, 'r', encoding='utf-8') as f:
        blog_html_content = f.read()

    # Replace the blog grid content
    # We look for <div class="blog-grid"> and the closing </div>
    import re
    pattern = re.compile(r'(<div class="blog-grid">)(.*?)(</div>)', re.DOTALL)
    
    if pattern.search(blog_html_content):
        new_blog_html_content = pattern.sub(r'\1' + blog_grid_html + r'\n\3', blog_html_content)
        
        with open(BLOG_INDEX_FILE, 'w', encoding='utf-8') as f:
            f.write(new_blog_html_content)
        print(f"Updated {BLOG_INDEX_FILE}")
    else:
        print("Could not find blog-grid div in blog.html")

if __name__ == "__main__":
    main()
