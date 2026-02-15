# T3 Content Library

Python CLI that generates 20 realistic TYPO3 example pages with AI-generated German content using the Claude API. Each page is output as Markdown with YAML frontmatter and TYPO3 content element annotations.

## What it does

Given a company description (e.g. "Italienisches Restaurant La Bella Vista in München"), the tool generates a complete set of 20 pages typical for a German business website:

| Pages | Description |
|-------|-------------|
| Startseite, Über uns, Team, Geschichte | Company presentation |
| Leistungen + 3 Detail pages | Services / Products |
| Referenzen + Detail | Portfolio / Case studies |
| Aktuelles + 2 Articles | News / Blog |
| FAQ, Kontakt | Support |
| Impressum, Datenschutz, AGB | Legal (German) |
| Downloads, Sitemap | Utilities |

Each generated Markdown file contains:
- YAML frontmatter with title, slug, parent, layout, nav position, SEO fields
- Content elements annotated with `<!-- CE: type -->` comments matching TYPO3 CE types (header, textmedia, text, quote, accordion, etc.)

## Requirements

- Python 3.11+
- [Anthropic API key](https://console.anthropic.com/)

## Installation

```bash
git clone https://github.com/dkd-dobberkau/t3-content-library.git
cd t3-content-library
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Configuration

```bash
cp .env.example .env
# Add your Anthropic API key to .env
```

## Usage

```bash
python generate.py
```

You will be prompted for:
- **Firma/Thema** — Company description, e.g. `Italienisches Restaurant La Bella Vista in München`
- **Ausgabeverzeichnis** — Output directory (default: `./output`)

Or pass options directly:

```bash
python generate.py --company "Schreinerei Holzmann in Frankfurt" --output-dir ./output
```

The tool generates 20 Markdown files in a subdirectory named after the company.

## Project Structure

```
t3-content-library/
├── config/structure/       # 20 YAML page definitions with CE types and prompts
├── t3_content_library/
│   ├── loader.py           # YAML structure loader
│   ├── generator.py        # Claude API content generator
│   ├── renderer.py         # Jinja2 Markdown renderer
│   └── cli.py              # Click CLI
├── templates/
│   └── page.md.j2          # Markdown output template
├── tests/                  # Unit and integration tests
├── generate.py             # Entry point
└── requirements.txt
```

## Testing

```bash
pip install pytest
python -m pytest tests/ -v
```

All tests use mocked API calls — no API key needed for testing.

## License

[MIT](LICENSE)
