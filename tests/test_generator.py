from unittest.mock import patch, MagicMock
from t3_content_library.generator import generate_content_for_page


def _make_mock_response(text: str):
    mock_response = MagicMock()
    mock_block = MagicMock()
    mock_block.text = text
    mock_response.content = [mock_block]
    return mock_response


def test_generate_content_for_page():
    structure = {
        "page": {"title": "Über uns", "slug": "ueber-uns", "parent": "/", "nav_position": 2},
        "content_elements": [
            {"type": "header", "prompt": "Erstelle eine Überschrift für {company}"},
            {"type": "text", "prompt": "Schreibe einen Text über {company}"},
        ],
    }

    with patch("t3_content_library.generator.anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.side_effect = [
            _make_mock_response("# Willkommen bei La Bella Vista"),
            _make_mock_response("Seit 2005 servieren wir authentische Küche."),
        ]

        result = generate_content_for_page(structure, "La Bella Vista, München")

        assert len(result) == 2
        assert result[0]["type"] == "header"
        assert "Willkommen" in result[0]["content"]
        assert result[1]["type"] == "text"
        assert "2005" in result[1]["content"]
        assert mock_client.messages.create.call_count == 2


def test_content_element_preserves_metadata():
    """Image paths, positions etc. are passed through to results."""
    structure = {
        "page": {"title": "Test", "slug": "test", "parent": "/", "nav_position": 1},
        "content_elements": [
            {
                "type": "textmedia",
                "prompt": "Text über {company}",
                "image": "placeholder://hero.jpg",
                "image_position": "right",
            },
        ],
    }

    with patch("t3_content_library.generator.anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = _make_mock_response("Toller Text.")

        result = generate_content_for_page(structure, "TestFirma")

        assert result[0]["image"] == "placeholder://hero.jpg"
        assert result[0]["image_position"] == "right"
