# T3 Content Library

Python CLI + Web UI that generates 20 realistic TYPO3 example pages with AI-generated German content using the Claude API. Each page is output as Markdown with YAML frontmatter and TYPO3 content element annotations.

![Start](docs/screenshots/01-start.png)

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

## Web UI

The project includes a React frontend with real-time progress tracking, token usage display and page preview.

**Progress tracking** with page chips, live token counter and elapsed time:

![Progress](docs/screenshots/02-progress.png)

**Results view** with stats bar (duration, tokens, cost) and content preview:

![Results](docs/screenshots/03-results.png)

## Requirements

- Python 3.11+
- Node.js 18+ (for Web UI)
- [Anthropic API key](https://console.anthropic.com/)

## Installation

### CLI

```bash
git clone https://github.com/dkd-dobberkau/t3-content-library.git
cd t3-content-library
uv venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt
```

### Web UI

```bash
# Backend
cd backend
uv venv .venv && source .venv/bin/activate
uv pip install -r requirements.txt -r ../requirements.txt

# Frontend
cd ../frontend-vite
npm install
```

## Configuration

```bash
cp .env.example .env
# Add your Anthropic API key to .env
```

## Usage

### CLI

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

Options:
- `--parallel N` — Number of concurrent page generations (default: 5)
- `--jsonl` — Machine-readable JSONL output (used by backend)

### Web UI

Start both services:

```bash
# Terminal 1: Backend (Port 8000)
cd backend && .venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: Frontend (Port 3000)
cd frontend-vite && npm run dev
```

Open http://localhost:3000 in your browser.

## Project Structure

```
t3-content-library/
├── config/structure/       # 20 YAML page definitions with CE types and prompts
├── t3_content_library/
│   ├── loader.py           # YAML structure loader
│   ├── generator.py        # Claude API content generator (batched, with token tracking)
│   ├── renderer.py         # Jinja2 Markdown renderer
│   └── cli.py              # Click CLI (parallel generation, JSONL output)
├── backend/
│   └── app.py              # FastAPI REST API + SSE progress streaming
├── frontend-vite/          # React + Vite frontend
│   └── src/
│       ├── App.jsx         # Main application component
│       └── styles.css      # Dark theme styling
├── templates/
│   └── page.md.j2          # Markdown output template
├── tests/                  # Unit and integration tests
├── generate.py             # Entry point
└── requirements.txt
```

## Testing

```bash
uv pip install pytest
python -m pytest tests/ -v
```

All tests use mocked API calls — no API key needed for testing.

## License

[MIT](LICENSE)
