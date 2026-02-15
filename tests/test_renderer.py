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


def test_render_page_with_image_keywords():
    page_meta = {"title": "Über uns", "slug": "ueber-uns", "parent": "/", "nav_position": 2}
    content_elements = [{"type": "header", "content": "# Über uns"}]
    keywords = ["business team professional", "modern office interior"]

    result = render_page(page_meta, content_elements, "TestFirma", image_keywords=keywords)

    assert "images:" in result
    assert "search_keywords:" in result
    assert "business team professional" in result
    assert "modern office interior" in result


def test_render_page_without_image_keywords():
    page_meta = {"title": "Test", "slug": "test", "parent": "/", "nav_position": 1}
    content_elements = [{"type": "header", "content": "# Test"}]

    result = render_page(page_meta, content_elements, "TestFirma")

    assert "images:" not in result
    assert "search_keywords:" not in result
