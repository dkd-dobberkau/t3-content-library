from unittest.mock import patch, MagicMock
from t3_content_library.generator import generate_content_for_page


def _make_mock_response(text: str, input_tokens: int = 100, output_tokens: int = 200):
    mock_response = MagicMock()
    mock_block = MagicMock()
    mock_block.text = text
    mock_response.content = [mock_block]
    mock_response.usage = MagicMock(input_tokens=input_tokens, output_tokens=output_tokens)
    return mock_response


def test_generate_content_for_page():
    structure = {
        "page": {"title": "Über uns", "slug": "ueber-uns", "parent": "/", "nav_position": 2},
        "content_elements": [
            {"type": "header", "prompt": "Erstelle eine Überschrift für {company}"},
            {"type": "text", "prompt": "Schreibe einen Text über {company}"},
        ],
    }

    batched_response = (
        "===CE:1===\n"
        "# Willkommen bei La Bella Vista\n"
        "===CE:2===\n"
        "Seit 2005 servieren wir authentische Küche.\n"
        "===IMAGES===\n"
        "italian restaurant interior warm lighting\n"
        "mediterranean cuisine fresh pasta\n"
        "cozy dining room candles"
    )

    with patch("t3_content_library.generator.anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = _make_mock_response(batched_response, 150, 320)

        result, usage, image_keywords = generate_content_for_page(structure, "La Bella Vista, München")

        assert len(result) == 2
        assert result[0]["type"] == "header"
        assert "Willkommen" in result[0]["content"]
        assert result[1]["type"] == "text"
        assert "2005" in result[1]["content"]
        assert mock_client.messages.create.call_count == 1
        assert usage["input_tokens"] == 150
        assert usage["output_tokens"] == 320
        assert len(image_keywords) == 3
        assert "italian restaurant interior warm lighting" in image_keywords


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

    batched_response = "===CE:1===\nToller Text."

    with patch("t3_content_library.generator.anthropic") as mock_anthropic:
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = _make_mock_response(batched_response)

        result, usage, image_keywords = generate_content_for_page(structure, "TestFirma")

        assert result[0]["image"] == "placeholder://hero.jpg"
        assert result[0]["image_position"] == "right"
        assert usage["input_tokens"] == 100
        assert usage["output_tokens"] == 200
