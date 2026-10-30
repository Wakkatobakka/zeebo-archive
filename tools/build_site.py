#!/usr/bin/env python3
"""Rebuild the static catalog from data/catalog.json. No game files required."""
from pathlib import Path
import csv, html, json, sys, xml.etree.ElementTree as ET

ROOT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parents[1]
D=json.loads((ROOT/'data/catalog.json').read_text())
E=D['entries']; C=D['counts']; BASE=D['site_url']; SOURCE=D['source']['url']
REPO='https://github.com/'+D['repository']
def esc(x): return html.escape(str(x),quote=True)
def fmt(n):
    return f'{n:,} B' if n<1024 else f'{n/1024:,.1f} KiB' if n<1024**2 else f'{n/1024**2:,.2f} MiB'
def route(e): return ('games/' if e['id'].isdigit() else 'resources/')+e['slug']+'/index.html'
def put(p,s):
    p=ROOT/p;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s,encoding='utf-8')
def ext(url,label,cls=''):
    return f'<a class="{cls}" href="{esc(url)}" target="_blank" rel="noopener noreferrer">{label} <span aria-hidden="true">↗</span></a>'
def head(title,description,path='',prefix=''):
    canonical=BASE+path.replace('index.html','')
    schema={'@context':'https://schema.org','@type':'CollectionPage' if not path else 'WebPage','name':title,'url':canonical,'description':description,'isPartOf':{'@type':'WebSite','name':D['title'],'url':BASE}}
    return f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="dark"><meta name="theme-color" content="#0a1016">
