import os
from unittest.mock import patch, MagicMock
from click.testing import CliRunner
from t3_content_library.cli import main

MOCK_USAGE = {"input_tokens": 100, "output_tokens": 200}


def test_cli_generates_output_files(tmp_path):
    """CLI creates markdown files in output directory."""
    structure_dir = os.path.join(os.path.dirname(__file__), "..", "config", "structure")

    with patch("t3_content_library.cli.generate_content_for_page") as mock_gen:
        mock_gen.return_value = (
            [
                {"type": "header", "content": "# Test Seite"},
                {"type": "text", "content": "Beispieltext."},
            ],
            MOCK_USAGE,
        )

        runner = CliRunner()
        result = runner.invoke(
            main,
            input=f"Testfirma GmbH\n{tmp_path}\n",
        )

        assert result.exit_code == 0
        assert "generiert" in result.output.lower() or "generated" in result.output.lower()

        # At least one .md file should exist
        md_files = list(tmp_path.rglob("*.md"))
        assert len(md_files) >= 1


def test_cli_shows_progress():
    """CLI shows progress like [1/20]."""
    with patch("t3_content_library.cli.generate_content_for_page") as mock_gen:
        mock_gen.return_value = (
            [{"type": "header", "content": "# Test"}],
            MOCK_USAGE,
        )

        runner = CliRunner()
        result = runner.invoke(
            main,
            input="Testfirma\n/tmp/t3test\n",
        )

        assert "[1/" in result.output
