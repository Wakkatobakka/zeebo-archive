"""History-led Zeebo pages, preserving the original file inventory."""
from collections import defaultdict, Counter
from pathlib import Path
import csv
import html
import json
import re
import unicodedata
import xml.etree.ElementTree as ET
from inventory import package_panel


def render(root):
    data = json.loads((root / 'data/catalog.json').read_text())
    research = json.loads((root / 'data/research.json').read_text())
    entries = sorted(data['entries'], key=lambda e: e['title'].casefold())
    byid = {e['id']: e for e in entries}
    games, sources = research['games'], research['sources']
    base, repo = data['site_url'], 'https://github.com/' + data['repository']
    h = lambda x: html.escape(str(x), quote=True)
    def slug(x):
        return re.sub('[^a-z0-9]+', '-', unicodedata.normalize('NFKD', x).encode('ascii', 'ignore').decode().lower()).strip('-')
    def route(e, prefix=''):
        return prefix + ('games/' if e['id'].isdigit() else 'resources/') + e['slug'] + '/index.html'
    def person(name, prefix=''):
        return prefix + 'creators/index.html#person-' + slug(name)
    def studio(name, prefix=''):
        return prefix + 'creators/index.html#studio-' + slug(name)
    people, studios = defaultdict(list), defaultdict(list)
    for e in entries:
        for c in games[e['id']]['credits']:
            people[c['name']].append((e, c))
        for s in games[e['id']]['studio_roles']:
            studios[s['name']].append((e, s))

    def save(path, title, description, body, prefix='', active='', scripts=()):
        canonical = base + str(path).replace('index.html', '')
        head = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="dark"><meta name="theme-color" content="#0a1016"><title>{h(title)} | Zeebo Archive</title><meta name="description" content="{h(description)}"><link rel="canonical" href="{h(canonical)}"><meta property="og:type" content="website"><meta property="og:title" content="{h(title)} | Zeebo Archive"><meta property="og:description" content="{h(description)}"><meta property="og:url" content="{h(canonical)}"><meta property="og:image" content="{base}assets/social-preview.png"><meta name="twitter:card" content="summary_large_image"><link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="{prefix}assets/styles.css"><link rel="stylesheet" href="{prefix}assets/history.css"></head><body><div class="ambient" aria-hidden="true"></div><a class="skip-link" href="#main">Skip to content</a>'''
        nav = f'<header class="site-header"><div class="shell nav-shell"><a class="brand" href="{prefix}index.html" aria-label="Zeebo Archive home"><span class="brand-mark" aria-hidden="true"><span></span><span></span><span></span><span></span></span><span>ZEEBO <span class="brand-slash">/</span> ARCHIVE</span></a><nav class="top-nav" aria-label="Main navigation">'
        for key, label, url in [('catalog', 'Catalog', 'index.html#catalog'), ('history', 'Platform history', 'history/index.html'), ('creators', 'Creators', 'creators/index.html'), ('sources', 'Sources', 'sources/index.html')]:
            nav += f'<a href="{prefix}{url}"' + (' aria-current="page"' if active == key else '') + f'>{label}</a>'
        nav += '</nav></div></header>'
        foot = f'<footer class="site-footer"><div class="shell"><div class="foot"><div><a class="brand" href="{prefix}index.html">ZEEBO / ARCHIVE</a><p class="footer-vision">A true archive of the game and its history, not just a file.</p><p class="preservation-credit">Original preservation: OpenZeebo and the Internet Archive community. Printed guide: Zeebo Brasil S.A.</p></div><div class="foot-links"><a href="{prefix}about/index.html">Methods &amp; credits</a><a href="{repo}">GitHub ↗</a><a href="https://wakkatobakka.github.io/">Wakka’s Workshop ↗</a></div></div><nav class="archive-family" aria-label="Other game archives"><span>Other archives</span>'
        for name, folder in [('BREW', 'qualcomm-brew-archive'), ('DoJa', 'doja-archive'), ('ExEn', 'exen-game-archive'), ('J2ME', 'j2me-archive'), ('N-Gage', 'ngage-archive')]:
            foot += f'<a href="https://wakkatobakka.github.io/{folder}/">{name} ↗</a>'
        foot += '</nav></div></footer>'
        script = ''.join(f'<script src="{prefix}assets/{name}" defer></script>' for name in scripts)
        p = root / path
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(head + nav + '<main id="main">' + body + '</main>' + foot + script + '</body></html>\n')

    def used(gid):
        g = games[gid]
        refs = ['inventory-' + gid]
        refs += [sid for key in ('overview', 'development', 'release', 'notes') for p in g[key] for sid in p['sources']]
        refs += [q['source'] for q in g['quotes']]
        refs += [c['source'] for c in g['credits']]
        refs += [s['source'] for s in g['studio_roles']]
        refs += [m['source'] for m in g.get('media', [])]
        return list(dict.fromkeys(refs))
    def cites(ids, refs):
        return '<span class="citations">' + ''.join(f'<a href="#source-{h(s)}" aria-label="Source {refs.index(s) + 1}">[{refs.index(s) + 1}]</a>' for s in dict.fromkeys(ids)) + '</span>' if ids else ''
    def paragraphs(items, refs):
        return '<div class="entry-prose">' + ''.join(f'<p>{h(p["text"])}{cites(p["sources"], refs)}</p>' for p in items) + '</div>' if items else ''
    def quotations(items, refs, section):
        result = ''
        for q in items:
            if q['section'] != section:
                continue
            translation = '<span class="translation-credit">' + h(q['translation']) + '</span>' if q.get('translation') else ''
            result += f'<figure class="source-quote"><blockquote><p>“{h(q["text"])}”</p></blockquote><figcaption>{h(q["speaker"])} · {h(q["attribution"])}{translation}{cites([q["source"]], refs)}</figcaption></figure>'
        return result
    def media(items, refs, prefix='../../'):
        result = ''
        for m in items:
            url = prefix + m['path']
            wide = ' wide-media' if m['kind'] in ('production', 'guide', 'advertisement') else ''
            result += f'<figure class="archive-figure{wide}"><div class="artifact" data-kind="{h(m["kind"])}"><a class="image-open" href="{h(url)}" data-image="{h(url)}" data-caption="{h(m["caption"])}" aria-label="Enlarge: {h(m["caption"])}"><img src="{h(url)}" alt="{h(m["alt"])}" width="{m["width"]}" height="{m["height"]}" loading="lazy"></a></div><figcaption>{h(m["caption"])}{cites([m["source"]], refs)}<span class="image-credit">{h(m["credit"])}</span></figcaption><a class="enlarge" href="{h(url)}" data-image="{h(url)}" data-caption="{h(m["caption"])}">Enlarge image <span aria-hidden="true">+</span></a></figure>'
        return result
    def narrative(items, quotes, refs, section):
        selected = [q for q in quotes if q['section'] == section]
        if len(selected) == 1 and any(p.get('after_quote') for p in items):
            before = [p for p in items if not p.get('after_quote')]
            after = [p for p in items if p.get('after_quote')]
            return paragraphs(before, refs) + quotations(selected, refs, section) + paragraphs(after, refs)
        anchored = defaultdict(list)
        for quote in selected:
            matches = [i for i, item in enumerate(items) if quote['source'] in item['sources']]
            anchored[matches[-1] if matches else len(items) - 1].append(quote)
        content, pending = '', []
        for i, item in enumerate(items):
            pending.append(item)
            if i in anchored:
                content += paragraphs(pending, refs) + quotations(anchored[i], refs, section)
                pending = []
        return content + paragraphs(pending, refs) + (quotations(selected, refs, section) if not items else '')
    def bibliography(refs):
        result = '<section class="entry-section bibliography" id="sources"><h2>Sources</h2><ol>'
        for sid in refs:
            s = sources[sid]
            published = h(s['published']) + ' · ' if s.get('published') else ''
            result += f'<li id="source-{h(sid)}"><a href="{h(s["url"])}" target="_blank" rel="noopener noreferrer">{h(s["title"])} ↗</a><small>{published}{h(s["kind"])}</small>'
            if s.get('note'):
                result += f'<p>{h(s["note"])}</p>'
            result += '</li>'
        return result + '</ol></section>'
    def viewer():
        return '<dialog id="image-viewer" aria-labelledby="viewer-title"><div class="viewer-toolbar"><strong id="viewer-title">Archive image</strong><div><button id="viewer-zoom" type="button" aria-pressed="false">Zoom in</button><button id="viewer-close" type="button">Close</button></div></div><div id="viewer-canvas" class="viewer-canvas"><img id="viewer-image" alt=""></div><p class="viewer-help">Zoom in to examine the image. Swipe or scroll to move around it.</p></dialog>'
    def category(e):
        return e['kind'] if e['kind'] in ('Game', 'Application', 'Documentation') else 'Development'
    def card(e):
        g = games[e['id']]
        search = [e['title'], e['id'], *e.get('aliases', []), g['deck']]
        search += [c['name'] + ' ' + c['role'] + ' ' + c['team'] for c in g['credits']]
        search += [s['name'] for s in g['studio_roles']]
        for p in e['packages']:
            search += [p['filename'], p['sha256'], *p['source_paths']]
            search += [m['path'] + ' ' + m.get('sha256', '') for m in p['contents'] if not m['dir']]
        year = f'{g["year"]} · ' if g.get('year') else ''
        return f'<a class="entry-card" href="{route(e)}" data-search="{h(" ".join(search))}" data-type="{category(e)}" data-subsets="{" ".join(e["subsets"])}" data-has-guide="{"yes" if e.get("guide_scan") else "no"}"><div><span class="entry-sub">{year}{h(e["kind"])}</span><h3 class="entry-title">{h(e["title"])}</h3><p class="entry-description">{h(g["deck"])}</p></div><span class="card-bottom"><small>ID {h(e["id"])} · {len(e["packages"])} {"package" if len(e["packages"]) == 1 else "variants"}</small><span aria-hidden="true">↗</span></span></a>'

    features = [('276675', 'Resident Evil 4’s Zeebo adaptation and its development credits.'), ('277727', 'The team and tools behind the Zeebo Extreme racing series.'), ('277380', 'Fishlabs describes bringing Galaxy on Fire to Zeebo.')]
    featurecards = ''
    for gid, deck in features:
        e, g = byid[gid], games[gid]
        art = ''
        featurecards += f'<a class="feature-card" href="{route(e)}">{art}<div><h3>{h(e["title"])}</h3><p>{h(deck)}</p><span class="text-link">Read the entry ↗</span></div></a>'
    chips = ''.join(f'<button class="chip{" active" if k == "Game" else ""}" type="button" data-type="{k}" aria-pressed="{"true" if k == "Game" else "false"}">{label}</button>' for k, label in [('Game', 'Games'), ('Application', 'Apps'), ('Development', 'Tools & samples'), ('Documentation', 'Documents'), ('All', 'All records')])
    options = ''.join(f'<option value="{k}">{h(v)}</option>' for k, v in data['subsets'].items())
    counts = Counter(e['kind'] for e in entries)
    home = f'''<section class="hero shell archive-home"><div class="hero-copy"><div class="eyebrow"><span class="pulse"></span>WAKKA’S GAME ARCHIVES</div><h1>Games made for<br><em>Zeebo.</em></h1><p class="hero-lede">Explore the games, their creators and the console they worked with, alongside original coverage and preserved file records.</p><div class="hero-actions"><a class="btn btn-primary" href="#catalog">Browse the catalog ↓</a><a class="btn btn-secondary" href="history/index.html">About Zeebo ↗</a></div><p class="small-flag">A true archive of the game and its history, not just a file.</p></div><div class="hero-art console-art"><span class="art-orbit orbit-one" aria-hidden="true"></span><span class="art-orbit orbit-two" aria-hidden="true"></span><img src="assets/zeebo-console.svg" width="540" height="460" alt="Stylized illustration of the white Zeebo console and controller"></div></section><section class="count-strip" aria-label="Archive contents"><div class="shell stats-grid"><div><strong>{counts['Game']}</strong><span>games</span></div><div><strong>{counts['Application']}</strong><span>system applications</span></div><div><strong>{len(entries) - counts['Game'] - counts['Application']}</strong><span>tools &amp; reference records</span></div><div><strong>{data['counts']['source_files']}</strong><span>preserved source files</span></div></div></section><section class="shell featured-section"><div class="section-heading"><h2>Start with a game</h2></div><div class="feature-grid">{featurecards}</div></section><section class="shell explore-paths"><a href="history/index.html"><h2>Platform history</h2><p>Tectoy, Qualcomm, the development environment and the download service.</p><span class="text-link">Read about Zeebo ↗</span></a><a href="creators/index.html"><h2>Creators</h2><p>People and studios behind original games and Zeebo adaptations, with their roles and sources.</p><span class="text-link">Browse people and studios ↗</span></a></section><section class="catalog-wrap" id="catalog"><div class="shell"><div class="section-heading"><div><h2>Catalog</h2><p>Search by game, creator, studio, ID, filename or checksum.</p></div></div><div class="catalog-controls"><label class="search-field"><span class="sr-only">Search the archive</span><input id="search" type="search" autocomplete="off" placeholder="Try a game, creator, ID or filename…"><kbd>/</kbd></label><div class="filter-group" role="group" aria-label="Record type">{chips}</div><div class="collection-picker"><label for="collection">Source subset</label><select id="collection"><option value="All">All subsets</option>{options}</select></div></div><div class="evidence-filter"><label><input id="guide-only" type="checkbox">Described in the printed guide</label><a class="text-link" href="data/catalog.csv" download>Catalog CSV ↓</a></div><div class="results-line"><span id="results-count" role="status" aria-live="polite">Showing 81 of 81 records</span></div><div class="entry-grid">{''.join(card(e) for e in entries)}</div><div class="empty-results" id="no-results" hidden><h3>No matching records</h3><p>Try another name or clear the filters.</p></div><div class="catalog-bottom"><button class="btn btn-secondary" type="button" id="clear-search">Reset filters</button><noscript><p>All 81 records are available above. Search and filters require JavaScript.</p></noscript></div><details class="catalog-data"><summary>Catalog scope and data downloads</summary><p>The original collection contains 61 game/app IDs in 68 title packages, plus 20 reference records. Package variants remain grouped. The original inventory, filenames and fingerprints are retained.</p><div class="buttons"><a class="btn btn-secondary" href="data/catalog.json" download>Original inventory JSON ↓</a><a class="btn btn-secondary" href="data/packages.csv" download>Package CSV ↓</a><a class="btn btn-secondary" href="data/contents.csv" download>Member inventory CSV ↓</a><a class="btn btn-secondary" href="data/research.json" download>Histories &amp; credits JSON ↓</a></div><a class="text-link" href="about/index.html">Methods and credits ↗</a></details></div></section>'''
    save('index.html', 'Zeebo games and their history', 'Zeebo games, creators, development accounts, archival images and preserved file records.', home, active='catalog', scripts=('site.js',))

    for index, e in enumerate(entries):
        gid, g = e['id'], games[e['id']]
        refs, sections, toc = used(gid), [], []
        def add(sid, title, content):
            if content:
                toc.append((sid, title))
                sections.append(f'<section class="entry-section" id="{sid}"><h2>{title}</h2>{content}</section>')
        primary = [m for m in g.get('media', []) if m.get('placement') == 'game']
        production = [m for m in g.get('media', []) if m.get('placement') == 'development']
        gallery = [m for m in g.get('media', []) if m.get('placement', 'gallery') == 'gallery']
        title = 'The game' if e['kind'] == 'Game' else 'The application' if e['kind'] == 'Application' else 'The material'
        add('the-game', title, paragraphs(g['overview'], refs) + media(primary, refs))
        add('development', 'Development', narrative(g['development'], g['quotes'], refs, 'development') + media(production, refs))
        grouped = defaultdict(list)
        for c in g['credits']:
            grouped[c['name']].append(c)
        def people_rows(names):
            rows = '<div class="people-list">'
            for name in names:
                work = grouped[name]
                roles = ' · '.join(dict.fromkeys(c['role'] + (f' ({c["scope"]})' if c['scope'] != 'Zeebo' else '') for c in work))
                teams = ' · '.join(dict.fromkeys(c['team'] for c in work if c.get('team')))
                rows += f'<div class="person-row"><h3><a href="{person(name, "../../")}">{h(name)}</a></h3><div><p>{h(roles)}{cites([c["source"] for c in work], refs)}</p><small>{h(teams)}</small></div></div>'
            return rows + '</div>'
        creative = [n for n, cs in grouped.items() if any(re.search('program|design|art|graphic|music|code|concept|gameplay|animation', c['role'], re.I) for c in cs)]
        other = [n for n in grouped if n not in creative]
        if len(grouped) <= 8:
            creative, other = list(grouped), []
        peoplebody = people_rows(creative) if creative else ''
        if other:
            peoplebody += f'<details class="more-credits"><summary>More credits ({len(other)})</summary>{people_rows(other)}</details>'
        if g['studio_roles']:
            rows = ''.join(f'<li><a href="{studio(s["name"], "../../")}">{h(s["name"])}</a><span>{h(s["role"])}{(" · " + h(s["scope"])) if s["scope"] != "Zeebo" else ""}{cites([s["source"]], refs)}</span></li>' for s in g['studio_roles'])
            peoplebody += f'<div class="studio-block"><h3>Studios and production</h3><ul class="studio-roles">{rows}</ul></div>'
        add('creators', 'People', peoplebody)
        add('reception', 'Release and reception', narrative(g['release'], g['quotes'], refs, 'reception'))
        add('gallery', 'Gallery', '<div class="archive-gallery">' + media(gallery, refs) + '</div>' if gallery else '')
        packages = ''.join(package_panel(p, i) for i, p in enumerate(e['packages'], 1))
        count = len(e['packages'])
        files = f'<details class="file-variants"><summary>{count} preserved {"package" if count == 1 else "variants"} · IDs, checksums and file contents</summary>{packages}</details><p class="file-note">These file checks identify preserved packages. They do not record a gameplay test.</p>'
        add('files', 'Files and versions', files)
        toc.append(('sources', 'Sources'))
        sections.append(bibliography(refs))
        original_notes = e.get('notes', [])
        if g['notes'] or original_notes:
            original = '<div class="entry-prose">' + ''.join(f'<p>{h(note)}</p>' for note in original_notes) + '</div>' if original_notes else ''
            sections.append('<details class="record-notes"><summary>Edition and research notes</summary>' + paragraphs(g['notes'], refs) + original + '</details>')
        links = []
        if e.get('guide_scan'):
            links.append(f'<a href="{h(e["guide_source_url"])}" target="_blank" rel="noopener noreferrer">Printed game guide · spread {h(e["guide_scan"])} ↗</a>')
        if e.get('title_source_url'):
            links.append(f'<a href="{h(e["title_source_url"])}" target="_blank" rel="noopener noreferrer">OpenZeebo ID list · 23 October 2011 ↗</a>')
        if links:
            sections.append('<details class="record-notes"><summary>Original catalog references</summary><div class="original-references">' + ''.join('<p>' + link + '</p>' for link in links) + '</div></details>')
        related = []
        for othergame in entries:
            shared = set(grouped) & {c['name'] for c in games[othergame['id']]['credits']}
            if othergame['id'] != gid and shared:
                related.append((len(shared), othergame, sorted(shared)))
        related.sort(key=lambda x: (-x[0], x[1]['title']))
        if related:
            links = ''.join(f'<li><a href="{route(o, "../../")}">{h(o["title"])}</a><small>{h(", ".join(ns[:2]))}{" and others" if len(ns) > 2 else ""}</small></li>' for _, o, ns in related[:3])
            sections.append(f'<aside class="entry-related" aria-label="Games with shared contributors"><h2>Also in this archive</h2><p>Games with contributors in common.</p><ul>{links}</ul></aside>')
        adjacent = [x for x in entries if x['kind'] == e['kind']]
        ix = adjacent.index(e)
        prev, following = adjacent[(ix - 1) % len(adjacent)], adjacent[(ix + 1) % len(adjacent)]
        if len(adjacent) > 1:
            sections.append(f'<nav class="detail-links" aria-label="Adjacent records"><a href="{route(prev, "../../")}">← {h(prev["title"])}</a><a href="{route(following, "../../")}">{h(following["title"])} →</a></nav>')
        year = f'<span class="chip">{g["year"]}</span>' if g.get('year') else ''
        quick = [(s['role'], s['name']) for s in g['studio_roles'] if s['scope'] == 'Zeebo'][:3]
        quick_markup = '<dl class="quick-facts">' + ''.join(f'<div><dt>{h(k)}</dt><dd>{h(v)}</dd></div>' for k, v in quick) + '</dl>' if quick else ''
        jumps = ''.join(f'<a href="#{sid}">{label}</a>' for sid, label in toc)
        overview_sources = list(dict.fromkeys(s for p in g['overview'][:1] for s in p['sources']))
        badge = 'Zeebo' if gid.isdigit() else e['kind']
        body = f'<header class="shell detail-hero"><nav class="breadcrumbs" aria-label="Breadcrumb"><a href="../../index.html">Zeebo Archive</a><span aria-hidden="true">/</span><a href="../../index.html#catalog">Catalog</a><span aria-hidden="true">/</span><span aria-current="page">{h(e["title"])}</span></nav><div class="chips">{year}<span class="chip mint">{h(badge)}</span><a class="chip file-shortcut" href="#files">Files and versions ↓</a></div><h1>{h(e["title"])}</h1><p class="detail-deck">{h(g["deck"])}{cites(overview_sources, refs)}</p>{quick_markup}</header><div class="shell entry-layout"><nav class="entry-contents" aria-label="In this entry"><h2>In this entry</h2><div>{jumps}</div></nav><article class="game-entry">{"".join(sections)}</article></div>{viewer()}'
        save(route(e), e['title'], g['deck'], body, prefix='../../', scripts=('site.js', 'entry.js'))

    platform = research['platform']
    refs = list(dict.fromkeys([s for p in platform for s in p['sources']] + [q['source'] for p in platform for q in p.get('quotes', [])] + [m['source'] for p in platform for m in p.get('media', [])]))
    body = '<article class="narrow article platform-history"><div class="eyebrow">ZEEBO / PLATFORM HISTORY</div><h1>Making games for Zeebo</h1><p class="lede">The console, its development environment, and the games made for it.</p>'
    for p in platform:
        body += f'<section class="entry-section"><h2>{h(p["heading"])}</h2>' + paragraphs([p], refs) + quotations(p.get('quotes', []), refs, 'development') + media(p.get('media', []), refs, '../') + '</section>'
    body += '<nav class="reading-routes" aria-label="Game development accounts">' + ''.join(f'<a href="{route(byid[gid], "../")}">{h(byid[gid]["title"])} ↗</a>' for gid, _ in features) + '</nav>'
    body += '<nav class="reading-routes" aria-label="Development reference records">' + ''.join(f'<a href="{route(e, "../")}">{h(e["title"])}</a>' for e in entries if e['kind'] in ('Development', 'BREW sample')) + '</nav>' + bibliography(refs) + '</article>' + viewer()
    save('history/index.html', 'Platform history', 'Zeebo, its creators, the BREW development environment and digital distribution.', body, prefix='../', active='history', scripts=('entry.js',))

    creatorcards = ''
    for name, work in sorted(people.items(), key=lambda x: slug(x[0])):
        roles = ' · '.join(dict.fromkeys(c['role'] for _, c in work))
        count = len({e['id'] for e, _ in work})
        search = name + ' ' + roles + ' ' + ' '.join(e['title'] for e, _ in work)
        links = ''.join(f'<li><a href="{route(e, "../")}#creators">{h(e["title"])}</a><span>{h(c["role"])} · {h(c["scope"])} · <a href="{h(sources[c["source"]]["url"])}" target="_blank" rel="noopener noreferrer">source ↗</a></span></li>' for e, c in work)
        creatorcards += f'<article class="creator-card" id="person-{slug(name)}" data-search="{h(search)}"><span class="source-kind">{count} GAME/APP {"ENTRIES" if count != 1 else "ENTRY"}</span><h2>{h(name)}</h2><p>{h(roles)}</p><details><summary>Games and contributions</summary><ul>{links}</ul></details></article>'
    studiocards = ''
    for name, work in sorted(studios.items(), key=lambda x: slug(x[0])):
        search = name + ' ' + ' '.join(e['title'] for e, _ in work)
        links = ''.join(f'<li><a href="{route(e, "../")}">{h(e["title"])}</a><span>{h(s["role"])} · {h(s["scope"])} · <a href="{h(sources[s["source"]]["url"])}" target="_blank" rel="noopener noreferrer">source ↗</a></span></li>' for e, s in work)
        studiocards += f'<article class="creator-card" id="studio-{slug(name)}" data-search="{h(search)}"><span class="source-kind">STUDIO / ORGANISATION</span><h2>{h(name)}</h2><p>{len(work)} game/app relationships</p><details><summary>Games and roles</summary><ul>{links}</ul></details></article>'
    body = f'<section class="shell index-hero"><div class="eyebrow">ZEEBO / CREATORS</div><h1>People and studios</h1><p class="lede">{len(people)} named contributors, with their games, roles and edition credits.</p><div class="creator-tools" hidden><label for="creator-search">Find a person, role, game or studio</label><input type="search" id="creator-search" placeholder="Try a name, design, or programming…"><span id="creator-count" aria-live="polite"></span></div><nav class="record-jumps" aria-label="Creator index sections"><a href="#people">People ({len(people)})</a><a href="#studios">Studios ({len(studios)})</a></nav></section><section class="shell creator-section" id="people"><h2>People</h2><div class="creator-grid">{creatorcards}</div></section><section class="shell creator-section" id="studios"><h2>Studios and organisations</h2><div class="creator-grid">{studiocards}</div><p class="empty-state" id="creator-empty" hidden>No matching people or studios.</p></section>'
    save('creators/index.html', 'Creators', 'People and studios behind Zeebo games and adaptations, with edition-specific roles and sources.', body, prefix='../', active='creators', scripts=('creators.js',))

    backrefs = defaultdict(set)
    for gid in games:
        for sid in used(gid):
            backrefs[sid].add(gid)
    body = '<article class="shell article source-index"><div class="eyebrow">ZEEBO / SOURCES</div><h1>Sources</h1><p class="lede">References for game histories, personal credits, production images and the original file inventory.</p><div class="source-register">'
    for kind in sorted({s['kind'] for s in sources.values()}):
        body += f'<section><h2>{h(kind)}</h2><ul>'
        for sid, s in sources.items():
            if s['kind'] != kind:
                continue
            date = h(s['published']) + ' · ' if s.get('published') else ''
            links = ' '.join(f'<a href="{route(byid[gid], "../")}">{h(byid[gid]["title"])}</a>' for gid in sorted(backrefs[sid]))
            note = f'<p>{h(s["note"])}</p>' if s.get('note') else ''
            body += f'<li id="source-{h(sid)}"><a href="{h(s["url"])}" target="_blank" rel="noopener noreferrer">{h(s["title"])}</a><small>{date}Reviewed {h(s["reviewed"])}</small>{note}<div class="source-backrefs">{links or "Platform history"}</div></li>'
        body += '</ul></section>'
    body += '</div><div class="buttons"><a class="btn btn-secondary" href="../data/research.json" download>Histories &amp; credits JSON ↓</a><a class="btn btn-secondary" href="../data/credits.csv" download>Contributor CSV ↓</a></div></article>'
    save('sources/index.html', 'Sources', 'Sources for Zeebo game histories, interviews, creator credits, images and preserved files.', body, prefix='../', active='sources')
    body = f'''<article class="narrow article"><div class="eyebrow">ZEEBO / METHODS &amp; CREDITS</div><h1>About the archive</h1><p class="lede">A true archive of the game and its history, not just a file.</p><section class="entry-section"><h2>The collection</h2><p>The original inventory contains 56 games, five applications and 20 tools or reference records. The 61 numeric game/app IDs represent 68 title packages. Variants stay grouped under the existing record URLs.</p><p>All 88 source files, direct-member inventories, source paths and fingerprints are retained. IMICRO3D component ID 12875, bundled with Action Hero 3D, remains part of that package rather than a separate game.</p></section><section class="entry-section"><h2>Game histories</h2><p>Interviews, developer portfolios, credit records, announcements and contemporary coverage are cited alongside each entry. Direct quotations retain the original wording and identify the speaker, publication and translation where relevant.</p><p>Original arcade, console or phone teams are distinguished from Zeebo porting teams. A contributor’s edition is shown with the credit. Historical announcements describe plans at the time; entries distinguish those plans from documented releases.</p></section><section class="entry-section"><h2>Images and original documents</h2><p>Images have captions, source links and contributor or reproduction credits. Emulator captures are labelled as such. The image collection includes creator portfolios, game interfaces, promotional material and later photographs. Captions distinguish released-game images, interface artwork, emulator captures, portraits and conference photographs; they do not imply that these are early prototypes or workplace photographs.</p><p>The undated Zeebo Brasil game guide contains 14 scanned spreads. The existing guide descriptions cover 39 title IDs and retain the exact scan locators. Full-resolution scans remain linked at the original source.</p></section><section class="entry-section"><h2>File records and verification</h2><p>The original research matched all 88 source files to the sizes and SHA-1 values in the Internet Archive manifest. SHA-256 values were measured for source files and direct regular archive members. Those records are unchanged in this edition.</p><p>Internal BAR, PAK and GGZ containers were not exhaustively decoded. Content-multiset fingerprints compare file bytes and sizes while ignoring names and order.</p><p>No game or developer utility was executed for this catalog. File identification and gameplay testing remain separate.</p></section><section class="entry-section"><h2>Preservation credits</h2><p>OpenZeebo’s compilation and ID mapping are dated 23 October 2011. The Internet Archive collection was added on 1 March 2021. Original preservation credits belong to OpenZeebo and the Internet Archive community; the printed guide is credited to Zeebo Brasil S.A.</p><p>Wakka assembled this independent archive. Individual entries identify the developers, artists, interviewers, reviewers and researchers whose work is used.</p></section><section class="entry-section"><h2>Corrections and additions</h2><p><a href="{repo}/issues">Send a correction or source</a> with the title or record ID and a supporting reference. Wakka reviews changes before publication.</p></section><div class="buttons"><a class="btn btn-primary" href="../index.html#catalog">Browse the catalog</a><a class="btn btn-secondary" href="../sources/index.html">Sources</a></div></article>'''
    save('about/index.html', 'Methods and credits', 'Collection scope, source attribution, file verification and preservation credits.', body, prefix='../')
    save('404.html', 'Page not found', 'Find a record in the Zeebo archive.', f'<section class="narrow article"><h1>Page not found</h1><p class="lede">Browse the catalog to find a game or reference record.</p><a class="btn btn-primary" href="{base}">Zeebo catalog →</a></section>', prefix=base)
    with (root / 'data/credits.csv').open('w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'title', 'person', 'role', 'team', 'scope', 'source_url'])
        writer.writeheader()
        for e in entries:
            for c in games[e['id']]['credits']:
                writer.writerow(dict(id=e['id'], title=e['title'], person=c['name'], role=c['role'], team=c['team'], scope=c['scope'], source_url=sources[c['source']]['url']))
    paths = ['', 'about/', 'history/', 'creators/', 'sources/'] + [route(e).replace('index.html', '') for e in entries]
    tree = ET.Element('urlset', xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    for path in paths:
        ET.SubElement(ET.SubElement(tree, 'url'), 'loc').text = base + path
    (root / 'sitemap.xml').write_text(ET.tostring(tree, encoding='unicode'))
    print(f'Built {len(entries)} records, {len(people)} people, {len(studios)} studios, {len(sources)} references and {len(paths) + 1} HTML pages.')