<title>{esc(title)}</title><meta name="description" content="{esc(description)}"><link rel="canonical" href="{esc(canonical)}">
<meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(description)}"><meta property="og:url" content="{esc(canonical)}"><meta property="og:image" content="{BASE}assets/social-preview.png"><meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{prefix}assets/favicon.svg" type="image/svg+xml"><link rel="stylesheet" href="{prefix}assets/styles.css">
<script type="application/ld+json">{json.dumps(schema,ensure_ascii=False).replace('<','&#60;')}</script></head><body><div class="ambient" aria-hidden="true"></div><a class="skip-link" href="#main">Skip to content</a>
<header class="site-header"><div class="shell nav-shell"><a class="brand" href="{prefix}index.html" aria-label="Zeebo Archive home"><span class="brand-mark" aria-hidden="true"><span></span><span></span><span></span><span></span></span><span>ZEEBO<span class="brand-slash">/</span>ARCHIVE</span></a><nav class="top-nav" aria-label="Main navigation"><a href="{prefix}index.html#catalog">The catalog</a><a href="{prefix}about/index.html">Sources &amp; story</a>{ext(SOURCE,'Original archive','source-nav')}</nav></div></header>'''
def foot(prefix=''):
    return f'''<footer class="site-footer"><div class="shell footer-grid"><div><span class="footer-brand">ZEEBO<span>/</span>ARCHIVE</span><p>A small console. A surprisingly deep archive. An independent catalog by Wakka, built from the preserved files.</p></div><div><div class="footer-cap">EXPLORE</div><a href="{prefix}index.html#catalog">Browse all {C['catalog_entries']} records</a><a href="{prefix}about/index.html">Sources, credits &amp; methodology</a><a href="{prefix}data/catalog.csv">Download catalog (CSV)</a><a href="{prefix}data/packages.csv">File fingerprints (CSV)</a><a href="{prefix}data/catalog.json">Complete metadata (JSON)</a></div><div><div class="footer-cap">THE WORKSHOP</div>{ext('https://wakkatobakka.github.io/','Wakkatobakka')}{ext('https://wakkatobakka.github.io/qualcomm-brew-archive/','The BREW catalog')}{ext(REPO,'This project on GitHub')}<p class="fineprint">Preservation credits: OpenZeebo and the Internet Archive community. Printed guide: Zeebo Brasil S.A. Original content retains its respective ownership.</p></div></div><div class="shell footer-bottom"><span>{C['title_ids']} game/app IDs · {C['title_packages']} title packages · {C['source_files']} source files</span><span>Independent community project. No affiliation with Zeebo, Tectoy or Qualcomm.</span></div></footer><script src="{prefix}assets/site.js" defer></script></body></html>'''
def card(e):
    search=' '.join([e['title'],e['id'],e['description'],*e.get('aliases',[]),*[p['filename']+' '+p['sha256']+' '+' '.join(p['source_paths'])+' '+' '.join(x['path'] for x in p['contents']) for p in e['packages']]])
    kind=e['kind'] if e['kind'] in ['Game','Application','Documentation'] else 'Development'
    tag='ID '+e['id'] if e['id'].isdigit() else e['kind']
    icon={'Game':'▣','Application':'◈','Documentation':'▤','Development':'⌘'}[kind]
    return f'''<a class="entry-card" href="{route(e)}" data-search="{esc(search)}" data-type="{kind}" data-subsets="{' '.join(e['subsets'])}" data-has-guide="{'yes' if e.get('guide_scan') else 'no'}"><span class="entry-pictogram" aria-hidden="true">{icon}</span><span class="entry-info"><span class="entry-title">{esc(e['title'])}</span><span class="entry-sub">{esc(tag)} <span class="dot-sep">·</span> {len(e['packages'])} preserved {'package' if len(e['packages'])==1 else 'variants'}</span><span class="entry-description">{esc(e['description'])}</span><span class="entry-research-tag">{esc(e['evidence'])}</span><span class="entry-chips"><span class="mini-chip">{esc(e['kind'])}</span>{''.join(f'<span class="mini-chip">{esc(D["subsets"][s])}</span>' for s in e['subsets'])}</span></span><span class="entry-arrow" aria-hidden="true">↗</span></a>'''
def homepage():
    spots=[]
    for n,(code,glyph) in enumerate([('276675','RE4'),('276153','QII'),('276121','NFS'),('274214','CNK'),('277727','BAJA'),('279382','Z')],1):
        e=next(x for x in E if x['id']==code)
        spots.append(f'<a class="spotlight-card" href="{route(e)}"><div class="spotlight-top"><span>0{n}</span><span class="corner-arrow">↗</span></div><div class="spotlight-symbol">{glyph}</div><div class="spotlight-content"><span class="minor-label">ZEEBO · ID {code}</span><h3>{esc(e["title"])}</h3><span class="spotlight-file">{len(e["packages"])} preserved {"package" if len(e["packages"])==1 else "variants"}</span></div></a>')
    chips=''.join(f'<button class="chip {"active" if k=="All" else ""}" type="button" data-type="{k}" aria-pressed="{"true" if k=="All" else "false"}">{label}</button>' for k,label in [('All','All'),('Game','Games'),('Application','Apps'),('Development','Tools & samples'),('Documentation','Documents')])
    options=''.join(f'<option value="{k}">{esc(v)}</option>' for k,v in D['subsets'].items())
    text=head('Zeebo / The Lost Catalog','Explore 61 Zeebo game and app IDs, 68 title packages, developer files and a printed guide. An independent preservation catalog.')
    text+=f'''<main id="main"><section class="hero shell"><div class="hero-copy"><div class="eyebrow"><span class="pulse"></span> AN INDEPENDENT CONSOLE PRESERVATION INDEX</div><h1>A small console.<br><em>A surprisingly deep archive.</em></h1><p class="hero-lede">Quake, Resident Evil, downhill soapbox races, and a whole world behind six-digit filenames. Explore the Zeebo collection by name, compare preserved packages, and follow the evidence back to its source.</p><div class="hero-actions"><a class="btn btn-primary" href="#catalog">Explore the catalog <span aria-hidden="true">↘</span></a>{ext(SOURCE,'Visit the original archive','btn btn-secondary')}</div></div><div class="hero-art console-art"><span class="art-orbit orbit-one" aria-hidden="true"></span><span class="art-orbit orbit-two" aria-hidden="true"></span><img src="assets/zeebo-console.svg" width="540" height="460" alt="Original stylized illustration of a white console and game controller"><div class="art-note">FROM NUMBERS <span>→</span> BACK TO NAMES</div></div></section>
