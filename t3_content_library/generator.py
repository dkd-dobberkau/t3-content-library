import os
import re

import anthropic


DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")

SYSTEM_PROMPT = """Du bist ein Content-Autor für eine Unternehmenswebsite.
Schreibe natürlichen, professionellen deutschen Content.
Antworte NUR mit dem angeforderten Content, ohne Erklärungen oder Kommentare.
Verwende Markdown-Formatierung wo passend.
Wenn nach Bild-Suchbegriffen gefragt, liefere passende englische Suchbegriffe für Stockfoto-Plattformen wie Unsplash."""

# Pricing per million tokens (Claude Sonnet 4.5)
PRICING = {
    "input": 3.00,
    "output": 15.00,
}


def generate_content_for_page(
    structure: dict,
    company_description: str,
    model: str = DEFAULT_MODEL,
    client: anthropic.Anthropic | None = None,
) -> tuple[list[dict], dict, list[str]]:
    """Generate content for all content elements of a page in a single API call.

    Returns (content_elements, usage, image_keywords) where usage contains
    token counts and image_keywords is a list of English search terms for
    stock photo platforms.
    """
    if client is None:
        client = anthropic.Anthropic()

    content_elements = structure["content_elements"]
    page_title = structure["page"]["title"]

    # Build batched prompt for all CEs
    parts = []
    for i, ce in enumerate(content_elements, 1):
        prompt = ce["prompt"].replace("{company}", company_description)
        parts.append(f"[CE:{i}] {prompt}")

    batched_prompt = (
        f"Generiere Content für die Seite \"{page_title}\".\n\n"
        f"Erstelle die folgenden {len(content_elements)} Content-Elemente. "
        f"Trenne jedes Element mit einer eigenen Zeile die NUR ===CE:N=== enthält "
        f"(N = Nummer des Elements). Beginne mit ===CE:1===\n\n"
        + "\n".join(parts)
        + "\n\nGanz am Ende, nach allen Content-Elementen, füge eine Zeile ===IMAGES=== ein. "
        "Darunter liste 1-3 englische Suchbegriffe für Stockfoto-Plattformen (z.B. Unsplash), "
        "die zum Thema und Inhalt dieser Seite passen. "
        "Ein Suchbegriff pro Zeile, ohne Nummerierung oder Aufzählungszeichen. "
        "Die Begriffe sollen spezifisch und beschreibend sein (z.B. 'italian restaurant interior warm lighting' "
        "statt nur 'restaurant')."
    )

    response = client.messages.create(
        model=model,
        max_tokens=4096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": batched_prompt}],
    )

    raw = response.content[0].text

    usage = {
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
    }

    # Split off ===IMAGES=== section
    image_keywords = []
    if "===IMAGES===" in raw:
        raw, images_section = raw.split("===IMAGES===", 1)
        raw = raw.strip()
        image_keywords = [
            line.strip()
            for line in images_section.strip().splitlines()
            if line.strip()
        ]

    # Parse response by ===CE:N=== markers
    sections = re.split(r"===CE:\d+===\s*", raw)
    sections = [s.strip() for s in sections if s.strip()]

    results = []
    for i, ce in enumerate(content_elements):
        content_text = sections[i] if i < len(sections) else ""
        result = {"type": ce["type"], "content": content_text}
        for key in ("subtype", "image", "image_position"):
            if key in ce:
                result[key] = ce[key]
        results.append(result)

    return results, usage, image_keywords
