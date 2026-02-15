# T3 Content Library Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Python CLI that generates 20 TYPO3 example pages with Claude API-generated content as Markdown + YAML frontmatter.

**Architecture:** CLI (click) loads YAML structure definitions per page, sends prompts to Claude API for each content element, renders results through a Jinja2 template into Markdown files with CE-type annotations.

**Tech Stack:** Python 3.11+, click, anthropic, jinja2, pyyaml, python-dotenv

---

### Task 1: Project Scaffolding

**Files:**
- Create: `requirements.txt`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `t3_content_library/__init__.py`

**Step 1: Create requirements.txt**

```
click>=8.1
anthropic>=0.40
jinja2>=3.1
pyyaml>=6.0
python-dotenv>=1.0
```

**Step 2: Create .env.example**

```
ANTHROPIC_API_KEY=sk-ant-...
```

**Step 3: Create .gitignore**

```
output/
.env
__pycache__/
*.pyc
.venv/
```

**Step 4: Create package init**

Create `t3_content_library/__init__.py` as empty file.

**Step 5: Create virtual environment and install dependencies**

Run: `python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
Expected: All packages install successfully.

**Step 6: Commit**

```bash
git add requirements.txt .env.example .gitignore t3_content_library/__init__.py
git commit -m "chore: project scaffolding with dependencies"
```

---

### Task 2: Structure Loader

**Files:**
- Create: `t3_content_library/loader.py`
- Create: `tests/test_loader.py`
- Create: `config/structure/02-about.yaml` (test fixture)

**Step 1: Create test fixture YAML**

Create `config/structure/02-about.yaml`:

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
    prompt: "Schreibe über die Geschichte von {company}. 3-4 Sätze, authentisch."
    image: "placeholder://team.jpg"
    image_position: right
  - type: text
    subtype: bullets
    prompt: "Nenne 3 Kernwerte von {company} mit je einer kurzen Erklärung"
  - type: quote
    prompt: "Erstelle ein realistisches Kundenzitat über {company}"
```

**Step 2: Write the failing test**

Create `tests/test_loader.py`:

```python
import os
from t3_content_library.loader import load_page_structure, load_all_structures


def test_load_page_structure():
    base = os.path.join(os.path.dirname(__file__), "..", "config", "structure")
    page = load_page_structure(os.path.join(base, "02-about.yaml"))

    assert page["page"]["title"] == "Über uns"
    assert page["page"]["slug"] == "ueber-uns"
    assert len(page["content_elements"]) == 4
    assert page["content_elements"][0]["type"] == "header"
    assert "{company}" in page["content_elements"][0]["prompt"]


def test_load_all_structures():
    base = os.path.join(os.path.dirname(__file__), "..", "config", "structure")
    pages = load_all_structures(base)

    assert len(pages) >= 1
    assert pages[0]["page"]["title"] == "Über uns"


def test_structures_sorted_by_filename():
    """Structures load in filename order (01-, 02-, etc.)."""
    base = os.path.join(os.path.dirname(__file__), "..", "config", "structure")
    pages = load_all_structures(base)
    # With only one file, just verify it loads
    assert len(pages) >= 1
```

**Step 3: Run test to verify it fails**

Run: `cd /Users/olivier/Versioncontrol/local/t3-content-library && .venv/bin/python -m pytest tests/test_loader.py -v`
Expected: FAIL with `ModuleNotFoundError` or `ImportError`

**Step 4: Write minimal implementation**

Create `t3_content_library/loader.py`:

```python
import os
import yaml


def load_page_structure(filepath: str) -> dict:
    """Load a single page structure definition from a YAML file."""
    with open(filepath, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_all_structures(directory: str) -> list[dict]:
    """Load all page structure YAML files from a directory, sorted by filename."""
    structures = []
    for filename in sorted(os.listdir(directory)):
        if filename.endswith(".yaml") or filename.endswith(".yml"):
            filepath = os.path.join(directory, filename)
            structures.append(load_page_structure(filepath))
    return structures
```

**Step 5: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_loader.py -v`
Expected: 3 tests PASS

**Step 6: Commit**

```bash
git add t3_content_library/loader.py tests/test_loader.py config/structure/02-about.yaml
git commit -m "feat: add YAML structure loader for page definitions"
```

---

### Task 3: Content Generator (Claude API)

**Files:**
- Create: `t3_content_library/generator.py`
- Create: `tests/test_generator.py`

**Step 1: Write the failing test**

Create `tests/test_generator.py`:

```python
from unittest.mock import patch, MagicMock
from t3_content_library.generator import generate_content_for_page


