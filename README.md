# Zeebo / The Lost Catalog

**A small console. A surprisingly deep archive.**

A searchable GitHub Pages catalog assembled from four supplied Zeebo archive copies. Original preservation credits belong to OpenZeebo and the Internet Archive community. The printed guide is credited to Zeebo Brasil S.A.

## What's here

- **61 game/app IDs**, mapped using the 2011 OpenZeebo title list.
- **68 title packages**, with variants grouped on the same title page.
- **20 tools and reference records**, including 16 developer/support files, the guide and three source-text records.
- **14 scanned guide spreads indexed**, with original summaries for **39 documented title IDs**.
- **81 browsing records / 88 source-file fingerprints**, plus direct-member inventories and SHA-256 values.
- Search by title, ID, original path, internal filename or package SHA-256. Filter by record type, source subset or guide coverage.

This repository contains metadata, original summaries, decorative artwork and source links. Original game binaries, tools, guide scans and PDFs remain at their source.

## Publish on GitHub Pages

1. Extract this ZIP on your computer.
2. Create a public GitHub repository named **`zeebo-archive`** under **Wakkatobakka**.
3. Copy this folder's **contents** into the repository root. `index.html`, `assets`, `games`, `resources`, `data`, `about` and `tools` must sit directly inside the repository.
4. Commit and publish the repository.
5. Open **Settings → Pages**. Choose **Deploy from a branch → main → /(root)**, then **Save**.

Expected address after deployment: **https://wakkatobakka.github.io/zeebo-archive/**

No build service, API keys or paid hosting are required. You can preview locally by opening `index.html` before uploading.

## Sources & counting rules

Original collection: **https://archive.org/details/zeebo-romset-and-devtools**

All 88 cataloged source files match sizes and SHA-1 values in the embedded Internet Archive manifest. SHA-256 values were measured independently. Input-archive and manifest fingerprints are retained in `data/catalog.json`.

Game/app counts are distinct six-digit IDs, not a claim of 61 retail games. ID 12875 is a bundled IMICRO3D component. Material under the developer folder is not automatically classified as a Zeebo release. All distinct title packages remain recorded.

The printed guide is undated. The English OpenZeebo readme is dated 23 October 2011. Guide descriptions identify advertised products, not exact executable revisions. No preserved game or utility was run for this catalog.

## Metadata downloads

| File | Contents |
| --- | --- |
| `data/catalog.csv` | 81 title/reference records |
| `data/packages.csv` | 88 source files, including title variants |
| `data/contents.csv` | Direct regular archive members, with SHA-256 |
| `data/catalog.json` | Full nested catalog and provenance |

Directories are excluded from file counts. Internal BAR, PAK and GGZ containers were not exhaustively decoded. Content-multiset fingerprints ignore member names and order.

## Suggest a correction

Open an issue or propose a pull request with the title/ID, correction and a source. Wakka reviews contributions before they appear on the site.

## Maintainer notes

Edit `data/catalog.json`, then run:

```sh
python3 tools/build_site.py
```

The standard-library script rebuilds the homepage, record pages, About page, CSV exports and sitemap. It needs no game files. For lasting metadata edits, update JSON rather than the generated CSVs or pages.

To use another repository, change `repository` and `site_url` in the JSON, rebuild, and update these publishing instructions.

---

Independent community catalog by Wakka. No affiliation with Zeebo, Tectoy, Qualcomm or original rights holders. Original content retains its respective ownership.
