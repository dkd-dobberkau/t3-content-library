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
    """Generiert TYPO3-Beispielseiten mit Content von Claude."""
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

        click.echo(" ok")

    click.echo(f"\n{total} Seiten generiert in {dest}/")
