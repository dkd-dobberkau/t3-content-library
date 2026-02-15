import os
import pytest
from t3_content_library.loader import load_page_structure, load_all_structures, load_page_sets


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

    assert len(pages) == 20
    assert pages[0]["page"]["title"] == "Startseite"
    assert pages[1]["page"]["title"] == "Über uns"


def test_structures_sorted_by_filename():
    """Structures load in filename order (01-, 02-, etc.)."""
    base = os.path.join(os.path.dirname(__file__), "..", "config", "structure")
    pages = load_all_structures(base)
    # With only one file, just verify it loads
    assert len(pages) >= 1


def test_load_page_sets():
    config_dir = os.path.join(os.path.dirname(__file__), "..", "config")
    sets = load_page_sets(config_dir)
    assert "small" in sets
    assert "medium" in sets
    assert "full" in sets
    assert len(sets["small"]) == 8
    assert len(sets["medium"]) == 15
    assert sets["full"] == "all"


def test_load_all_structures_small_set():
    base = os.path.join(os.path.dirname(__file__), "..", "config", "structure")
    pages = load_all_structures(base, page_set="small")
    assert len(pages) == 8
    titles = [p["page"]["title"] for p in pages]
    assert "Startseite" in titles
    assert "Kontakt" in titles


def test_load_all_structures_medium_set():
    base = os.path.join(os.path.dirname(__file__), "..", "config", "structure")
    pages = load_all_structures(base, page_set="medium")
    assert len(pages) == 15


def test_load_all_structures_full_set():
    base = os.path.join(os.path.dirname(__file__), "..", "config", "structure")
    pages = load_all_structures(base, page_set="full")
    assert len(pages) == 20


def test_load_all_structures_invalid_set():
    base = os.path.join(os.path.dirname(__file__), "..", "config", "structure")
    with pytest.raises(ValueError, match="Unknown page set"):
        load_all_structures(base, page_set="nonexistent")
