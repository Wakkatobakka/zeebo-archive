"""Check generated pages, citations, inventory preservation and local navigation."""
from collections import Counter
from html import unescape
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote
import csv
import hashlib
import json
import re
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]

def check(ok, message):
    if not ok:
        raise AssertionError(message)

class Page(HTMLParser):
    def __init__(self, path):
        super().__init__(convert_charrefs=True)
        self.ids, self.links, self.h1 = set(), [], 0
        self.feed(path.read_text())
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if 'id' in attrs:
            check(attrs['id'] not in self.ids, 'Duplicate ID: ' + attrs['id'])
            self.ids.add(attrs['id'])
        self.h1 += tag == 'h1'
        for key in ('href', 'src'):
            if attrs.get(key):
                self.links.append(attrs[key])
        if tag == 'img':
            check('alt' in attrs, 'Image missing alt text')

catalog = json.loads((ROOT / 'data/catalog.json').read_text())
research = json.loads((ROOT / 'data/research.json').read_text())
protected = json.loads((ROOT / 'data/protected-files.json').read_text())
for name, digest in protected.items():
    check(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == digest, 'Original file changed: ' + name)
entries, games, sources = catalog['entries'], research['games'], research['sources']
check(len(entries) == 81 and len(games) == 81, 'Record count')
check(set(games) == {e['id'] for e in entries}, 'Research IDs')
check(Counter(e['kind'] for e in entries)['Game'] == 56, 'Game count')
check(sum(e['kind'] == 'Application' for e in entries) == 5, 'Application count')
check(sum(len(e['packages']) for e in entries) == 88, 'Source-file count')
quote_words = Counter()
media_count = 0
for gid, g in games.items():
    check(g['overview'] and g['deck'], 'Missing introduction: ' + gid)
    refs = []
    for section in ('overview', 'development', 'release', 'notes'):
        refs += [sid for p in g[section] for sid in p['sources']]
    for q in g['quotes']:
        check(q['speaker'] and q['attribution'], 'Unattributed quotation: ' + gid)
        quote_words[sources[q['source']]['url']] += len(q['text'].split())
        refs.append(q['source'])
    for c in g['credits'] + g['studio_roles']:
        check(c['name'] and c['scope'] and c['role'], 'Unscoped credit: ' + gid)
        refs.append(c['source'])
    for m in g.get('media', []):
        media_count += 1
        check((ROOT / m['path']).is_file(), 'Missing media: ' + m['path'])
        check(m['alt'] and m['caption'] and m['credit'], 'Missing media attribution')
        check(m['platform'] == 'Zeebo' and m['platform_evidence'], 'Unverified image platform')
        refs.append(m['source'])
    refs.append('inventory-' + gid)
    check(all(s in sources for s in refs), 'Missing citation: ' + gid)
for p in research['platform']:
    check(all(s in sources for s in p['sources']), 'Platform citation')
    for q in p.get('quotes', []):
        quote_words[sources[q['source']]['url']] += len(q['text'].split())
check(all(n <= 25 for n in quote_words.values()), 'Quoted source exceeds 25 words: ' + repr(quote_words))
check(media_count == 8, 'Image count')
html_files = sorted(ROOT.rglob('*.html'))
check(len(html_files) == 87, 'HTML page count')
pages = {p.resolve(): Page(p) for p in html_files}
base = catalog['site_url']
local_links = 0
for path, page in pages.items():
    check(page.h1 == 1, 'Expected one H1: ' + str(path))
    for link in page.links:
        if link.startswith(base):
            link = '/' + link[len(base):]
        url = urlsplit(link)
        if url.scheme or url.netloc:
            continue
        target = (ROOT / unquote(url.path).lstrip('/')) if url.path.startswith('/') else path.parent / unquote(url.path) if url.path else path
        if target.is_dir():
            target /= 'index.html'
        target = target.resolve()
        check(target.is_relative_to(ROOT), 'Escaping local link: ' + link)
        check(target.is_file(), 'Broken local link: ' + str(path.relative_to(ROOT)) + ' → ' + link)
        if url.fragment and target in pages:
            check(unquote(url.fragment) in pages[target].ids, 'Broken anchor: ' + link)
        local_links += 1
for e in entries:
    path = ROOT / ('games' if e['id'].isdigit() else 'resources') / e['slug'] / 'index.html'
    text = unescape(path.read_text())
    for p in e['packages']:
        check(p['filename'] in text and p['sha256'] in text and p['source_sha1'] in text, 'Missing package evidence: ' + e['id'])
        for member in p['contents']:
            if not member['dir']:
                check(member['path'] in text and member['sha256'] in text, 'Missing member evidence: ' + e['id'])
sitemap = ET.parse(ROOT / 'sitemap.xml').getroot()
check(len(sitemap) == 86, 'Sitemap count')
for item in sitemap:
    url = item[0].text
    check(url.startswith(base), 'Sitemap base')
    check((ROOT / url[len(base):] / 'index.html').is_file(), 'Sitemap path: ' + url)
with (ROOT / 'data/credits.csv').open(newline='') as f:
    check(len(list(csv.DictReader(f))) == sum(len(g['credits']) for g in games.values()), 'CSV credit parity')
check(not any(p.suffix.lower() in ('.7z', '.rar', '.mod', '.mif', '.exe', '.apk') for p in ROOT.rglob('*') if '.git' not in p.parts), 'Unexpected executable or game payload')
print(f'PASS: 81 records, 88 source files, {len(html_files)} pages, {local_links:,} local links/anchors, {len(sources)} references, {media_count} images; original inventory and palette unchanged.')