<section class="count-strip" aria-label="Catalog scope"><div class="shell stats-grid"><div><strong>{C['title_ids']}</strong><span>game &amp; app IDs</span></div><div><strong>{C['title_packages']}</strong><span>preserved title packages</span></div><div><strong>{C['catalog_entries']-C['title_ids']}</strong><span>tools &amp; reference records</span></div><div><strong>{C['guide_scans']}</strong><span>printed guide spreads indexed</span></div></div></section>
<section class="shell intro-section"><div><div class="section-kicker">THE TELEVISION HAD MOBILE DNA</div><h2>A console at the edge of two eras.</h2></div><div class="intro-copy"><p>Zeebo brought a download-only, 3G-connected console to the television. The surviving collection brings together games, system applications, BREW development material and a printed game guide.</p><p>The numeric filenames are not the whole story. The <strong>2011 OpenZeebo ID list</strong> restores their names, while the supplied guide gives {C['guide_documented_titles']} titles historical context.</p><a class="text-link" href="about/index.html">How the evidence fits together ↗</a></div></section>
<section class="shell feature-section"><div class="section-heading"><div><div class="section-kicker">START SOMEWHERE INTERESTING</div><h2>Familiar games. A different home.</h2></div><p>Six doors into the collection, from global series to Zeebo's own characters.</p></div><div class="spotlight-grid">{''.join(spots)}</div></section>
<section class="catalog-wrap" id="catalog"><div class="shell"><div class="section-heading catalog-heading"><div><div class="section-kicker">THE PRESERVED INVENTORY</div><h2>Find something forgotten.</h2></div><p>One record per title ID or reference item. Package variants stay together.</p></div><div class="catalog-controls"><label class="search-field"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"></circle><path d="M16 16l5 5"></path></svg><span class="sr-only">Search titles, IDs, filenames or package checksums</span><input id="search" type="search" autocomplete="off" placeholder="Search titles, IDs, filenames, SHA-256…"><kbd>/</kbd></label><div class="filter-group" role="group" aria-label="Record type">{chips}</div><div class="collection-picker"><label for="collection">Source subset</label><select id="collection"><option value="All">All four subsets</option>{options}</select></div></div><div class="evidence-filter"><label><input id="guide-only" type="checkbox"> Described in the printed guide</label><a class="text-link" href="data/catalog.csv">Download catalog CSV ↗</a></div><div class="results-line"><span id="results-count" role="status" aria-live="polite">Showing {C['catalog_entries']} of {C['catalog_entries']} records</span><span>Archive records, not a claim of tested playability.</span></div><div class="entry-grid">{''.join(card(e) for e in E)}</div><div class="empty-results" id="no-results" hidden><h3>No records match those filters.</h3><p>Try an ID, filename or a different source subset.</p></div><div class="catalog-bottom"><button class="btn btn-secondary" type="button" id="clear-search">Reset filters</button><noscript><p>The complete catalog is visible above. Search and filters need JavaScript.</p></noscript></div></div></section>
<section class="shell closing-banner"><div><div class="section-kicker">FOLLOW THE THREAD</div><h2>The files survived.<br><em>Let's keep their context, too.</em></h2><p>Original names, exact paths, file fingerprints and the stories that can be supported by the surviving sources.</p></div><a class="btn btn-primary" href="about/index.html">Sources, credits &amp; methodology ↗</a></section></main>'''+foot()
    put('index.html',text)
def source_refs(e):
    refs=[]
    if e.get('title_source_url'): refs.append(ext(e['title_source_url'],'OpenZeebo readme — ID mapping, 23 October 2011'))
    if e.get('guide_source_url'): refs.append(ext(e['guide_source_url'],f'Zeebo Brasil Guia de Jogos — scan {esc(e["guide_scan"])}'))
    refs.extend(ext(p['source_url'],f'Original file: {esc(p["filename"])} · {esc(p["subset_name"])}') for p in e['packages'])
    return '<ul>'+''.join('<li>'+x+'</li>' for x in refs)+'</ul>'
