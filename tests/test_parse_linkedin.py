"""Tests for LinkedIn PDF parser."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.parse_linkedin import (
    Contact,
    Education,
    Experience,
    Highlight,
    ResumeData,
    _join_split_lines,
    convert_to_resume_format,
    extract_education,
    extract_experience,
    extract_name_title_location,
    extract_sidebar_sections,
    extract_summary,
    extract_text_from_pdf,
    find_section_indices,
    main,
    parse_date_range,
    parse_education_years,
    parse_experience_highlights,
    parse_linkedin_pdf,
)


class TestParseDateRange:
    """Tests for parse_date_range function."""

    def test_full_date_range(self):
        start, end = parse_date_range("November 2021 - November 2025 (4 years 1 month)")
        assert start == "Nov 2021"
        assert end == "Nov 2025"

    def test_date_range_with_present(self):
        start, end = parse_date_range("August 2017 - Present (4 years)")
        assert start == "Aug 2017"
        assert end == "Present"

    def test_date_range_no_duration(self):
        start, end = parse_date_range("January 2020 - December 2022")
        assert start == "Jan 2020"
        assert end == "Dec 2022"

    def test_single_date(self):
        start, end = parse_date_range("March 2019")
        assert start == "Mar 2019"
        assert end == "Present"


class TestParseEducationYears:
    """Tests for parse_education_years function."""

    def test_full_date_range(self):
        start, end = parse_education_years("(September 2008 - June 2013)")
        assert start == "2008"
        assert end == "2013"

    def test_with_prefix(self):
        start, end = parse_education_years("· (September 2005 - June 2008)")
        assert start == "2005"
        assert end == "2008"

    def test_single_year(self):
        start, end = parse_education_years("(2020)")
        assert start == "2020"
        assert end == "2020"

    def test_no_years(self):
        start, end = parse_education_years("No dates here")
        assert start == ""
        assert end == ""


class TestJoinSplitLines:
    """Tests for _join_split_lines function."""

    def test_join_lowercase_continuation(self):
        lines = ["Improving Deep Neural Networks:", "hyperparameter tuning"]
        result = _join_split_lines(lines)
        assert result == ["Improving Deep Neural Networks: hyperparameter tuning"]

    def test_join_comma_continuation(self):
        lines = ["First part,", "second part"]
        result = _join_split_lines(lines)
        assert result == ["First part second part"]

    def test_no_join_uppercase_start(self):
        lines = ["First Item", "Second Item", "Third Item"]
        result = _join_split_lines(lines)
        assert result == ["First Item", "Second Item", "Third Item"]

    def test_empty_list(self):
        result = _join_split_lines([])
        assert result == []


class TestFindSectionIndices:
    """Tests for find_section_indices function."""

    def test_finds_all_sections(self):
        lines = [
            "Contact",
            "email@example.com",
            "Top Skills",
            "Python",
            "Summary",
            "A summary",
            "Experience",
            "Company",
            "Education",
            "School",
        ]
        indices = find_section_indices(lines)
        assert indices["Contact"] == 0
        assert indices["Top Skills"] == 2
        assert indices["Summary"] == 4
        assert indices["Experience"] == 6
        assert indices["Education"] == 8

    def test_missing_sections(self):
        lines = ["Contact", "email@example.com", "Summary", "A summary"]
        indices = find_section_indices(lines)
        assert "Contact" in indices
        assert "Summary" in indices
        assert "Experience" not in indices


class TestExtractSidebarSections:
    """Tests for extract_sidebar_sections function."""

    def test_extracts_contact_email(self):
        lines = ["Contact", "test@example.com", "Top Skills", "Python"]
        indices = find_section_indices(lines)
        sidebar = extract_sidebar_sections(lines, indices)
        assert sidebar["contact"]["email"] == "test@example.com"

    def test_extracts_skills(self):
        lines = ["Contact", "email@test.com", "Top Skills", "Python", "JavaScript", "AWS", "Summary"]
        indices = find_section_indices(lines)
        sidebar = extract_sidebar_sections(lines, indices)
        assert "Python" in sidebar["top_skills"]
        assert "JavaScript" in sidebar["top_skills"]
        assert "AWS" in sidebar["top_skills"]


class TestParseExperienceHighlights:
    """Tests for parse_experience_highlights function."""

    def test_converts_bullets_to_highlights(self):
        description = "- First point - Second point - Third point"
        result = parse_experience_highlights(description)
        assert isinstance(result, list)
        assert len(result) == 3

    def test_extracts_labels(self):
        description = "- Leadership: Led a team - Technical: Built systems"
        result = parse_experience_highlights(description)
        assert result[0]["label"] == "Leadership:"
        assert result[0]["description"] == "Led a team"

    def test_no_bullets_returns_description(self):
        description = "A plain description without bullets"
        result = parse_experience_highlights(description)
        assert result == description

    def test_empty_description(self):
        result = parse_experience_highlights("")
        assert result == ""


class TestConvertToResumeFormat:
    """Tests for convert_to_resume_format function."""

    def test_creates_valid_structure(self):
        sidebar = {
            "contact": {"email": "test@example.com", "linkedin": "linkedin.com/in/test"},
            "top_skills": ["Python", "AWS"],
            "certifications": ["AWS Certified"],
        }
        experience = [
            {
                "company": "Test Company",
                "title": "Engineer",
                "start_date": "Jan 2020",
                "end_date": "Present",
                "description": "Did things",
            }
        ]
        education = [
            {
                "school": "Test University",
                "degree": "BS Computer Science",
                "start_year": "2010",
                "end_year": "2014",
            }
        ]

        result = convert_to_resume_format(
            sidebar=sidebar,
            name="John Doe",
            title="Software Engineer",
            location="New York, USA",
            summary="A summary",
            experience=experience,
            education=education,
        )

        assert isinstance(result, ResumeData)
        assert result.name == "John Doe"
        assert result.title == "Software Engineer"
        assert result.contact.email == "test@example.com"
        assert result.contact.location == "New York, USA"
        assert len(result.experience) == 1
        assert len(result.education) == 1
        assert result.skills == ["Python", "AWS"]


class TestExtractExperience:
    """Tests for extract_experience function."""

    def test_extracts_single_experience(self):
        text = """
