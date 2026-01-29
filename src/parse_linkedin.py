#!/usr/bin/env python3
"""
LinkedIn PDF Parser - Converts LinkedIn exported PDF profiles to JSON format

Usage:
    uv run parse-linkedin -i Profile.pdf                    # Output to stdout
    uv run parse-linkedin -i Profile.pdf -o resume.json     # Output to file
    uv run parse-linkedin -i Profile.pdf -o resume.json -v  # Verbose mode
"""

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from pypdf import PdfReader


@dataclass
class Contact:
    """Contact information."""

    email: str = ""
    linkedin: str = ""
    location: str = ""
    phone: str = ""
    website: str = ""


@dataclass
class Highlight:
    """Experience highlight/bullet point."""

    label: str = ""
    description: str = ""


@dataclass
class Experience:
    """Work experience entry."""

    company: str = ""
    title: str = ""
    start_date: str = ""
    end_date: str = ""
    description: str = ""
    highlights: list[Highlight] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dict, excluding empty fields."""
        result = {
            "company": self.company,
            "title": self.title,
            "start_date": self.start_date,
            "end_date": self.end_date,
        }
        if self.highlights:
            result["highlights"] = [asdict(h) for h in self.highlights]
        elif self.description:
            result["description"] = self.description
        return result


@dataclass
class Education:
    """Education entry."""

    school: str = ""
    degree: str = ""
    start_year: str = ""
    end_year: str = ""


@dataclass
class ResumeData:
    """Complete resume data structure."""

    name: str = ""
    title: str = ""
    contact: Contact = field(default_factory=Contact)
    summary: str = ""
    experience: list[Experience] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    certifications: list[str] = field(default_factory=list)
    certifications_title: str = "Certifications"
    education: list[Education] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "title": self.title,
            "contact": asdict(self.contact),
            "summary": self.summary,
            "experience": [exp.to_dict() for exp in self.experience],
            "skills": self.skills,
            "certifications": self.certifications,
            "certifications_title": self.certifications_title,
            "education": [asdict(edu) for edu in self.education],
        }


def extract_text_from_pdf(pdf_path: str) -> list[str]:
    """Extract text content from each page of a PDF file."""
    reader = PdfReader(pdf_path)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            # Normalize non-breaking spaces to regular spaces
            text = text.replace("\xa0", " ")
            pages.append(text)
    return pages


def parse_date_range(date_str: str) -> tuple[str, str]:
    """
    Parse date range string into start_date and end_date.

    Examples:
        "November 2021 - November 2025 (4 years 1 month)" -> ("Nov 2021", "Nov 2025")
        "August 2015 - July 2017 (2 years)" -> ("Aug 2015", "Jul 2017")
    """
    # Remove duration in parentheses
    date_str = re.sub(r"\s*\([^)]+\)\s*", "", date_str).strip()

    # Month abbreviation mapping
    month_map = {
        "January": "Jan",
        "February": "Feb",
        "March": "Mar",
        "April": "Apr",
        "May": "May",
        "June": "Jun",
        "July": "Jul",
        "August": "Aug",
        "September": "Sep",
        "October": "Oct",
        "November": "Nov",
        "December": "Dec",
    }

    # Split by " - "
    if " - " in date_str:
        start, end = date_str.split(" - ", 1)
    else:
        start = date_str
        end = "Present"

    # Abbreviate months
    for full, abbr in month_map.items():
        start = start.replace(full, abbr)
        end = end.replace(full, abbr)

    return start.strip(), end.strip()


def parse_education_years(date_str: str) -> tuple[str, str]:
    """
    Parse education date range into start_year and end_year.

    Examples:
        "(September 2008 - June 2013)" -> ("2008", "2013")
    """
    years = re.findall(r"\b((?:19|20)\d{2})\b", date_str)
    if len(years) >= 2:
        return years[0], years[1]
    elif len(years) == 1:
        return years[0], years[0]
    return "", ""


def find_section_indices(lines: list[str]) -> dict[str, int]:
    """Find the line indices of major section headers."""
    sections = {}
    section_markers = ["Contact", "Top Skills", "Languages", "Certifications", "Summary", "Experience", "Education"]

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped in section_markers and stripped not in sections:
            sections[stripped] = i

    return sections


def extract_sidebar_sections(lines: list[str], section_indices: dict[str, int]) -> dict:
    """Extract sidebar sections: Contact, Top Skills, Languages, Certifications."""
    result = {
        "contact": {"email": "", "linkedin": ""},
        "top_skills": [],
        "languages": [],
        "certifications": [],
    }

    # Determine the end of sidebar (where main content begins - Summary or name)
    summary_idx = section_indices.get("Summary", len(lines))

    # Contact section
    if "Contact" in section_indices:
        start = section_indices["Contact"] + 1
        end = section_indices.get("Top Skills", summary_idx)
        for i in range(start, end):
            line = lines[i].strip()
            if "@" in line:
                # Email might be split across lines
                email = line
                if i + 1 < end and lines[i + 1].strip() and "@" not in lines[i + 1] and "." not in lines[i + 1].strip():
                    email += lines[i + 1].strip()
                result["contact"]["email"] = email.replace("\n", "")
            elif "linkedin.com" in line.lower():
                # LinkedIn URL might be split across multiple lines
                url_parts = [line]
                j = i + 1
                while j < end:
                    next_line = lines[j].strip()
                    # Stop if we hit a section marker or another type of content
                    if not next_line or next_line.startswith("Top") or "@" in next_line:
                        break
                    # Check if this line is continuation of URL (username part or "(LinkedIn)")
                    if "(LinkedIn)" in next_line or (next_line and not next_line[0].isupper()):
                        url_parts.append(next_line)
                        j += 1
                    else:
                        break
                url = "".join(url_parts)
                url = url.replace("www.", "").replace("(LinkedIn)", "").strip()
                result["contact"]["linkedin"] = url

    # Top Skills section
    if "Top Skills" in section_indices:
        start = section_indices["Top Skills"] + 1
        end = section_indices.get("Languages", section_indices.get("Certifications", summary_idx))
        for i in range(start, end):
            line = lines[i].strip()
            if line and line not in ["Languages", "Certifications"]:
                result["top_skills"].append(line)

    # Languages section
    if "Languages" in section_indices:
        start = section_indices["Languages"] + 1
        end = section_indices.get("Certifications", summary_idx)
        for i in range(start, end):
            line = lines[i].strip()
            if line and line != "Certifications":
                result["languages"].append(line)

    # Certifications section
    if "Certifications" in section_indices:
        start = section_indices["Certifications"] + 1
        end = summary_idx
        cert_lines = []
        for i in range(start, end):
            line = lines[i].strip()
            # Stop when we hit the name (a short line that's a name, followed by title with |)
            if line and i + 1 < len(lines):
                next_line = lines[i + 1].strip() if i + 1 < len(lines) else ""
                # Name is typically followed by a line with | separators (title)
                if "|" in next_line:
                    break
            if line and line not in ["Summary", "Experience", "Education"]:
                cert_lines.append(line)

        # Join certification lines that were split
        result["certifications"] = _join_split_lines(cert_lines)

    return result


def _join_split_lines(lines: list[str]) -> list[str]:
    """Join lines that were split inappropriately (e.g., multi-line cert names)."""
    if not lines:
        return []

    result = []
    current = ""

    for line in lines:
        # If line starts with lowercase or is a continuation, append to current
        if current and (line[0].islower() or line.endswith(",") or current.endswith(",")):
            current = current.rstrip(",") + " " + line
        else:
            if current:
                result.append(current.strip())
            current = line

    if current:
        result.append(current.strip())

    return result


def extract_name_title_location(lines: list[str], section_indices: dict[str, int]) -> tuple[str, str, str]:
    """Extract name, title, and location from main content area."""
    name = ""
    title = ""
    location = ""

    # The name appears between Certifications and Summary sections
    # It's followed by a line with | separators (the title)
    certs_idx = section_indices.get("Certifications", 0)
    summary_idx = section_indices.get("Summary", len(lines))

    for i in range(certs_idx, summary_idx):
        line = lines[i].strip()
        if not line:
            continue

        # Check if next line contains | (indicating current line is the name)
        if i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if "|" in next_line and not name:
                name = line
                # Collect title (might span multiple lines)
                title_parts = [next_line]
                j = i + 2
                while j < summary_idx:
                    following = lines[j].strip()
                    if "|" in following:
                        title_parts.append(following)
                        j += 1
                    elif following and "," in following and len(following.split(",")) == 2:
                        # This is likely location (City, Country)
                        location = following
                        break
                    else:
                        break
                title = " ".join(title_parts)
                break

    return name, title, location


def extract_summary(lines: list[str], section_indices: dict[str, int]) -> str:
    """Extract the Summary section content."""
    if "Summary" not in section_indices:
        return ""

    start = section_indices["Summary"] + 1
    end = section_indices.get("Experience", len(lines))

    summary_lines = []
    for i in range(start, end):
        line = lines[i].strip()
        if line and line != "Experience":
            summary_lines.append(line)

    return " ".join(summary_lines)


def extract_experience(text: str) -> list[dict]:
    """Extract work experience entries from the full text."""
    experiences = []

    # Find Experience section
    exp_match = re.search(r"\nExperience\n", text)
    if not exp_match:
        return experiences

    # Find where Experience section ends (Education or end of text)
    edu_match = re.search(r"\nEducation\n", text)
    exp_text = text[exp_match.end() : edu_match.start()] if edu_match else text[exp_match.end() :]

    # Date pattern: Month Year - Month Year (X years Y months)
    date_pattern = re.compile(r"([A-Z][a-z]+ \d{4}) - ([A-Z][a-z]+ \d{4}|Present) \([^)]+\)")
    # Location pattern: City, Country/State
    location_pattern = re.compile(r"^[A-Z][a-zA-Z\s]+,\s*[A-Z][a-zA-Z\s]+$")
    # Page marker pattern
    page_marker = re.compile(r"^\s*Page \d+ of \d+\s*$")

    # Pre-filter lines to remove page markers and empty lines, but keep track of content
    raw_lines = exp_text.split("\n")
    lines = []
    for line in raw_lines:
        stripped = line.strip()
        if stripped and not page_marker.match(stripped):
            lines.append(stripped)

    i = 0
    while i < len(lines):
        line = lines[i]

        # Look for date pattern to identify start of experience entry
        # The structure is: Company\nTitle\nDate\nLocation\nDescription
        # So we look 2 lines ahead for a date
        if i + 2 < len(lines):
            date_line = lines[i + 2]
            date_match = date_pattern.match(date_line)

            if date_match:
                company = line
                title = lines[i + 1]
                start_date, end_date = parse_date_range(date_match.group(0))

                # Move past company, title, date
                i += 3

                # Check for location
                if i < len(lines) and location_pattern.match(lines[i]):
                    i += 1

                # Collect description until next company (signaled by another date pattern 2 lines ahead)
                description_lines = []
                while i < len(lines):
                    desc_line = lines[i]

                    # Check if we've hit the next experience entry
                    # (current line is company, next is title, line after is date)
                    if i + 2 < len(lines):
                        future_date = lines[i + 2]
                        if date_pattern.match(future_date):
                            break

                    description_lines.append(desc_line)
                    i += 1

                description = " ".join(description_lines)

                experiences.append(
                    {
                        "company": company,
                        "title": title,
                        "start_date": start_date,
                        "end_date": end_date,
                        "description": description,
                    }
                )
                continue

        i += 1

    return experiences


def extract_education(text: str) -> list[dict]:
    """Extract education entries from the full text."""
    education = []

    # Find Education section
    edu_match = re.search(r"\nEducation\n", text)
    if not edu_match:
        return education

    edu_text = text[edu_match.end() :]

    # Remove page markers
    edu_text = re.sub(r"Page \d+ of \d+", "", edu_text)

    lines = [ln.strip() for ln in edu_text.split("\n") if ln.strip()]

    # Education format: School Name (multi-line possible) \n Degree · (dates)
    # The dates end with a closing parenthesis containing years
    # Strategy: Find lines ending with date patterns like "2013)" or "2008)"

    # First, join all lines and then split by the date closing pattern
    full_edu = "\n".join(lines)

    # Pattern to match end of education entry: year followed by )
    entry_pattern = re.compile(r"(\d{4}\))")

    # Find all positions where entries end
    entries_text = []
    last_end = 0
    for match in entry_pattern.finditer(full_edu):
        entry_text = full_edu[last_end : match.end()]
        entries_text.append(entry_text)
        last_end = match.end()

    # Degree indicators - lines containing these are part of the degree, not school name
    degree_indicators = ["Degree", "Diploma", "Certificate", "Bachelor", "Master", "PhD", "Ph.D", "MBA"]

    for entry_text in entries_text:
        entry_lines = [ln.strip() for ln in entry_text.strip().split("\n") if ln.strip()]
        if not entry_lines:
            continue

        # Find where degree starts (line containing degree indicator or line before ·)
        degree_start_idx = -1
        degree_line_idx = -1

        for i, line in enumerate(entry_lines):
            if "·" in line:
                degree_line_idx = i
                break

        if degree_line_idx == -1:
            continue

        # Look for degree indicator in lines before ·
        for i in range(degree_line_idx + 1):
            if any(indicator in entry_lines[i] for indicator in degree_indicators):
                degree_start_idx = i
                break

        # If no degree indicator found, assume the line right before · is part of degree
        # and check if it looks like a degree (contains comma for field of study)
        if degree_start_idx == -1:
            for i in range(degree_line_idx, -1, -1):
                line = entry_lines[i]
                # Lines with "Degree" patterns or that look like "Field, Specialization"
                if "," in line or any(ind in line for ind in degree_indicators):
                    degree_start_idx = i
                    break

        # If still not found, school is first line only
        if degree_start_idx == -1:
            degree_start_idx = 1 if len(entry_lines) > 1 else 0

        # School is everything before degree_start_idx
        school_parts = entry_lines[:degree_start_idx]
        school = " ".join(school_parts).strip()

        # Degree is from degree_start_idx to end (including line with ·)
        degree_parts = entry_lines[degree_start_idx:]
        degree_text = " ".join(degree_parts)

        # Split by · to get degree and dates
        if "·" in degree_text:
            parts = degree_text.split("·", 1)
            degree = parts[0].strip()
            date_part = parts[1].strip() if len(parts) > 1 else ""
        else:
            degree = degree_text
            date_part = ""

        start_year, end_year = parse_education_years(date_part)

        if school:
            education.append(
                {
                    "school": school,
                    "degree": degree,
                    "start_year": start_year,
                    "end_year": end_year,
                }
            )

    return education


def parse_experience_highlights(description: str) -> list[dict] | str:
    """Convert description with bullet points to highlights format."""
    if not description:
        return ""

    # Check if description has bullet points (starts with - or has embedded -)
    if "- " in description:
        # Split by bullet points
        parts = re.split(r"(?:^|\s)- ", description)
        highlights = []

        for part in parts:
            part = part.strip()
            if not part:
                continue

            # Check for label: description format
            if ":" in part:
                colon_idx = part.index(":")
                # Only treat as label if colon is within first ~40 chars
                if colon_idx < 40:
                    label = part[: colon_idx + 1].strip()
                    desc = part[colon_idx + 1 :].strip()
                    highlights.append({"label": label, "description": desc})
                else:
                    highlights.append({"label": "", "description": part})
            else:
                highlights.append({"label": "", "description": part})

        return highlights if highlights else description

    return description


def convert_to_resume_format(
    sidebar: dict, name: str, title: str, location: str, summary: str, experience: list[dict], education: list[dict]
) -> ResumeData:
    """Convert all parsed data to the ResumeData dataclass."""
    contact = Contact(
        email=sidebar["contact"].get("email", ""),
        linkedin=sidebar["contact"].get("linkedin", ""),
        location=location,
        phone="",
        website="",
    )

    # Convert education entries
    education_entries = [
        Education(
            school=edu.get("school", ""),
            degree=edu.get("degree", ""),
            start_year=edu.get("start_year", ""),
            end_year=edu.get("end_year", ""),
        )
        for edu in education
    ]

    # Convert experience entries
    experience_entries = []
    for exp in experience:
        description = exp.get("description", "")
        parsed_highlights = parse_experience_highlights(description)

        if isinstance(parsed_highlights, list):
            highlights = [
                Highlight(label=h.get("label", ""), description=h.get("description", "")) for h in parsed_highlights
            ]
            exp_entry = Experience(
                company=exp.get("company", ""),
                title=exp.get("title", ""),
                start_date=exp.get("start_date", ""),
                end_date=exp.get("end_date", ""),
                highlights=highlights,
            )
        else:
            exp_entry = Experience(
                company=exp.get("company", ""),
                title=exp.get("title", ""),
                start_date=exp.get("start_date", ""),
                end_date=exp.get("end_date", ""),
                description=parsed_highlights,
            )
        experience_entries.append(exp_entry)

    return ResumeData(
        name=name,
        title=title,
        contact=contact,
        summary=summary,
        experience=experience_entries,
        skills=sidebar["top_skills"],
        certifications=sidebar["certifications"],
        certifications_title="Certifications",
        education=education_entries,
    )


def parse_linkedin_pdf(pdf_path: str) -> ResumeData:
    """
    Parse a LinkedIn exported PDF and return resume data as ResumeData.

    Args:
        pdf_path: Path to the LinkedIn PDF file

    Returns:
        ResumeData dataclass containing parsed resume data
    """
    # Extract text from PDF
    pages = extract_text_from_pdf(pdf_path)
    full_text = "\n".join(pages)

    # Split into lines for section parsing
    lines = full_text.split("\n")

    # Find section indices
    section_indices = find_section_indices(lines)

    # Extract sidebar sections
    sidebar = extract_sidebar_sections(lines, section_indices)

    # Extract name, title, location
    name, title, location = extract_name_title_location(lines, section_indices)

    # Extract summary
    summary = extract_summary(lines, section_indices)

    # Extract experience from full text (better handles multi-line entries)
    experience = extract_experience(full_text)

    # Extract education from full text
    education = extract_education(full_text)

    # Convert to resume format
    resume = convert_to_resume_format(sidebar, name, title, location, summary, experience, education)

    return resume


def main():
    parser = argparse.ArgumentParser(
        description="Parse LinkedIn exported PDF and convert to JSON format for resume generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -i Profile.pdf
      Parse LinkedIn PDF and output JSON to stdout

  %(prog)s -i Profile.pdf -o resume_data.json
      Parse and save to file

  %(prog)s -i Profile.pdf -o resume_data.json -v
      Parse with verbose output

  %(prog)s -i Profile.pdf -o data.json && uv run generate-resume -d data.json
      Parse and immediately generate resume PDF
        """,
    )

    parser.add_argument(
        "-i",
        "--input",
        type=str,
        required=True,
        help="Path to LinkedIn PDF file",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output JSON file path (default: stdout)",
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show verbose output",
    )

    parser.add_argument(
        "--pretty",
        action="store_true",
        default=True,
        help="Pretty-print JSON output (default: True)",
    )

    args = parser.parse_args()

    # Validate input file exists
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: Input file not found: {args.input}")
        return 1

    if input_path.suffix.lower() != ".pdf":
        print(f"Warning: Input file may not be a PDF: {args.input}")

    if args.verbose:
        print(f"Parsing LinkedIn PDF: {args.input}")

    try:
        resume_data = parse_linkedin_pdf(args.input)
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return 1

    if args.verbose:
        print(f"Extracted name: {resume_data.name}")
        print(f"Extracted title: {resume_data.title}")
        print(f"Found {len(resume_data.experience)} experience entries")
        print(f"Found {len(resume_data.education)} education entries")
        print(f"Found {len(resume_data.skills)} skills")
        print(f"Found {len(resume_data.certifications)} certifications")
        print()

    # Output JSON
    indent = 2 if args.pretty else None
    json_output = json.dumps(resume_data.to_dict(), indent=indent, ensure_ascii=False)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json_output, encoding="utf-8")
        if args.verbose:
            print(f"Output written to: {args.output}")
    else:
        print(json_output)

    return 0


if __name__ == "__main__":
    exit(main())
