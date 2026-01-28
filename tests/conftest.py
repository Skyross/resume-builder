"""Pytest configuration and fixtures."""

import json
from pathlib import Path

import pytest


@pytest.fixture
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture
def template_dir(project_root: Path) -> Path:
    """Return the templates directory."""
    return project_root / "templates"


@pytest.fixture
def sample_resume_data() -> dict:
    """Return minimal sample resume data for testing."""
    return {
        "name": "Test Person",
        "title": "Software Engineer",
        "contact": {
            "email": "test@example.com",
            "linkedin": "linkedin.com/in/test",
            "location": "Test City, TC",
            "phone": "+1 234 567 8900",
            "website": "test.com",
        },
        "summary": "A test summary for the resume.",
        "experience": [
            {
                "company": "Test Company",
                "title": "Test Title",
                "start_date": "Jan 2020",
                "end_date": "Present",
                "highlights": [
                    {"label": "Achievement:", "description": "Did something great"},
                ],
            }
        ],
        "skills": ["Python", "Testing", "CI/CD"],
        "certifications": ["Test Certification"],
        "certifications_title": "Certifications",
        "education": [
            {
                "school": "Test University",
                "degree": "BS, Computer Science",
                "start_year": "2015",
                "end_year": "2019",
            }
        ],
    }


@pytest.fixture
def sample_data_file(tmp_path: Path, sample_resume_data: dict) -> Path:
    """Create a temporary JSON data file with sample resume data."""
    data_file = tmp_path / "test_resume_data.json"
    data_file.write_text(json.dumps(sample_resume_data, indent=2))
    return data_file


@pytest.fixture
def invalid_json_file(tmp_path: Path) -> Path:
    """Create a temporary file with invalid JSON."""
    invalid_file = tmp_path / "invalid.json"
    invalid_file.write_text("{invalid json content")
    return invalid_file