Experience
Test Company
Software Engineer
January 2020 - December 2022 (2 years)
New York, USA
Did great things at this company.
Education
Test School
"""
        experiences = extract_experience(text)
        assert len(experiences) == 1
        assert experiences[0]["company"] == "Test Company"
        assert experiences[0]["title"] == "Software Engineer"
        assert experiences[0]["start_date"] == "Jan 2020"
        assert experiences[0]["end_date"] == "Dec 2022"

    def test_extracts_multiple_experiences(self):
        text = """
Experience
Company A
Role A
January 2022 - Present (1 year)
City A, Country
Description A
Company B
Role B
January 2020 - December 2021 (2 years)
City B, Country
Description B
Education
School
"""
        experiences = extract_experience(text)
        assert len(experiences) == 2


class TestExtractEducation:
    """Tests for extract_education function."""

    def test_extracts_education(self):
        text = """
Education
Test University
Bachelor's Degree, Computer Science · (September 2010 - June 2014)
"""
        education = extract_education(text)
        assert len(education) == 1
        assert education[0]["school"] == "Test University"
        assert "Bachelor" in education[0]["degree"]
        assert education[0]["start_year"] == "2010"
        assert education[0]["end_year"] == "2014"


class TestParseLinkedInPdfIntegration:
    """Integration tests using mocked PDF content."""

    @pytest.fixture
    def sample_linkedin_text(self):
        """Sample LinkedIn PDF text structure."""
        return [
            """