def package_panel(p,i):
    rows=[]
    for f in sorted((x for x in p['contents'] if not x['dir']),key=lambda x:x['path'].casefold()):
        rows.append(f'<div class="file-row"><code>{esc(f["path"])}</code><span>{fmt(f["size"])}</span><small class="member-hash">SHA-256 {f["sha256"]}</small></div>')
    info=''
    if p['module_files']: info+='<p><strong>Executable members:</strong> '+', '.join('<code>'+esc(x)+'</code>' for x in p['module_files'])+'</p>'
    if p['descriptor_files']: info+='<p><strong>Descriptors:</strong> '+', '.join('<code>'+esc(x)+'</code>' for x in p['descriptor_files'])+'</p>'
    if p['format']=='7Z' and not p['descriptor_files']: info+='<p>No .mif descriptor is present in this package inventory. Completeness is not assumed.</p>'
    listing=f'<details class="contents"><summary>View {p["files_count"]:,} direct file members <span class="chevron" aria-hidden="true">⌄</span></summary><div class="file-list">{"".join(rows)}</div></details>' if rows else '<p class="detail-text">Standalone file; no archive-member listing.</p>'
    return f'''<section class="detail-panel variant-panel" id="variant-{i}"><div class="panel-heading"><h2>Package {i}: {esc(p['filename'])}</h2><span class="mono-light">{esc(p['subset_name'])}</span></div><dl class="variant-specs"><div><dt>Original format</dt><dd>{esc(p['format'])}</dd></div><div><dt>File size</dt><dd>{fmt(p['size'])} · {p['size']:,} bytes</dd></div><div><dt>Direct file members</dt><dd>{p['files_count']:,}</dd></div><div><dt>Source check</dt><dd>Size + SHA-1 match</dd></div></dl><p class="source-path">{esc(p['source_paths'][0])}</p><div class="checksum"><div class="checksum-title">SHA-256 of this exact source file</div><code>{p['sha256']}</code><button class="copy-button" type="button" data-copy="{p['sha256']}">Copy SHA-256</button></div><details class="verification-details"><summary>Source verification details</summary><p>{esc(p['source_match'])}. This identifies the source file; it is not a playability test.</p><p>Recorded source SHA-1: <code>{p['source_sha1']}</code></p>{f'<p>Content multiset fingerprint: <code>{p["content_sha256"]}</code></p>' if p.get('content_sha256') else ''}</details><div class="detail-text">{info}</div>{listing}<div class="package-actions">{ext(p['source_url'],'Locate this file at Internet Archive','text-link')}<button class="copy-button" type="button" data-copy="{esc(p['source_paths'][0])}">Copy source path</button></div></section>'''
def detail(e):
    ps=e['packages']; badge='APPLICATION ID '+e['id'] if e['id'].isdigit() else 'REFERENCE RECORD'
    notes=''.join('<p>'+esc(n)+'</p>' for n in e.get('notes',[]))
    if e.get('guide_scan'): notes+='<p>Guide descriptions record the advertised game. They do not identify the exact revision of a preserved executable.</p>'
    related=[x for x in E if x['kind']==e['kind'] and x['id']!=e['id']][:4]
    links=''.join(f'<a href="../../{route(x)}"><span>{esc(x["title"])}</span><span aria-hidden="true">↗</span></a>' for x in related)
    text=head(e['title']+' | Zeebo Archive',e['description'],route(e),'../../')
    text+=f'''<main class="shell detail-layout" id="main"><div class="crumbs"><a href="../../index.html">Archive</a><span>/</span><a href="../../index.html#catalog">Catalog</a><span>/</span><span>{esc(e['title'])}</span></div><div class="detail-header"><div class="detail-titleblock"><div class="eyebrow">{esc(badge)}</div><h1>{esc(e['title'])}</h1><div class="detail-badges"><span class="pill">{esc(e['kind'])}</span><span class="pill">{len(ps)} preserved {'package' if len(ps)==1 else 'variants'}</span><span class="pill caution">{esc(e['evidence'])}</span></div><p class="detail-lede">{esc(e['description'])}</p></div><div class="artifact-display" aria-hidden="true"><span class="artifact-caption">PRESERVED FILE RECORD</span><div class="artifact-glyph">{esc(e['id'] if e['id'].isdigit() else 'REF')}</div><div class="artifact-file">ZEEBO / ARCHIVE</div></div></div><div class="detail-columns"><div class="detail-main"><section class="detail-panel history-panel"><div class="panel-heading"><h2>The story in the surviving sources</h2></div><div class="detail-text history-prose"><p>{esc(e['context'])}</p>{notes}</div><div class="history-sources"><h3>Sources for this record</h3>{source_refs(e)}</div></section>{''.join(package_panel(p,i) for i,p in enumerate(ps,1))}</div><aside class="detail-side"><section class="source-panel"><div class="source-icon" aria-hidden="true">↗</div><h2>Follow it to the source.</h2><p>The original collection and preserved files remain at Internet Archive. Match the filenames and fingerprints recorded here.</p>{ext(SOURCE,'Open original collection','btn btn-primary full-btn')}<p class="source-foot">This catalog contains metadata and original summaries. The packages are linked at their original location.</p></section><section class="spec-panel"><h2>At a glance</h2><dl><div><dt>Record ID</dt><dd>{esc(e['id'])}</dd></div><div><dt>Source subsets</dt><dd>{esc(', '.join(D['subsets'][s] for s in e['subsets']))}</dd></div><div><dt>Cataloged package bytes</dt><dd>{fmt(sum(p['size'] for p in ps))}</dd></div><div><dt>Printed guide locator</dt><dd>{esc(e.get('guide_scan') or 'No title summary indexed')}</dd></div></dl></section><section class="detail-panel"><div class="panel-heading"><h2>Keep exploring</h2></div><div class="related-list">{links}</div></section><div class="context-note"><span class="context-icon" aria-hidden="true">i</span><p>Inclusion documents the surviving files. Compatibility, completion and current network services have not been verified by this catalog.</p></div></aside></div><div class="backrow"><a class="btn btn-secondary" href="../../index.html#catalog">← Back to all {C['catalog_entries']} records</a></div></main>'''+foot('../../')
    put(route(e),text)
