import re

import anthropic


SYSTEM_PROMPT = """Du bist ein Content-Autor für eine Unternehmenswebsite.
Schreibe natürlichen, professionellen deutschen Content.
Antworte NUR mit dem angeforderten Content, ohne Erklärungen oder Kommentare.
Verwende Markdown-Formatierung wo passend."""

# Pricing per million tokens (Claude Sonnet 4.5)
PRICING = {
    "input": 3.00,
    "output": 15.00,
}


def generate_content_for_page(
    structure: dict,
    company_description: str,
    model: str = "claude-sonnet-4-5-20250929",
    client: anthropic.Anthropic | None = None,
) -> tuple[list[dict], dict]:
    """Generate content for all content elements of a page in a single API call.

    Returns (content_elements, usage) where usage contains token counts.
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

    return results, usage