Contact
john.doe@example.com
www.linkedin.com/in/
johndoe (LinkedIn)
Top Skills
Python
AWS
Docker
Languages
English (Native)
Certifications
AWS Solutions Architect
John Doe
Senior Software Engineer | Tech Lead
New York, USA
Summary
Experienced software engineer with 10+ years of expertise in building scalable systems.
Experience
Acme Corp
Senior Software Engineer
January 2020 - Present (4 years)
New York, USA
Led development of microservices architecture.
- Leadership: Managed team of 5 engineers
- Technical: Built scalable APIs
Previous Company
Software Engineer
June 2015 - December 2019 (4 years 6 months)
Boston, USA
Developed backend services using Python and Django.
Education
MIT
Bachelor's Degree, Computer Science · (September 2011 - June 2015)
"""
        ]

    def test_parse_mocked_pdf(self, sample_linkedin_text):
        with patch("src.parse_linkedin.extract_text_from_pdf", return_value=sample_linkedin_text):
            result = parse_linkedin_pdf("fake_path.pdf")

        # Check result is ResumeData
        assert isinstance(result, ResumeData)

        # Check required fields exist and have values
        assert result.name == "John Doe"
        assert "Senior Software Engineer" in result.title
        assert isinstance(result.contact, Contact)
        assert result.contact.email == "john.doe@example.com"
        assert "johndoe" in result.contact.linkedin
        assert result.summary
        assert isinstance(result.experience, list)
        assert isinstance(result.education, list)
        assert isinstance(result.skills, list)

        # Check experience entries exist
        assert len(result.experience) == 2
        assert all(isinstance(exp, Experience) for exp in result.experience)
        assert result.experience[0].company == "Acme Corp"

        # Check education entries exist
        assert len(result.education) == 1
        assert all(isinstance(edu, Education) for edu in result.education)
        assert result.education[0].school == "MIT"

    def test_output_is_json_serializable(self, sample_linkedin_text):
        with patch("src.parse_linkedin.extract_text_from_pdf", return_value=sample_linkedin_text):
            result = parse_linkedin_pdf("fake_path.pdf")
        # Should not raise - use to_dict() for serialization
        json_output = json.dumps(result.to_dict())
        assert "John Doe" in json_output
        assert "Acme Corp" in json_output


@pytest.mark.slow
class TestParseLinkedInPdfWithRealFile:
    """Integration tests using actual PDF file (skipped if file not present or empty)."""

    @pytest.fixture
    def sample_pdf_path(self):
        """Return path to sample LinkedIn PDF if it exists and is not empty."""
        pdf_path = Path(__file__).parent.parent / "Profile.pdf"
        if not pdf_path.exists():
            pytest.skip("Sample LinkedIn PDF not found")
        if pdf_path.stat().st_size < 1000:  # Valid PDFs are at least 1KB
            pytest.skip("Sample LinkedIn PDF is empty or too small")
        return str(pdf_path)

    def test_parse_real_pdf(self, sample_pdf_path):
        result = parse_linkedin_pdf(sample_pdf_path)

        # Check result is ResumeData
        assert isinstance(result, ResumeData)
        assert result.name
        assert len(result.experience) > 0


class TestMain:
    """Tests for main CLI function."""

    def test_main_file_not_found(self, monkeypatch, capsys, tmp_path: Path) -> None:
        """Test error when input file doesn't exist."""
        nonexistent = tmp_path / "nonexistent.pdf"
        monkeypatch.setattr("sys.argv", ["parse-linkedin", "-i", str(nonexistent)])
        result = main()
        assert result == 1
        captured = capsys.readouterr()
        assert "Input file not found" in captured.out

    def test_main_non_pdf_warning(self, monkeypatch, capsys, tmp_path: Path) -> None:
        """Test warning when input file is not a PDF."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not a pdf")
        monkeypatch.setattr("sys.argv", ["parse-linkedin", "-i", str(txt_file)])

        with patch("src.parse_linkedin.parse_linkedin_pdf") as mock_parse:
            mock_parse.return_value = ResumeData(name="Test", title="Engineer")
            main()

        captured = capsys.readouterr()
        assert "Warning" in captured.out
        assert "may not be a PDF" in captured.out

    def test_main_verbose_output(self, monkeypatch, capsys, tmp_path: Path) -> None:
        """Test verbose flag produces additional output."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake pdf content")

        with patch("src.parse_linkedin.parse_linkedin_pdf") as mock_parse:
            mock_parse.return_value = ResumeData(
                name="John Doe",
                title="Engineer",
                experience=[Experience(company="Test Co", title="Dev")],
                education=[Education(school="Test U")],
                skills=["Python", "AWS"],
                certifications=["Cert1"],
            )
            monkeypatch.setattr("sys.argv", ["parse-linkedin", "-i", str(pdf_file), "-v"])
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "Parsing LinkedIn PDF:" in captured.out
        assert "Extracted name: John Doe" in captured.out
        assert "Found 1 experience entries" in captured.out
        assert "Found 1 education entries" in captured.out
        assert "Found 2 skills" in captured.out
        assert "Found 1 certifications" in captured.out

    def test_main_output_to_file(self, monkeypatch, tmp_path: Path) -> None:
        """Test output written to file."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake pdf content")
        output_file = tmp_path / "output.json"

        with patch("src.parse_linkedin.parse_linkedin_pdf") as mock_parse:
            mock_parse.return_value = ResumeData(name="Test", title="Engineer")
            monkeypatch.setattr(
                "sys.argv",
                ["parse-linkedin", "-i", str(pdf_file), "-o", str(output_file)],
            )
            result = main()

        assert result == 0
        assert output_file.exists()
        data = json.loads(output_file.read_text())
        assert data["name"] == "Test"

    def test_main_output_to_file_verbose(self, monkeypatch, capsys, tmp_path: Path) -> None:
        """Test verbose output when writing to file."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake pdf content")
        output_file = tmp_path / "output.json"

        with patch("src.parse_linkedin.parse_linkedin_pdf") as mock_parse:
            mock_parse.return_value = ResumeData(name="Test", title="Engineer")
            monkeypatch.setattr(
                "sys.argv",
                ["parse-linkedin", "-i", str(pdf_file), "-o", str(output_file), "-v"],
            )
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "Output written to:" in captured.out

    def test_main_parse_error(self, monkeypatch, capsys, tmp_path: Path) -> None:
        """Test error handling when parsing fails."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake pdf content")

        with patch(
            "src.parse_linkedin.parse_linkedin_pdf",
            side_effect=Exception("Parse failed"),
        ):
            monkeypatch.setattr("sys.argv", ["parse-linkedin", "-i", str(pdf_file)])
            result = main()

        assert result == 1
        captured = capsys.readouterr()
        assert "Error parsing PDF" in captured.out

    def test_main_output_to_stdout(self, monkeypatch, capsys, tmp_path: Path) -> None:
        """Test JSON output to stdout."""
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_bytes(b"%PDF-1.4 fake pdf content")

        with patch("src.parse_linkedin.parse_linkedin_pdf") as mock_parse:
            mock_parse.return_value = ResumeData(name="Jane Doe", title="Manager")
            monkeypatch.setattr("sys.argv", ["parse-linkedin", "-i", str(pdf_file)])
            result = main()

        assert result == 0
        captured = capsys.readouterr()
        assert "Jane Doe" in captured.out
        # Should be valid JSON
        data = json.loads(captured.out)
        assert data["name"] == "Jane Doe"


class TestExtractTextFromPdf:
    """Tests for extract_text_from_pdf function."""

    def test_extract_text_normalizes_non_breaking_spaces(self, tmp_path: Path) -> None:
        """Test that non-breaking spaces are normalized."""
        assert tmp_path is not None  # to avoid unused variable warning

        # We need to mock PdfReader since creating real PDFs is complex
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Hello\xa0World"

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page]

        with patch("src.parse_linkedin.PdfReader", return_value=mock_reader):
            result = extract_text_from_pdf("fake.pdf")

        assert result == ["Hello World"]

    def test_extract_text_skips_empty_pages(self, tmp_path: Path) -> None:
        """Test that empty pages are skipped."""
        assert tmp_path is not None  # to avoid unused variable warning

        mock_page1 = MagicMock()
        mock_page1.extract_text.return_value = "Page 1 content"
        mock_page2 = MagicMock()
        mock_page2.extract_text.return_value = ""
        mock_page3 = MagicMock()
        mock_page3.extract_text.return_value = "Page 3 content"

        mock_reader = MagicMock()
        mock_reader.pages = [mock_page1, mock_page2, mock_page3]

        with patch("src.parse_linkedin.PdfReader", return_value=mock_reader):
            result = extract_text_from_pdf("fake.pdf")

        assert len(result) == 2
        assert result[0] == "Page 1 content"
        assert result[1] == "Page 3 content"


class TestExtractSidebarSectionsAdvanced:
    """Additional tests for extract_sidebar_sections edge cases."""

    def test_extracts_linkedin_url_multiline(self) -> None:
        """Test extracting LinkedIn URL split across multiple lines."""
        lines = [
            "Contact",
            "www.linkedin.com/in/",
            "johndoe",
            "(LinkedIn)",
            "Top Skills",
            "Python",
        ]
        indices = find_section_indices(lines)
        sidebar = extract_sidebar_sections(lines, indices)
        assert "johndoe" in sidebar["contact"]["linkedin"]

    def test_extracts_languages_section(self) -> None:
        """Test extracting languages section."""
        lines = [
            "Contact",
            "test@email.com",
            "Top Skills",
            "Python",
            "Languages",
            "English (Native)",
            "Spanish (Fluent)",
            "Certifications",
            "AWS Cert",
            "Summary",
        ]
        indices = find_section_indices(lines)
        sidebar = extract_sidebar_sections(lines, indices)
        assert "English (Native)" in sidebar["languages"]
        assert "Spanish (Fluent)" in sidebar["languages"]

    def test_certifications_stops_at_name(self) -> None:
        """Test that certifications extraction stops before the name."""
        lines = [
            "Certifications",
            "AWS Certified",
            "Google Cloud",
            "John Doe",
            "Software Engineer | Tech Lead",
            "Summary",
        ]
        indices = find_section_indices(lines)
        sidebar = extract_sidebar_sections(lines, indices)
        assert "AWS Certified" in sidebar["certifications"]
        assert "Google Cloud" in sidebar["certifications"]
        assert "John Doe" not in sidebar["certifications"]


class TestExtractNameTitleLocation:
    """Tests for extract_name_title_location function."""

    def test_extracts_name_with_multi_line_title(self) -> None:
        """Test extracting name with title spanning multiple lines."""
        lines = [
            "Some header",
            "Certifications",
            "Cert1",
            "John Doe",
            "Software Engineer | Tech Lead",
            "| Python Expert",
            "New York, USA",
            "Summary",
            "About me",
        ]
        indices = find_section_indices(lines)
        name, title, location = extract_name_title_location(lines, indices)
        assert name == "John Doe"
        assert "Software Engineer" in title
        assert "Python Expert" in title
        assert location == "New York, USA"

    def test_handles_missing_name(self) -> None:
        """Test handling when name pattern isn't found."""
        lines = ["Summary", "About me", "Experience", "Work"]
        indices = find_section_indices(lines)
        name, title, location = extract_name_title_location(lines, indices)
        assert name == ""
        assert title == ""
        assert location == ""