def about():
    readme=next(e for e in E if e['title']=='OpenZeebo readme — English')['packages'][0]['source_url']
    guide=next(e for e in E if e['id']=='printed-guide')['packages'][0]['source_url']
    interview='https://www.gamedeveloper.com/game-platforms/interview-making-plans-for-zeebo'
    text=head('Sources & story | Zeebo Archive','The history, source evidence, counting rules and preservation credits behind this independent Zeebo catalog.','about/index.html','../')
    text+=f'''<main id="main" class="shell about-shell"><div class="crumbs"><a href="../index.html">Archive</a><span>/</span><span>Sources &amp; story</span></div><div class="about-hero"><div class="eyebrow"><span class="pulse"></span> CONTEXT MATTERS, TOO</div><h1>The games had names.<br><em>The archive should, too.</em></h1><p>Behind the six-digit filenames is an unusual console, a community preservation effort, and a printed guide full of games worth remembering.</p></div><div class="about-grid"><div class="about-text"><h2>A console with mobile roots</h2><p>Zeebo was a television console built around Qualcomm mobile technology. Games arrived over a 3G connection rather than on discs. In a May 2009 interview, its executives described an effort aimed at middle-class households in emerging markets, with Brazil as the initial launch market. {ext(interview,'Read the contemporary interview')}</p><h2>From a storefront to a surviving collection</h2><p>The <strong>OpenZeebo readme dated 23 October 2011</strong> describes a preservation compilation and maps numeric application IDs to game and system-app names. Its claim to contain every release is a statement by that historical source; this catalog counts the files actually supplied.</p><p>The Internet Archive item <strong>Zeebo (All Games + Dev Tools)</strong> was added on <strong>1 March 2021</strong>. Its original collection is credited here, rather than presented as a new recovery by this project. {ext(SOURCE,'View the original collection')}</p><h2>What the four supplied archives contain</h2><p>The uploaded copies yield <strong>61 game/app IDs in 68 title packages</strong>. Those include system applications as well as games. Shared IDs are grouped on one page, retaining distinct packages. IMICRO3D, component ID 12875 inside Action Hero 3D, is not counted as an additional game.</p><p>There are also <strong>16 developer/support files</strong>, three readme/ID-list records and one printed-guide record. Together these make <strong>81 browsing records and 88 source files</strong>. Material under the BREW tools folder is not automatically classified as a Zeebo retail release.</p><h2>A printed guide puts the names in context</h2><p>The undated <strong>Zeebo Brasil S.A. Guia de Jogos</strong> contains 14 scanned spreads. Original brief English summaries of its product descriptions accompany <strong>39 title IDs</strong>. Each page gives its exact scan filename so the description can be checked.</p><p>The guide describes advertised products; it does not authenticate the revision of a surviving executable. Scans and original documents remain linked at their source.</p><h2>How the evidence was checked</h2><p>All <strong>88 source files</strong> match a file size and SHA-1 in the Internet Archive file manifest embedded in the supplied ZIP. SHA-256 values were measured independently for every source file and every direct regular archive member.</p><p>The member inventory excludes directories from file counts. Containers inside the packages, including BAR, PAK and GGZ, were not exhaustively decoded. A content-multiset fingerprint compares file sizes and bytes while ignoring names and order; it is not a folder-layout equivalence claim.</p><h2>Can these files be played?</h2><p>This is a discovery and research catalog. No preserved game or developer utility was executed while assembling it. A file record does not establish compatibility, complete gameplay or continued availability of original online services.</p><h2>Help improve the record</h2><p>Report an incorrect detail, missing credit or broken link through {ext(REPO+'/issues','GitHub Issues')}. Include the title or ID and a supporting source where possible. Wakka reviews reports and publishes updates.</p></div><aside><div class="about-fact"><span>2009</span><strong>A different route to the television</strong><p>A contemporary executive interview explains the digital distribution model and intended audience.</p></div><div class="about-fact"><span>2011</span><strong>OpenZeebo compilation</strong><p>The source readme dates its preservation effort to 23 October.</p></div><div class="about-fact"><span>2021</span><strong>Internet Archive upload</strong><p>The collection was added on 1 March.</p></div><div class="about-fact"><span>2026</span><strong>The names become browsable</strong><p>A searchable catalog with file evidence, source links and guide summaries.</p></div></aside></div><section class="sources-section"><h2>Primary records &amp; context</h2>{''.join(f'<div class="source-reference"><span>0{i}</span><div><strong>{label}</strong><p>{note}</p></div>{ext(url,"View")}</div>' for i,(label,note,url) in enumerate([('Original Internet Archive collection','Source files and public collection metadata',SOURCE),('OpenZeebo English readme','Numeric ID mapping and preservation notes · 23 October 2011',readme),('Zeebo Brasil Guia de Jogos','Printed product guide · undated; 14 scan members',guide),('Contemporary executive interview','Game Developer / Gamasutra · 20 May 2009',interview)],1))}</section><section class="about-end"><h2>Small consoles deserve a big memory.</h2><p>Preservation credits belong to OpenZeebo, the Internet Archive community, Zeebo Brasil S.A. and the original creators. Wakka assembled this independent catalog.</p><a class="btn btn-primary" href="../index.html#catalog">Browse the collection →</a></section></main>'''+foot('../')
    put('about/index.html',text)
