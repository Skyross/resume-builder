"""Tests for generate_resume module."""

import json
from pathlib import Path

import pytest

from src.generate_resume import (
    TEMPLATES,
    generate_resume_pdf,
    list_templates,
    load_resume_data,
    main,
    render_template,
)


class TestLoadResumeData:
    """Tests for load_resume_data function."""

    def test_load_valid_json(self, sample_data_file: Path) -> None:
        """Test loading a valid JSON file."""
        data = load_resume_data(str(sample_data_file))
        assert data["name"] == "Test Person"
        assert data["title"] == "Software Engineer"
        assert "contact" in data
        assert "experience" in data

    def test_load_nonexistent_file(self, tmp_path: Path) -> None:
        """Test loading a file that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_resume_data(str(tmp_path / "nonexistent.json"))

    def test_load_invalid_json(self, invalid_json_file: Path) -> None:
        """Test loading a file with invalid JSON."""
        with pytest.raises(json.JSONDecodeError):
            load_resume_data(str(invalid_json_file))


class TestRenderTemplate:
    """Tests for render_template function."""

    def test_render_default_template(self, template_dir: Path, sample_resume_data: dict) -> None:
        """Test rendering the default template."""
        html = render_template(template_dir, TEMPLATES["default"], sample_resume_data)
        assert "Test Person" in html
        assert "Software Engineer" in html
        assert "test@example.com" in html

    def test_render_all_templates(self, template_dir: Path, sample_resume_data: dict) -> None:
        """Test that all templates can be rendered without errors."""
        for template_name, template_file in TEMPLATES.items():
            html = render_template(template_dir, template_file, sample_resume_data)
            assert html, f"Template {template_name} rendered empty content"
            assert sample_resume_data["name"] in html


class TestGenerateResumePdf:
    """Tests for generate_resume_pdf function."""

    @pytest.mark.slow
    def test_generate_pdf(self, template_dir: Path, sample_resume_data: dict, tmp_path: Path) -> None:
        """Test generating a PDF file."""
        output_path = tmp_path / "test_output.pdf"

        generate_resume_pdf(
            template_dir,
            TEMPLATES["default"],
            sample_resume_data,
            str(output_path),
        )

        assert output_path.exists()
        assert output_path.stat().st_size > 0
        # PDF files start with %PDF
        with output_path.open("rb") as f:
            assert f.read(4) == b"%PDF"

    @pytest.mark.slow
    def test_generate_pdf_creates_output_dir(
        self, template_dir: Path, sample_resume_data: dict, tmp_path: Path
    ) -> None:
        """Test that output directory is created if it doesn't exist."""
        output_path = tmp_path / "new_dir" / "nested" / "output.pdf"

        generate_resume_pdf(
            template_dir,
            TEMPLATES["default"],
            sample_resume_data,
            str(output_path),
        )

        assert output_path.exists()


class TestListTemplates:
    """Tests for list_templates function."""

    def test_list_templates_prints_output(self, capsys) -> None:
        """Test that list_templates prints available templates."""
        list_templates()
        captured = capsys.readouterr()
        assert "Available templates:" in captured.out
        for template_name in TEMPLATES:
            assert template_name in captured.out


class TestTemplatesDict:
    """Tests for TEMPLATES configuration."""

    def test_all_templates_exist(self, template_dir: Path) -> None:
        """Test that all configured templates exist as files."""
        for template_name, template_file in TEMPLATES.items():
            template_path = template_dir / template_file
            assert template_path.exists(), f"Template {template_name} file not found: {template_file}"

    def test_templates_are_html(self) -> None:
        """Test that all templates are HTML files."""
        for template_file in TEMPLATES.values():
            assert template_file.endswith(".html")


class TestMain:
    """Tests for main CLI function."""

    def test_main_list_templates(self, monkeypatch, capsys) -> None:
        """Test --list-templates flag."""
        monkeypatch.setattr("sys.argv", ["generate_resume.py", "--list-templates"])
        result = main()
        assert result == 0
        captured = capsys.readouterr()
        assert "Available templates:" in captured.out

    def test_main_missing_data_file(self, monkeypatch, tmp_path: Path) -> None:
        """Test error handling when data file doesn't exist."""
        nonexistent = tmp_path / "nonexistent.json"
        monkeypatch.setattr("sys.argv", ["generate_resume.py", "-d", str(nonexistent)])
        result = main()
        assert result == 1

    def test_main_invalid_json(self, monkeypatch, invalid_json_file: Path) -> None:
        """Test error handling for invalid JSON."""
        monkeypatch.setattr("sys.argv", ["generate_resume.py", "-d", str(invalid_json_file)])
        result = main()
        assert result == 1

    @pytest.mark.slow
    def test_main_successful_generation(self, monkeypatch, sample_data_file: Path, tmp_path: Path) -> None:
        """Test successful PDF generation via main()."""
        output_path = tmp_path / "output.pdf"
        monkeypatch.setattr(
            "sys.argv",
            [
                "generate_resume.py",
                "-d",
                str(sample_data_file),
                "-o",
                str(output_path),
            ],
        )
        result = main()
        assert result == 0
        assert output_path.exists()