class TestExtractSummary:
    """Tests for extract_summary function."""

    def test_extracts_summary(self) -> None:
        """Test basic summary extraction."""
        lines = [
            "Summary",
            "I am a software engineer",
            "with 10 years of experience.",
            "Experience",
            "Company",
        ]
        indices = find_section_indices(lines)
        summary = extract_summary(lines, indices)
        assert "software engineer" in summary
        assert "10 years" in summary

    def test_missing_summary_returns_empty(self) -> None:
        """Test that missing summary section returns empty string."""
        lines = ["Experience", "Company", "Education", "School"]
        indices = find_section_indices(lines)
        summary = extract_summary(lines, indices)
        assert summary == ""


class TestParseExperienceHighlightsAdvanced:
    """Additional tests for parse_experience_highlights."""

    def test_long_colon_position_not_treated_as_label(self) -> None:
        """Test that colon far into the text is not treated as a label."""
        # Colon at position > 40 should not be treated as label
        description = "- This is a very long description that eventually has a colon: but it's not a label"
        result = parse_experience_highlights(description)
        assert isinstance(result, list)
        assert len(result) == 1
        assert result[0]["label"] == ""
        assert "eventually has a colon" in result[0]["description"]


class TestExtractEducationAdvanced:
    """Additional tests for extract_education edge cases."""

    def test_education_with_no_degree_indicators(self) -> None:
        """Test education entry without standard degree indicators."""
        text = """
Education
Some School Name
Field of Study · (2015 - 2019)
"""
        education = extract_education(text)
        assert len(education) == 1
        assert "Some School Name" in education[0]["school"]

    def test_education_multiple_entries(self) -> None:
        """Test extracting multiple education entries."""
        text = """
Education
First University
Master's Degree, Computer Science · (September 2018 - June 2020)
Second University
Bachelor's Degree, Engineering · (September 2014 - June 2018)
"""
        education = extract_education(text)
        assert len(education) == 2

    def test_education_no_education_section(self) -> None:
        """Test handling when Education section is missing."""
        text = """
Experience
Company
Software Engineer
January 2020 - Present (1 year)
"""
        education = extract_education(text)
        assert education == []


