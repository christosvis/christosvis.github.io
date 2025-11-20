import xml.etree.ElementTree as ET

tree = ET.parse('christosvisvardis.WordPress.2025-11-20.xml')
root = tree.getroot()

namespaces = {
    'wp': 'http://wordpress.org/export/1.2/',
    'content': 'http://purl.org/rss/1.0/modules/content/'
}

post_types = set()
for item in root.findall('.//item'):
    post_type = item.find('wp:post_type', namespaces).text
    post_types.add(post_type)

print("Post types found:", post_types)
