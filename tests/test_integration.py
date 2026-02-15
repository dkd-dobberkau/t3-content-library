import os
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from t3_content_library.cli import main


def _make_mock_response(text: str):
    mock_response = MagicMock()
    mock_block = MagicMock()
    mock_block.text = text
    mock_response.content = [mock_block]
    mock_response.usage = MagicMock(input_tokens=100, output_tokens=200)
    return mock_response


def test_full_generation_with_mocked_api(tmp_path):
    """End-to-end: all 20 pages generate correctly with mocked API."""
    with patch("t3_content_library.cli.anthropic") as mock_cli_anthropic, \
         patch("t3_content_library.generator.anthropic") as mock_gen_anthropic:
        mock_client = MagicMock()
        mock_cli_anthropic.Anthropic.return_value = mock_client
        mock_gen_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = _make_mock_response(
            "Generierter Beispielinhalt für die Webseite."
        )

        runner = CliRunner()
        result = runner.invoke(
            main,
            input=f"Restaurant La Bella Vista München\n{tmp_path}\n",
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"

        md_files = sorted(tmp_path.rglob("*.md"))
        assert len(md_files) == 20, f"Expected 20 files, got {len(md_files)}: {md_files}"

        # Verify each file has frontmatter and CE annotations
        for md_file in md_files:
            content = md_file.read_text(encoding="utf-8")
            assert content.startswith("---\n"), f"{md_file.name} missing frontmatter"
            assert "<!-- CE:" in content, f"{md_file.name} missing CE annotation"
            assert "title:" in content, f"{md_file.name} missing title in frontmatter"


def test_output_directory_structure(tmp_path):
    """Output files are in a slugified subdirectory."""
    with patch("t3_content_library.cli.anthropic") as mock_cli_anthropic, \
         patch("t3_content_library.generator.anthropic") as mock_gen_anthropic:
        mock_client = MagicMock()
        mock_cli_anthropic.Anthropic.return_value = mock_client
        mock_gen_anthropic.Anthropic.return_value = mock_client
        mock_client.messages.create.return_value = _make_mock_response("Inhalt.")

        runner = CliRunner()
        result = runner.invoke(
            main,
            input=f"Müller & Söhne GmbH\n{tmp_path}\n",
        )

        assert result.exit_code == 0
        subdirs = [d for d in tmp_path.iterdir() if d.is_dir()]
        assert len(subdirs) == 1
        assert "müller" in subdirs[0].name or "muller" in subdirs[0].name
