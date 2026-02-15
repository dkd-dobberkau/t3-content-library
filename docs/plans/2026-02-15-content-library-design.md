# T3 Content Library - Design Document

## Goal

A Python CLI tool that generates 20 example pages with typical TYPO3 content elements, themed to a user-specified business/industry. Content is generated via the Claude API for natural, unique text. Output is Markdown with YAML frontmatter, ready for import into TYPO3 v13.

## Target Audience

TYPO3 beginners (learning), agencies/developers (demos, sitepackage development).

## Architecture

### Flow

```
User runs CLI → enters company/theme description
  → Script loads 20 page structure definitions (YAML)
  → Per page: Claude API generates content for each CE
  → Script renders Markdown with YAML frontmatter
  → Output: 20 .md files in named subdirectory
```

### Project Structure

```
t3-content-library/
├── generate.py              # CLI entry point (click)
├── requirements.txt         # click, jinja2, pyyaml, anthropic
├── .env.example             # ANTHROPIC_API_KEY=sk-...
├── config/
│   └── structure/           # Page structure definitions
│       ├── 01-homepage.yaml
│       ├── 02-about.yaml
│       ├── ...
│       └── 20-sitemap.yaml
├── templates/
│   └── page.md.j2           # Markdown output template
└── output/                  # Generated files (gitignored)
```

### Structure Definition Format (YAML)

Each page is defined as a YAML file specifying its metadata and content elements with prompts:

```yaml
page:
  title: "Über uns"
  slug: "ueber-uns"
  parent: "/"
  nav_position: 2
content_elements:
  - type: header
    prompt: "Erstelle eine einladende Überschrift für die Über-uns-Seite von {company}"
  - type: textmedia
    prompt: "Schreibe über die Geschichte von {company}. 3-4 Sätze."
    image: "placeholder://team.jpg"
    image_position: right
  - type: text
    subtype: bullets
    prompt: "Nenne 3 Kernwerte von {company} mit kurzer Erklärung"
  - type: quote
    prompt: "Erstelle ein realistisches Kundenzitat über {company}"
```

### Output Format (Markdown + YAML Frontmatter)

```markdown
---
title: "Über uns"
slug: "ueber-uns"
parent: "/"
layout: "default"
nav_position: 2
seo:
  title: "Über uns - La Bella Vista"
  description: "Erfahren Sie mehr über La Bella Vista"
---

<!-- CE: header -->
# Willkommen bei La Bella Vista

<!-- CE: textmedia, image: placeholder://team.jpg, position: right -->
## Unsere Geschichte

Seit 2005 servieren wir in München authentische italienische Küche...

<!-- CE: text, subtype: bullets -->
## Unsere Werte

- **Authentizität** — Originalrezepte aus der Toskana
- **Frische** — Tägliche Lieferung vom Großmarkt
- **Gastfreundschaft** — Jeder Gast ist Familie

<!-- CE: quote -->
> "Das beste italienische Restaurant in München!"
> — Maria S., Stammgast
```

## 20 Pages with CE Coverage

| # | Page | Slug | Content Elements |
|---|------|------|-----------------|
| 1 | Startseite | `/` | header, textmedia, text, shortcut |
| 2 | Über uns | `/ueber-uns` | header, textmedia, text, quote |
| 3 | Team | `/ueber-uns/team` | header, text, image |
| 4 | Geschichte | `/ueber-uns/geschichte` | header, text blocks, textmedia |
| 5 | Leistungen | `/leistungen` | header, text, textmedia cards |
| 6 | Leistung Detail 1 | `/leistungen/detail-1` | header, textmedia, bullets, text |
| 7 | Leistung Detail 2 | `/leistungen/detail-2` | header, textmedia, table, text |
| 8 | Leistung Detail 3 | `/leistungen/detail-3` | header, textmedia, accordion |
| 9 | Referenzen | `/referenzen` | header, image gallery, textmedia |
| 10 | Referenz Detail | `/referenzen/projekt-1` | header, textmedia, quote, text |
| 11 | Blog/Aktuelles | `/aktuelles` | header, text listing |
| 12 | Blog-Artikel 1 | `/aktuelles/artikel-1` | header, textmedia, text, tags |
| 13 | Blog-Artikel 2 | `/aktuelles/artikel-2` | header, text, image, quote |
| 14 | FAQ | `/faq` | header, accordion |
| 15 | Kontakt | `/kontakt` | header, text, form placeholder |
| 16 | Impressum | `/impressum` | header, text |
| 17 | Datenschutz | `/datenschutz` | header, text |
| 18 | AGB | `/agb` | header, text |
| 19 | Downloads | `/downloads` | header, uploads, text |
| 20 | Sitemap | `/sitemap` | header, menu, text |

### CE Types Covered

header, text, textmedia, image, bullets, table, accordion, quote, uploads, menu, shortcut, HTML, form placeholder.

## CLI Interface

```bash
python generate.py

# Interactive prompts:
# > Company/Theme: Italienisches Restaurant La Bella Vista in München
# > Output directory [./output]:
#
# Generating pages...
# [1/20] Startseite ✓
# [2/20] Über uns ✓
# ...
# [20/20] Sitemap ✓
#
# ✓ 20 pages generated in ./output/la-bella-vista/
```

## Dependencies

- `click` — CLI interface
- `anthropic` — Claude API for content generation
- `jinja2` — Markdown template rendering
- `pyyaml` — Structure definition parsing
- `python-dotenv` — .env file loading

## Tech Decisions

- **TYPO3 v13** target version
- **German language** only
- **Claude API** (Anthropic) for content generation, API key required
- **No TYPO3 importer** in v1 — output is Markdown, import tooling is a future phase
