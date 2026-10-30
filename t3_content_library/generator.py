import os
import re

import anthropic


DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5-5")
# Thinking counts toward max_tokens, so the limit must cover more than the content.
MAX_TOKENS = 16000
# ANTHROPIC_MODEL can select older models, which reject these options.
SONNET_5_5_OPTIONS = {
    "output_config": {"effort": "low"},
    "betas": ["server-side-fallback-2026-07-01"],
    "fallbacks": "default",
}



class GenerationError(RuntimeError):
    """Claude returned no usable text."""


def _response_text(response) -> str:
    """Read text by block type, responses can start with a thinking block."""
    if response.stop_reason == "refusal":
        raise GenerationError("Claude declined the request")

    text = "".join(block.text for block in response.content if block.type == "text")
    if not text.strip():
        raise GenerationError(f"No text in response (stop_reason: {response.stop_reason})")
    return text


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

    response = client.beta.messages.create(
        model=model,
        max_tokens=MAX_TOKENS,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": batched_prompt}],
        **(SONNET_5_5_OPTIONS if model == "claude-sonnet-5-5" else {}),
    )

    raw = _response_text(response)

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