def _make_mock_response(text: str):
    mock_response = MagicMock()
    mock_block = MagicMock()
    mock_block.text = text
    mock_response.content = [mock_block]
    return mock_response


def test_generate_content_for_page():
    structure = {
        "page": {"title": "Über uns", "slug": "ueber-uns", "parent": "/", "nav_position": 2},
        "content_elements": [
            {"type": "header", "prompt": "Erstelle eine Überschrift für {company}"},
            {"type": "text", "prompt": "Schreibe einen Text über {company}"},
        ],
    }

    with patch("t3_content_library.generator.anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.side_effect = [
            _make_mock_response("# Willkommen bei La Bella Vista"),
            _make_mock_response("Seit 2005 servieren wir authentische Küche."),
        ]

        result = generate_content_for_page(structure, "La Bella Vista, München")

        assert len(result) == 2
        assert result[0]["type"] == "header"
        assert "Willkommen" in result[0]["content"]
        assert result[1]["type"] == "text"
        assert "2005" in result[1]["content"]
        assert mock_client.messages.create.call_count == 2


def test_content_element_preserves_metadata():
    """Image paths, positions etc. are passed through to results."""
    structure = {
        "page": {"title": "Test", "slug": "test", "parent": "/", "nav_position": 1},
        "content_elements": [
            {
                "type": "textmedia",
                "prompt": "Text über {company}",
                "image": "placeholder://hero.jpg",
                "image_position": "right",
            },
        ],
    }

    with patch("t3_content_library.generator.anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = _make_mock_response("Toller Text.")

        result = generate_content_for_page(structure, "TestFirma")

        assert result[0]["image"] == "placeholder://hero.jpg"
        assert result[0]["image_position"] == "right"
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_generator.py -v`
Expected: FAIL with `ImportError`

**Step 3: Write minimal implementation**

Create `t3_content_library/generator.py`:

```python
import anthropic


SYSTEM_PROMPT = """Du bist ein Content-Autor für eine Unternehmenswebsite.
Schreibe natürlichen, professionellen deutschen Content.
Antworte NUR mit dem angeforderten Content, ohne Erklärungen oder Kommentare.
Verwende Markdown-Formatierung wo passend."""


def generate_content_for_page(
    structure: dict,
    company_description: str,
    model: str = "claude-sonnet-4-5-20250929",
) -> list[dict]:
    """Generate content for all content elements of a page via Claude API."""
    client = anthropic.Anthropic()
    results = []

    for ce in structure["content_elements"]:
        prompt = ce["prompt"].replace("{company}", company_description)

        response = client.messages.create(
            model=model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}],
        )

        content_text = response.content[0].text

        result = {"type": ce["type"], "content": content_text}

        # Pass through metadata fields
        for key in ("subtype", "image", "image_position"):
            if key in ce:
                result[key] = ce[key]

        results.append(result)

    return results
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_generator.py -v`
Expected: 2 tests PASS

**Step 5: Commit**

```bash
git add t3_content_library/generator.py tests/test_generator.py
git commit -m "feat: add Claude API content generator"
```

---

### Task 4: Markdown Renderer

**Files:**
- Create: `templates/page.md.j2`
- Create: `t3_content_library/renderer.py`
- Create: `tests/test_renderer.py`

**Step 1: Write the failing test**

Create `tests/test_renderer.py`:

```python
from t3_content_library.renderer import render_page


def test_render_page_with_frontmatter():
    page_meta = {
        "title": "Über uns",
        "slug": "ueber-uns",
        "parent": "/",
        "nav_position": 2,
    }
    content_elements = [
        {"type": "header", "content": "# Willkommen bei La Bella Vista"},
        {
            "type": "textmedia",
            "content": "Seit 2005 servieren wir Küche.",
            "image": "placeholder://team.jpg",
            "image_position": "right",
        },
        {
            "type": "text",
            "subtype": "bullets",
            "content": "- **Qualität** — Frische Zutaten\n- **Service** — Herzlich",
        },
        {"type": "quote", "content": '> "Tolles Restaurant!"\n> — Maria S., Stammgast'},
    ]

    result = render_page(page_meta, content_elements, "La Bella Vista")

    # Check YAML frontmatter
    assert result.startswith("---\n")
    assert 'title: "Über uns"' in result
    assert 'slug: "ueber-uns"' in result

    # Check CE annotations
    assert "<!-- CE: header -->" in result
    assert "<!-- CE: textmedia, image: placeholder://team.jpg, position: right -->" in result
    assert "<!-- CE: text, subtype: bullets -->" in result
    assert "<!-- CE: quote -->" in result

    # Check content is present
    assert "Willkommen bei La Bella Vista" in result
    assert "Seit 2005" in result
    assert "Tolles Restaurant" in result


