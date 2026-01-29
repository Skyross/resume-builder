"""Tests for LinkedIn PDF parser."""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.parse_linkedin import (
    Contact,
    Education,
    Experience,
    ResumeData,
    _join_split_lines,
    convert_to_resume_format,
    extract_education,
    extract_experience,
    extract_sidebar_sections,
    find_section_indices,
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
