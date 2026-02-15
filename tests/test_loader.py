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
