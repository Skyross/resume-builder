"""Tests for generate_resume module."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.generate_resume import (
    TEMPLATES,
    apply_pdf_metadata,
    generate_resume_pdf,
    list_templates,
    load_resume_data,
    main,
    parse_metadata,
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


class TestParseMetadata:
    """Tests for parse_metadata function."""

    def test_parse_valid_metadata(self) -> None:
        """Test parsing valid key=value pairs."""
        meta_args = ["title=My Resume", "author=John Doe"]
        result = parse_metadata(meta_args)
        assert result is not None
        assert result["title"] == "My Resume"
        assert result["author"] == "John Doe"

    def test_parse_metadata_with_equals_in_value(self) -> None:
        """Test that values can contain equals signs."""
        meta_args = ["subject=Test = Subject"]
        result = parse_metadata(meta_args)
        assert result is not None
        assert result["subject"] == "Test = Subject"

    def test_parse_metadata_strips_whitespace(self) -> None:
        """Test that keys and values are stripped."""
        meta_args = ["  title  =  Spaced Title  "]
        result = parse_metadata(meta_args)
        assert result is not None
        assert result["title"] == "Spaced Title"

    def test_parse_metadata_none_input(self) -> None:
        """Test that None input returns None."""
        result = parse_metadata(None)
        assert result is None

    def test_parse_metadata_empty_list(self) -> None:
        """Test that empty list returns None."""
        result = parse_metadata([])
        assert result is None

    def test_parse_metadata_invalid_format_warning(self, capsys) -> None:
        """Test that invalid format prints warning."""
        meta_args = ["invalid_no_equals"]
        result = parse_metadata(meta_args)
        captured = capsys.readouterr()
        assert "Warning:" in captured.out
        assert "invalid_no_equals" in captured.out
        assert result is None

    def test_parse_metadata_mixed_valid_invalid(self, capsys) -> None:
        """Test mixed valid and invalid entries."""
        meta_args = ["title=Valid", "invalid", "author=Also Valid"]
        result = parse_metadata(meta_args)
        assert result is not None
        assert result["title"] == "Valid"
        assert result["author"] == "Also Valid"
        captured = capsys.readouterr()
        assert "Warning:" in captured.out


class TestApplyPdfMetadata:
    """Tests for apply_pdf_metadata function."""

    @pytest.mark.slow
    def test_apply_standard_metadata(self, template_dir: Path, sample_resume_data: dict, tmp_path: Path) -> None:
        """Test applying standard PDF metadata fields."""
        output_path = tmp_path / "test_meta.pdf"

        # First generate a PDF
        generate_resume_pdf(
            template_dir,
            TEMPLATES["default"],
            sample_resume_data,
            str(output_path),
        )

        # Apply metadata
        metadata = {
            "title": "Test Title",
            "author": "Test Author",
            "subject": "Test Subject",
            "keywords": "test,keywords",
        }
        apply_pdf_metadata(output_path, metadata)

        # Verify PDF is still valid
        assert output_path.exists()
        with output_path.open("rb") as f:
            assert f.read(4) == b"%PDF"

    @pytest.mark.slow
    def test_apply_custom_metadata_key(self, template_dir: Path, sample_resume_data: dict, tmp_path: Path) -> None:
        """Test applying custom (non-standard) metadata keys."""
        output_path = tmp_path / "test_custom_meta.pdf"

        generate_resume_pdf(
            template_dir,
            TEMPLATES["default"],
            sample_resume_data,
            str(output_path),
        )

        # Apply custom metadata key not in standard mapping
        metadata = {"customfield": "Custom Value"}
        apply_pdf_metadata(output_path, metadata)

        assert output_path.exists()


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

    @pytest.mark.slow
    def test_main_verbose_output(self, monkeypatch, capsys, sample_data_file: Path, tmp_path: Path) -> None:
        """Test verbose flag produces additional output."""
        output_path = tmp_path / "verbose_output.pdf"
        monkeypatch.setattr(
            "sys.argv",
            [
                "generate_resume.py",
                "-d",
                str(sample_data_file),
                "-o",
                str(output_path),
                "-v",
            ],
        )
        result = main()
        assert result == 0
        captured = capsys.readouterr()
        assert "Data file:" in captured.out
        assert "Template:" in captured.out
        assert "Output:" in captured.out

    @pytest.mark.slow
    def test_main_verbose_with_metadata(self, monkeypatch, capsys, sample_data_file: Path, tmp_path: Path) -> None:
        """Test verbose output includes metadata information."""
        output_path = tmp_path / "verbose_meta.pdf"
        monkeypatch.setattr(
            "sys.argv",
            [
                "generate_resume.py",
                "-d",
                str(sample_data_file),
                "-o",
                str(output_path),
                "-v",
                "-m",
                "title=Test Resume",
            ],
        )
        result = main()
        assert result == 0
        captured = capsys.readouterr()
        assert "Metadata:" in captured.out

    @pytest.mark.slow
    def test_main_with_metadata(self, monkeypatch, capsys, sample_data_file: Path, tmp_path: Path) -> None:
        """Test generating PDF with metadata."""
        output_path = tmp_path / "with_meta.pdf"
        monkeypatch.setattr(
            "sys.argv",
            [
                "generate_resume.py",
                "-d",
                str(sample_data_file),
                "-o",
                str(output_path),
                "-m",
                "author=John Doe",
                "-m",
                "title=My Resume",
            ],
        )
        result = main()
        assert result == 0
        captured = capsys.readouterr()
        assert "Applying PDF metadata" in captured.out

    @pytest.mark.slow
    def test_main_with_hidden_text(self, monkeypatch, sample_data_file: Path, tmp_path: Path) -> None:
        """Test generating PDF with hidden text."""
        output_path = tmp_path / "hidden_text.pdf"
        monkeypatch.setattr(
            "sys.argv",
            [
                "generate_resume.py",
                "-d",
                str(sample_data_file),
                "-o",
                str(output_path),
                "-s",
                "extra keywords for ATS",
            ],
        )
        result = main()
        assert result == 0
        assert output_path.exists()

    def test_main_template_not_found(self, monkeypatch, capsys, sample_data_file: Path, tmp_path: Path) -> None:
        """Test error when template file doesn't exist."""
        output_path = tmp_path / "output.pdf"
        # Patch TEMPLATES to point to nonexistent file
        with patch.dict(
            "src.generate_resume.TEMPLATES",
            {"default": "nonexistent_template.html"},
        ):
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
        assert result == 1
        captured = capsys.readouterr()
        assert "Template not found" in captured.out

    def test_main_pdf_generation_error(self, monkeypatch, capsys, sample_data_file: Path, tmp_path: Path) -> None:
        """Test error handling when PDF generation fails."""
        output_path = tmp_path / "output.pdf"
        with patch(
            "src.generate_resume.generate_resume_pdf",
            side_effect=Exception("PDF generation failed"),
        ):
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
        assert result == 1
        captured = capsys.readouterr()
        assert "Error generating PDF" in captured.out
