"""Original file-inventory display helpers, retained from the existing archive."""

import html

def esc(x): return html.escape(str(x),quote=True)

def fmt(n):
    return f'{n:,} B' if n<1024 else f'{n/1024:,.1f} KiB' if n<1024**2 else f'{n/1024**2:,.2f} MiB'

def ext(url,label,cls=''):
    return f'<a class="{cls}" href="{esc(url)}" target="_blank" rel="noopener noreferrer">{label} <span aria-hidden="true">↗</span></a>'

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