def exports():
    def write_csv(name,fields,rows):
        with (ROOT/'data'/name).open('w',encoding='utf-8-sig',newline='') as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)
    write_csv('catalog.csv',['id','title','kind','description','evidence','guide_scan','package_count','page_url'],[{'id':e['id'],'title':e['title'],'kind':e['kind'],'description':e['description'],'evidence':e['evidence'],'guide_scan':e.get('guide_scan') or '','package_count':len(e['packages']),'page_url':BASE+route(e)} for e in E])
    write_csv('packages.csv',['id','title','filename','subset','format','bytes','sha256','source_sha1','source_path','source_url','direct_files','content_multiset_sha256'],[{'id':e['id'],'title':e['title'],'filename':p['filename'],'subset':p['subset'],'format':p['format'],'bytes':p['size'],'sha256':p['sha256'],'source_sha1':p['source_sha1'],'source_path':p['source_paths'][0],'source_url':p['source_url'],'direct_files':p['files_count'],'content_multiset_sha256':p.get('content_sha256') or ''} for e in E for p in e['packages']])
    write_csv('contents.csv',['id','title','package_filename','package_sha256','member_path','bytes','sha256'],[{'id':e['id'],'title':e['title'],'package_filename':p['filename'],'package_sha256':p['sha256'],'member_path':m['path'],'bytes':m['size'],'sha256':m['sha256']} for e in E for p in e['packages'] for m in p['contents'] if not m['dir']])
    urlset=ET.Element('urlset',xmlns='http://www.sitemaps.org/schemas/sitemap/0.9')
    for path in ['', 'about/', *[route(e).replace('index.html','') for e in E]]:
        ET.SubElement(ET.SubElement(urlset,'url'),'loc').text=BASE+path
    put('sitemap.xml',ET.tostring(urlset,encoding='unicode'))
    put('robots.txt','User-agent: *\nAllow: /\nSitemap: '+BASE+'sitemap.xml\n')
    put('.nojekyll','')
    put('404.html',head('Page not found | Zeebo Archive','Return to the Zeebo preservation catalog.',prefix=BASE)+'<main id="main" class="shell about-shell"><div class="about-hero"><h1>This page wandered off.</h1><p><a class="btn btn-primary" href="'+BASE+'">Return to the catalog →</a></p></div></main>'+foot(BASE))