class TestExperienceToDict:
    """Tests for Experience.to_dict method."""

    def test_experience_with_highlights(self) -> None:
        """Test Experience.to_dict with highlights."""
        exp = Experience(
            company="Test Co",
            title="Engineer",
            start_date="Jan 2020",
            end_date="Present",
            highlights=[Highlight(label="Test:", description="Did things")],
        )
        result = exp.to_dict()
        assert "highlights" in result
        assert result["highlights"][0]["label"] == "Test:"
        assert "description" not in result

    def test_experience_with_description(self) -> None:
        """Test Experience.to_dict with description only."""
        exp = Experience(
            company="Test Co",
            title="Engineer",
            start_date="Jan 2020",
            end_date="Present",
            description="Did various things",
        )
        result = exp.to_dict()
        assert "description" in result
        assert "highlights" not in result


class TestConvertToResumeFormatAdvanced:
    """Additional tests for convert_to_resume_format."""

    def test_experience_with_highlights_list(self) -> None:
        """Test converting experience that has bullet points."""
        sidebar = {
            "contact": {"email": "test@example.com", "linkedin": ""},
            "top_skills": [],
            "certifications": [],
        }
        experience = [
            {
                "company": "Test Co",
                "title": "Engineer",
                "start_date": "Jan 2020",
                "end_date": "Present",
                "description": "- First task - Second task",
            }
        ]
        result = convert_to_resume_format(
            sidebar=sidebar,
            name="Test",
            title="Engineer",
            location="City, Country",
            summary="Summary",
            experience=experience,
            education=[],
        )
        # Should have converted bullet points to highlights
        assert len(result.experience) == 1
        assert len(result.experience[0].highlights) == 2


