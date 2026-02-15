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