def test_render_page_seo_fields():
    page_meta = {"title": "Kontakt", "slug": "kontakt", "parent": "/", "nav_position": 5}
    content_elements = [{"type": "header", "content": "# Kontakt"}]

    result = render_page(page_meta, content_elements, "TestFirma")

    assert "seo:" in result
    assert "Kontakt - TestFirma" in result
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_renderer.py -v`
Expected: FAIL with `ImportError`

**Step 3: Create Jinja2 template**

Create `templates/page.md.j2`:

```
---
title: "{{ page.title }}"
slug: "{{ page.slug }}"
parent: "{{ page.parent }}"
layout: "default"
nav_position: {{ page.nav_position }}
seo:
  title: "{{ page.title }} - {{ company_name }}"
  description: "{{ page.title }} von {{ company_name }}"
---
{% for ce in content_elements %}

<!-- CE: {{ ce.type }}
{%- if ce.image is defined %}, image: {{ ce.image }}{% endif %}
{%- if ce.image_position is defined %}, position: {{ ce.image_position }}{% endif %}
{%- if ce.subtype is defined %}, subtype: {{ ce.subtype }}{% endif %} -->
{{ ce.content }}
{% endfor %}
```

**Step 4: Write minimal implementation**

Create `t3_content_library/renderer.py`:

```python
import os
from jinja2 import Environment, FileSystemLoader


def render_page(
    page_meta: dict,
    content_elements: list[dict],
    company_name: str,
) -> str:
    """Render a page to Markdown with YAML frontmatter."""
    templates_dir = os.path.join(os.path.dirname(__file__), "..", "templates")
    env = Environment(
        loader=FileSystemLoader(templates_dir),
        keep_trailing_newline=True,
        trim_blocks=True,
        lstrip_blocks=True,
    )
    template = env.get_template("page.md.j2")

    return template.render(
        page=page_meta,
        content_elements=content_elements,
        company_name=company_name,
    )
```

**Step 5: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_renderer.py -v`
Expected: 2 tests PASS

Note: The template may need whitespace adjustments to match the assertions exactly. Fix the template until tests pass.

**Step 6: Commit**

```bash
git add templates/page.md.j2 t3_content_library/renderer.py tests/test_renderer.py
git commit -m "feat: add Jinja2 markdown renderer with YAML frontmatter"
```

---

### Task 5: CLI Entry Point

**Files:**
- Create: `generate.py`
- Create: `t3_content_library/cli.py`
- Create: `tests/test_cli.py`

**Step 1: Write the failing test**

Create `tests/test_cli.py`:

```python
import os
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from t3_content_library.cli import main


def test_cli_generates_output_files(tmp_path):
    """CLI creates markdown files in output directory."""
    structure_dir = os.path.join(os.path.dirname(__file__), "..", "config", "structure")

    with patch("t3_content_library.cli.generate_content_for_page") as mock_gen:
        mock_gen.return_value = [
            {"type": "header", "content": "# Test Seite"},
            {"type": "text", "content": "Beispieltext."},
        ]

        runner = CliRunner()
        result = runner.invoke(
            main,
            input=f"Testfirma GmbH\n{tmp_path}\n",
        )

        assert result.exit_code == 0
        assert "generiert" in result.output.lower() or "generated" in result.output.lower()

        # At least one .md file should exist
        md_files = list(tmp_path.rglob("*.md"))
        assert len(md_files) >= 1


def test_cli_shows_progress():
    """CLI shows progress like [1/20]."""
    with patch("t3_content_library.cli.generate_content_for_page") as mock_gen:
        mock_gen.return_value = [{"type": "header", "content": "# Test"}]

        runner = CliRunner()
        result = runner.invoke(
            main,
            input="Testfirma\n/tmp/t3test\n",
        )

        assert "[1/" in result.output
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/python -m pytest tests/test_cli.py -v`
Expected: FAIL with `ImportError`

**Step 3: Write implementation**

Create `t3_content_library/cli.py`:

```python
import os
import re
import click
from dotenv import load_dotenv

from t3_content_library.loader import load_all_structures
from t3_content_library.generator import generate_content_for_page
from t3_content_library.renderer import render_page


def slugify(text: str) -> str:
    """Create a filesystem-safe slug from text."""
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9äöüß\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:50].strip("-")


@click.command()
@click.option(
    "--company",
    prompt="Firma/Thema",
    help="Beschreibung des Unternehmens, z.B. 'Italienisches Restaurant La Bella Vista in München'",
)
@click.option(
    "--output-dir",
    prompt="Ausgabeverzeichnis",
    default="./output",
    help="Verzeichnis für die generierten Dateien",
)
def main(company: str, output_dir: str):
    """Generiert 20 TYPO3-Beispielseiten mit Content von Claude."""
    load_dotenv()

    structure_dir = os.path.join(os.path.dirname(__file__), "..", "config", "structure")
    structures = load_all_structures(structure_dir)

    if not structures:
        click.echo("Keine Seitenstrukturen gefunden in config/structure/")
        raise SystemExit(1)

    # Create output subdirectory from company name
    slug = slugify(company)
    dest = os.path.join(output_dir, slug)
    os.makedirs(dest, exist_ok=True)

    total = len(structures)
    for i, structure in enumerate(structures, 1):
        page = structure["page"]
        click.echo(f"[{i}/{total}] {page['title']}...", nl=False)

        content_elements = generate_content_for_page(structure, company)
        markdown = render_page(page, content_elements, company)

        filename = f"{page['slug'].strip('/').replace('/', '-') or 'index'}.md"
        filepath = os.path.join(dest, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown)

        click.echo(" ✓")

    click.echo(f"\n✓ {total} Seiten generiert in {dest}/")
```

Create `generate.py`:

```python
#!/usr/bin/env python3
"""T3 Content Library - TYPO3 Example Content Generator."""

from t3_content_library.cli import main

if __name__ == "__main__":
    main()
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/python -m pytest tests/test_cli.py -v`
Expected: 2 tests PASS

**Step 5: Commit**

```bash
git add generate.py t3_content_library/cli.py tests/test_cli.py
git commit -m "feat: add click CLI with progress output"
```

---

### Task 6: Create All 20 Page Structure Definitions

**Files:**
- Create: `config/structure/01-homepage.yaml`
- Verify: `config/structure/02-about.yaml` (already exists)
- Create: `config/structure/03-team.yaml`
- Create: `config/structure/04-geschichte.yaml`
- Create: `config/structure/05-leistungen.yaml`
- Create: `config/structure/06-leistung-detail-1.yaml`
- Create: `config/structure/07-leistung-detail-2.yaml`
- Create: `config/structure/08-leistung-detail-3.yaml`
- Create: `config/structure/09-referenzen.yaml`
- Create: `config/structure/10-referenz-detail.yaml`
- Create: `config/structure/11-aktuelles.yaml`
- Create: `config/structure/12-artikel-1.yaml`
- Create: `config/structure/13-artikel-2.yaml`
- Create: `config/structure/14-faq.yaml`
- Create: `config/structure/15-kontakt.yaml`
- Create: `config/structure/16-impressum.yaml`
- Create: `config/structure/17-datenschutz.yaml`
- Create: `config/structure/18-agb.yaml`
- Create: `config/structure/19-downloads.yaml`
- Create: `config/structure/20-sitemap.yaml`

**Step 1: Create all YAML files**

Each file follows the same schema. Key patterns per file:

**01-homepage.yaml** — CEs: header, textmedia, text, shortcut. Prompts ask for hero headline, intro text, teaser texts for subpages.

**03-team.yaml** — CEs: header, text (intro), image (gallery). Prompts: team overview, 3-4 fictional team members with roles.

**04-geschichte.yaml** — CEs: header, text (multiple blocks as timeline), textmedia. Prompts: founding story, milestones.

**05-leistungen.yaml** — CEs: header, text (intro), textmedia (x3 as cards). Prompts: services overview, 3 service teasers.

**06-leistung-detail-1.yaml** — CEs: header, textmedia, bullets, text. Prompts: detailed service description, feature list, conclusion.

**07-leistung-detail-2.yaml** — CEs: header, textmedia, table, text. Prompts: service details, pricing/comparison table.

**08-leistung-detail-3.yaml** — CEs: header, textmedia, accordion. Prompts: service with expandable detail sections.

**09-referenzen.yaml** — CEs: header, image (gallery), textmedia. Prompts: project showcase intro, project descriptions.

**10-referenz-detail.yaml** — CEs: header, textmedia, quote, text. Prompts: detailed project case study, client quote.

**11-aktuelles.yaml** — CEs: header, text (listing intro). Prompts: blog/news overview text.

**12-artikel-1.yaml** — CEs: header, textmedia, text. Prompts: industry-relevant news article.

**13-artikel-2.yaml** — CEs: header, text, image, quote. Prompts: second article with expert quote.

**14-faq.yaml** — CEs: header, accordion. Prompts: 6-8 typical FAQs for the business.

**15-kontakt.yaml** — CEs: header, text, text (form placeholder). Prompts: contact info, directions.