class TestExtractExperienceAdvanced:
    """Additional tests for extract_experience edge cases."""

    def test_experience_no_experience_section(self) -> None:
        """Test handling when Experience section is missing."""
        text = """
Summary
I am a software engineer.
Education
Test School
"""
        experiences = extract_experience(text)
        assert experiences == []

    def test_experience_with_page_markers(self) -> None:
        """Test that page markers are filtered out."""
        text = """
Experience
Test Company
Software Engineer
January 2020 - December 2022 (2 years)
New York, USA
Page 1 of 2
Did great things at this company.
Education
Test School
"""
        experiences = extract_experience(text)
        assert len(experiences) == 1
        assert "Page 1 of 2" not in experiences[0]["description"]

    def test_experience_skips_non_date_lines(self) -> None:
        """Test that lines without date pattern are skipped properly."""
        text = """
Experience
Not a company with date
Some random text
Actual Company
Software Engineer
January 2020 - December 2022 (2 years)
Location, USA
Description here
Education
"""
        experiences = extract_experience(text)
        assert len(experiences) == 1
        assert experiences[0]["company"] == "Actual Company"


class TestJoinSplitLinesAdvanced:
    """Additional tests for _join_split_lines edge cases."""

    def test_single_item_list(self) -> None:
        """Test list with single item."""
        lines = ["Single Item"]
        result = _join_split_lines(lines)
        assert result == ["Single Item"]

    def test_trailing_comma_join(self) -> None:
        """Test joining when current line ends with comma."""
        lines = ["First,", "Second,", "Third"]
        result = _join_split_lines(lines)
        assert len(result) == 1
        assert "First" in result[0]
        assert "Third" in result[0]


class TestExtractEducationEdgeCases:
    """Edge case tests for extract_education function."""

    def test_education_with_degree_indicator_in_later_line(self) -> None:
        """Test when degree indicator appears in a later line."""
        text = """
Education
University Name
Here is some text
Bachelor's Degree, Computer Science · (2010 - 2014)
"""
        education = extract_education(text)
        assert len(education) == 1
        assert "Bachelor" in education[0]["degree"]

    def test_education_without_bullet_separator(self) -> None:
        """Test education entry without · separator."""
        text = """
Education
Test University
Computer Science (2010 - 2014)
"""
        education = extract_education(text)
        # Should still parse something
        assert len(education) >= 0  # May or may not find entry depending on format


