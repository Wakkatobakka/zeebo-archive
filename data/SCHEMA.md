# Research data

`catalog.json`, `catalog.csv`, `packages.csv` and `contents.csv` preserve the original inventory byte for byte. `protected-files.json` records their SHA-256 values, plus those of the existing colour stylesheet and console illustration.

`research.json` adds historical material without changing the inventory:

- `version`, `reviewed`, `premise`: edition metadata.
- `sources`: stable source IDs mapped to title, URL, kind, publication date if known, review date and research note. Separate source records can reference different uses of one URL.
- `games`: keyed by the original catalog entry ID, including applications and reference material. Each record has a short `deck`, optional release `year`, paragraph arrays `overview`, `development`, `release` and `notes`, scoped `credits` and `studio_roles`, optional `quotes`, and optional `media`.
- `platform`: headings, sourced paragraphs and optional quotations for the platform-history page.

Each paragraph has `text` and `sources`. Development paragraphs marked `after_quote: true` follow the section's quotation. Quotations have exact `text`, `speaker`, `attribution`, optional `translation`, `section` and one `source` ID.

Personal credits have `name`, `role`, `team`, `scope` and `source`. Studio roles use `name`, `role`, `scope` and `source`. `scope: Zeebo` refers to the console edition; other scopes identify the original arcade, console or mobile work. These are selected documented roles, not an assertion that every original credit has been transcribed.

Images have a local `path`, `alt`, factual `caption`, `credit`, `source`, `original_url`, pixel dimensions, artifact `kind`, platform and evidence for its identification. `placement` controls whether an image appears alongside the game, development or gallery section. The included historical images retain their original bytes.

`credits.csv` is generated from personal roles. Edit research data and rebuild rather than editing the CSV or generated HTML directly.