**16-impressum.yaml** — CEs: header, text. Prompts: German legal notice (Impressum) with placeholder data.

**17-datenschutz.yaml** — CEs: header, text. Prompts: German DSGVO privacy policy template.

**18-agb.yaml** — CEs: header, text. Prompts: German terms & conditions template.

**19-downloads.yaml** — CEs: header, uploads, text. Prompts: downloadable resources description.

**20-sitemap.yaml** — CEs: header, menu, text. Prompts: sitemap introduction text.

See design document for full page table. Each YAML must include the `page` block (title, slug, parent, nav_position) and `content_elements` with type + prompt.

**Important prompt guidelines:**
- Every prompt must contain `{company}` placeholder
- Prompts should specify length (e.g., "3-4 Sätze", "6-8 Fragen")
- Prompts should specify format when needed ("als Markdown-Liste", "als Tabelle")
- Prompts for legal pages should note "Verwende Platzhalter-Daten"

**Step 2: Verify all 20 files load correctly**

Run: `.venv/bin/python -c "from t3_content_library.loader import load_all_structures; pages = load_all_structures('config/structure'); print(f'{len(pages)} pages loaded'); [print(f'  {p[\"page\"][\"title\"]}') for p in pages]"`
Expected: `20 pages loaded` with all titles listed.

**Step 3: Commit**

```bash
git add config/structure/
git commit -m "feat: add all 20 page structure definitions"
```

---

### Task 7: Integration Test (End-to-End)

**Files:**
- Create: `tests/test_integration.py`

**Step 1: Write the integration test**

Create `tests/test_integration.py`:

```python
import os
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from t3_content_library.cli import main


def _make_mock_response(text: str):
    mock_response = MagicMock()
    mock_block = MagicMock()
    mock_block.text = text
    mock_response.content = [mock_block]
    return mock_response


def test_full_generation_with_mocked_api(tmp_path):
    """End-to-end: all 20 pages generate correctly with mocked API."""
    with patch("t3_content_library.generator.anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = _make_mock_response(
            "Generierter Beispielinhalt für die Webseite."
        )

        runner = CliRunner()
        result = runner.invoke(
            main,
            input=f"Restaurant La Bella Vista München\n{tmp_path}\n",
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"

        md_files = sorted(tmp_path.rglob("*.md"))
        assert len(md_files) == 20, f"Expected 20 files, got {len(md_files)}: {md_files}"

        # Verify each file has frontmatter and CE annotations
        for md_file in md_files:
            content = md_file.read_text(encoding="utf-8")
            assert content.startswith("---\n"), f"{md_file.name} missing frontmatter"
            assert "<!-- CE:" in content, f"{md_file.name} missing CE annotation"
            assert "title:" in content, f"{md_file.name} missing title in frontmatter"


def test_output_directory_structure(tmp_path):
    """Output files are in a slugified subdirectory."""
    with patch("t3_content_library.generator.anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = _make_mock_response("Inhalt.")

        runner = CliRunner()
        result = runner.invoke(
            main,
            input=f"Müller & Söhne GmbH\n{tmp_path}\n",
        )

        assert result.exit_code == 0
        subdirs = [d for d in tmp_path.iterdir() if d.is_dir()]
        assert len(subdirs) == 1
        assert "müller" in subdirs[0].name or "muller" in subdirs[0].name
```

**Step 2: Run integration test**

Run: `.venv/bin/python -m pytest tests/test_integration.py -v`
Expected: 2 tests PASS

**Step 3: Run full test suite**

Run: `.venv/bin/python -m pytest tests/ -v`
Expected: All tests PASS (loader: 3, generator: 2, renderer: 2, cli: 2, integration: 2 = ~11 tests)

**Step 4: Commit**

```bash
git add tests/test_integration.py
git commit -m "test: add end-to-end integration test"
```

---

### Task 8: Manual Smoke Test

**Step 1: Set up API key**

Run: `cp .env.example .env` and add a real `ANTHROPIC_API_KEY`.

**Step 2: Run the generator for real**

Run: `.venv/bin/python generate.py`

Enter: `Italienisches Restaurant La Bella Vista in München`
Output dir: `./output`

Expected: 20 files generated in `./output/italienisches-restaurant-la-bella-vista-in-munchen/`

**Step 3: Verify a few output files**

Read 2-3 generated files and verify:
- YAML frontmatter is valid
- CE annotations are correct
- Content is German, thematic, professional
- No API errors or empty content

**Step 4: Final commit if any adjustments needed**

```bash
git add -A
git commit -m "fix: adjustments from manual smoke test"
```