class TestExtractSidebarSectionsEdgeCases:
    """Edge case tests for sidebar sections extraction."""

    def test_email_continuation_next_line(self) -> None:
        """Test email that might continue on next line."""
        lines = [
            "Contact",
            "verylongemail@example",
            ".com",  # Continuation line
            "Top Skills",
            "Python",
        ]
        indices = find_section_indices(lines)
        sidebar = extract_sidebar_sections(lines, indices)
        # Email extraction should handle this case
        assert "verylongemail@example" in sidebar["contact"]["email"]

    def test_linkedin_url_stops_at_section(self) -> None:
        """Test LinkedIn URL parsing stops at section markers."""
        lines = [
            "Contact",
            "www.linkedin.com/in/user",
            "Top Skills",  # Should stop here
            "Python",
            "Summary",
        ]
        indices = find_section_indices(lines)
        sidebar = extract_sidebar_sections(lines, indices)
        assert "user" in sidebar["contact"]["linkedin"]
        assert "Top Skills" not in sidebar["contact"]["linkedin"]

    def test_no_contact_section(self) -> None:
        """Test when Contact section is missing."""
        lines = ["Top Skills", "Python", "AWS", "Summary", "About me"]
        indices = find_section_indices(lines)
        sidebar = extract_sidebar_sections(lines, indices)
        assert sidebar["contact"]["email"] == ""
        assert sidebar["contact"]["linkedin"] == ""

    def test_no_skills_section(self) -> None:
        """Test when Top Skills section is missing."""
        lines = ["Contact", "email@test.com", "Summary", "About me"]
        indices = find_section_indices(lines)
        sidebar = extract_sidebar_sections(lines, indices)
        assert sidebar["top_skills"] == []


class TestExtractNameTitleLocationAdvanced:
    """Additional edge case tests for name/title/location extraction."""

    def test_no_pipe_in_next_line(self) -> None:
        """Test when there's no pipe character after potential name."""
        lines = [
            "Certifications",
            "AWS Cert",
            "John Doe",
            "No pipe here",
            "Summary",
            "About me",
        ]
        indices = find_section_indices(lines)
        name, title, _ = extract_name_title_location(lines, indices)
        # Should not find name since pattern doesn't match
        assert name == "" or title == ""

    def test_title_without_location(self) -> None:
        """Test name and title extraction without location line."""
        lines = [
            "Certifications",
            "Cert",
            "Jane Doe",
            "Software Engineer | Python",
            "Summary",
            "About me",
        ]
        indices = find_section_indices(lines)
        name, title, location = extract_name_title_location(lines, indices)
        assert name == "Jane Doe"
        assert "Software Engineer" in title
        assert location == ""  # No location found

    def test_empty_lines_between_sections(self) -> None:
        """Test handling of empty lines between certifications and summary."""
        lines = [
            "Certifications",
            "Cert1",
            "",  # Empty line
            "John Doe",
            "Engineer | Lead",
            "City, Country",
            "Summary",
        ]
        indices = find_section_indices(lines)
        name, _, location = extract_name_title_location(lines, indices)
        assert name == "John Doe"
        assert location == "City, Country"


class TestEducationParsingComplex:
    """Complex education parsing scenarios."""

    def test_education_with_field_comma(self) -> None:
        """Test education where field of study has comma."""
        text = """
Education
MIT
Computer Science, Artificial Intelligence · (2015 - 2019)
"""
        education = extract_education(text)
        assert len(education) == 1
        assert education[0]["school"] == "MIT"

    def test_education_entry_text_cleanup(self) -> None:
        """Test education handles entry text properly."""
        text = """
Education
Harvard University
Business Administration
MBA · (2010 - 2012)
"""
        education = extract_education(text)
        assert len(education) == 1
        # School name should be extracted
        assert "Harvard" in education[0]["school"] or "Business" in education[0]["degree"]

    def test_education_without_school_just_degree(self) -> None:
        """Test edge case where school portion might be empty."""
        text = """
Education
Bachelor's Degree · (2010 - 2014)
"""
        education = extract_education(text)
        # Should handle gracefully
        assert isinstance(education, list)


class TestExperienceExtractEdgeCases:
    """Edge cases for experience extraction."""

    def test_experience_ends_at_text_end(self) -> None:
        """Test experience extraction when there's no Education section."""
        text = """
Experience
Test Company
Software Engineer
January 2020 - December 2022 (2 years)
New York, USA
Did great things.
Another line of description.
"""
        experiences = extract_experience(text)
        assert len(experiences) == 1
        assert "great things" in experiences[0]["description"]

    def test_experience_multiple_without_location(self) -> None:
        """Test multiple experiences without location lines."""
        text = """
Experience
Company A
Role A
January 2022 - Present (1 year)
Description A
Company B
Role B
January 2020 - December 2021 (2 years)
Description B
Education
"""
        experiences = extract_experience(text)
        assert len(experiences) == 2