def readme():
    put('README.md',f'''# Zeebo / The Lost Catalog

**A small console. A surprisingly deep archive.**

[**Browse the Zeebo archive →**]({BASE}) · [Sources and story]({BASE}about/) · [Original collection]({SOURCE})

Created and maintained by **Wakkatobakka**. Explore the surviving Zeebo collection by name, compare preserved package variants, and follow the evidence back to its source.

![Zeebo Archive](assets/social-preview.png)

## Explore the collection

- **61 game/app IDs**, mapped using the 2011 OpenZeebo title list.
- **68 title packages**, with variants grouped on the same title page.
- **20 tools and reference records**, including 16 developer/support files, a printed guide, and three source-text records.
- **14 scanned guide spreads indexed**, with original summaries for **39 documented title IDs**.
- **81 browsing records and 88 source-file fingerprints**, with direct-member inventories and SHA-256 values.
- Search by title, ID, original path, internal filename, or package fingerprint; filter by record type, source subset, or guide coverage.

This catalog contains metadata, original summaries, decorative artwork, and source links. Original game binaries, developer tools, guide scans, and PDFs remain at their source.

## Sources and counting rules

Original preservation credits belong to **OpenZeebo and the Internet Archive community**. The printed game guide is credited to **Zeebo Brasil S.A.**

All 88 cataloged source files match sizes and SHA-1 values in the Internet Archive manifest embedded in the supplied archive. SHA-256 values were measured independently. Input-archive and manifest fingerprints remain in `data/catalog.json`.

The 61 game/app IDs include system applications; they are not a claim of 61 retail games. Bundled IMICRO3D component ID 12875 is not counted as an additional game. Material under the developer folder is not automatically classified as a Zeebo release.

The printed guide is undated. The English OpenZeebo readme is dated October 23, 2011. Guide descriptions identify advertised products, rather than authenticating exact executable revisions. No preserved game or utility was run for this catalog.

## Follow the records

| File | Contents |
| --- | --- |
| [Catalog CSV](data/catalog.csv) | 81 title/reference records |
| [Package CSV](data/packages.csv) | 88 source files, including title variants |
| [Contents CSV](data/contents.csv) | Direct regular archive members, with SHA-256 values |
| [Complete JSON](data/catalog.json) | Nested catalog and source provenance |

Directories are excluded from file counts. Internal BAR, PAK, and GGZ containers were not exhaustively decoded. Content-multiset fingerprints compare file bytes and sizes while ignoring member names and order.

## Errors and broken links

Report an incorrect detail, missing credit, or broken link through [GitHub Issues]({REPO}/issues). Include the title or record ID and a supporting source where possible. Wakka reviews reports and publishes any updates.

## More from Wakka's archive

[Qualcomm BREW](https://wakkatobakka.github.io/qualcomm-brew-archive/) · [Zeebo]({BASE}) · [ExEn](https://wakkatobakka.github.io/exen-game-archive/) · [DoJa](https://wakkatobakka.github.io/doja-archive/)

---
Independent catalog by Wakkatobakka. No affiliation with Zeebo, Tectoy, Qualcomm, or original rights holders. Original third-party content retains its respective ownership.
''')

homepage()
for e in E: detail(e)
about();exports();readme()
print(f'Rebuilt {len(E)} record pages, homepage, About, exports and sitemap.')
