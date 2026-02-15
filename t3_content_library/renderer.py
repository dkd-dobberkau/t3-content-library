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
