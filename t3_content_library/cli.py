import json
import os
import re
import threading
import time

import anthropic
import click
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

from t3_content_library.loader import load_all_structures
from t3_content_library.generator import generate_content_for_page, PRICING
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
@click.option(
    "--parallel",
    default=5,
    help="Anzahl paralleler Generierungen (Standard: 5)",
)
@click.option(
    "--set",
    "page_set",
    type=click.Choice(["small", "medium", "full"], case_sensitive=False),
    default="full",
    help="Seitenumfang: small (8), medium (15), full (20, Standard)",
)
@click.option(
    "--jsonl",
    is_flag=True,
    default=False,
    help="JSONL output for machine consumption (used by backend)",
)
def main(company: str, output_dir: str, parallel: int, page_set: str, jsonl: bool):
    """Generiert TYPO3-Beispielseiten mit Content von Claude."""
    load_dotenv()

    structure_dir = os.path.join(os.path.dirname(__file__), "..", "config", "structure")
    structures = load_all_structures(structure_dir, page_set=page_set)

    if not structures:
        click.echo("Keine Seitenstrukturen gefunden in config/structure/")
        raise SystemExit(1)

    slug = slugify(company)
    dest = os.path.join(output_dir, slug)
    os.makedirs(dest, exist_ok=True)

    total = len(structures)
    lock = threading.Lock()
    counter = [0]
    total_input_tokens = [0]
    total_output_tokens = [0]
    client = anthropic.Anthropic()
    start_time = time.time()

    def emit(data):
        if jsonl:
            click.echo(json.dumps(data, ensure_ascii=False))
        else:
            if data.get("event") == "page_done":
                click.echo(f"[{data['done']}/{data['total']}] {data['title']} ok")
            elif data.get("event") == "start":
                click.echo(f"Generiere {data['total']} Seiten für \"{company}\" ({parallel}x parallel)...")
            elif data.get("event") == "complete":
                cost = data['cost_usd']
                click.echo(
                    f"\n{data['total']} Seiten generiert in {dest}/"
                    f"\nTokens: {data['total_input_tokens']:,} input / {data['total_output_tokens']:,} output"
                    f"\nKosten: ${cost:.4f} | Dauer: {data['duration_sec']:.1f}s"
                )

    emit({"event": "start", "total": total, "parallel": parallel})

    def process_page(structure):
        page = structure["page"]
        content_elements, usage = generate_content_for_page(structure, company, client=client)
        markdown = render_page(page, content_elements, company)

        filename = f"{page['slug'].strip('/').replace('/', '-') or 'index'}.md"
        filepath = os.path.join(dest, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(markdown)

        with lock:
            counter[0] += 1
            total_input_tokens[0] += usage["input_tokens"]
            total_output_tokens[0] += usage["output_tokens"]
            emit({
                "event": "page_done",
                "title": page["title"],
                "done": counter[0],
                "total": total,
                "input_tokens": usage["input_tokens"],
                "output_tokens": usage["output_tokens"],
            })

    with ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = [executor.submit(process_page, s) for s in structures]
        for future in as_completed(futures):
            future.result()

    duration = time.time() - start_time
    cost = (
        total_input_tokens[0] / 1_000_000 * PRICING["input"]
        + total_output_tokens[0] / 1_000_000 * PRICING["output"]
    )

    emit({
        "event": "complete",
        "total": total,
        "total_input_tokens": total_input_tokens[0],
        "total_output_tokens": total_output_tokens[0],
        "cost_usd": round(cost, 6),
        "duration_sec": round(duration, 1),
    })
