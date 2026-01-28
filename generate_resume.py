#!/usr/bin/env python3
"""
Resume Generator - Creates a professional PDF resume from HTML template and JSON data

Usage:
    python generate_resume.py -d data.json                     # Use default template
    python generate_resume.py -d data.json -t modern           # Use modern template
    python generate_resume.py -d data.json -o output.pdf       # Custom output path
    python generate_resume.py --list-templates                 # List available templates
"""

import argparse
import json
from pathlib import Path

from jinja2 import Environment, FileSystemLoader
from pypdf import PdfReader, PdfWriter
from weasyprint import HTML

TEMPLATES = {
    "default": "resume_template.html",
    "minimalist": "resume_template_minimalist.html",
    "modern": "resume_template_modern.html",
    "classic": "resume_template_classic.html",
}


def load_resume_data(data_path: str) -> dict:
    """Load resume data from JSON file."""
    with Path(data_path).open(encoding="utf-8") as f:
        return json.load(f)


def render_template(template_dir: Path, template_name: str, data: dict) -> str:
    """Render HTML template with resume data using Jinja2."""
    env = Environment(loader=FileSystemLoader(template_dir))
    template = env.get_template(template_name)
    return template.render(**data)


def parse_metadata(meta_args: list[str] | None) -> dict[str, str] | None:
    """
    Parse metadata arguments into a dictionary.

    Args:
        meta_args: List of "key=value" strings

    Returns:
        Dictionary of metadata or None if no metadata provided
    """
    if not meta_args:
        return None

    metadata_map = {}
    for item in meta_args:
        if "=" not in item:
            print(f"Warning: Invalid metadata format '{item}', expected 'key=value'")
            continue
        key, value = item.split("=", 1)
        key = key.strip().lower()
        value = value.strip()
        metadata_map[key] = value

    return metadata_map if metadata_map else None


def apply_pdf_metadata(pdf_path: Path, metadata: dict[str, str]) -> None:
    """
    Apply custom metadata to an existing PDF file.

    Args:
        pdf_path: Path to the PDF file
        metadata: Dictionary of metadata key-value pairs
    """
    reader = PdfReader(pdf_path)
    writer = PdfWriter()

    # Copy all pages
    for page in reader.pages:
        writer.add_page(page)

    # Map user-friendly keys to PDF metadata keys
    pdf_metadata = {}
    key_mapping = {
        "title": "/Title",
        "author": "/Author",
        "subject": "/Subject",
        "keywords": "/Keywords",
        "creator": "/Creator",
        "producer": "/Producer",
    }

    for key, value in metadata.items():
        pdf_key = key_mapping.get(key, f"/{key.capitalize()}")
        pdf_metadata[pdf_key] = value

    writer.add_metadata(pdf_metadata)

    # Write to the same file
    with pdf_path.open("wb") as f:
        writer.write(f)


def generate_resume_pdf(
    template_dir: Path,
    template_name: str,
    data: dict,
    output_path: str,
    metadata: dict[str, str] | None = None,
) -> None:
    """
    Generate PDF from HTML resume template and data.

    Args:
        template_dir: Directory containing templates
        template_name: Name of the template file
        data: Resume data dictionary
        output_path: Path where the PDF will be saved
        metadata: Optional PDF metadata dictionary
    """
    output_file = Path(output_path)

    # Create output directory if it doesn't exist
    output_file.parent.mkdir(parents=True, exist_ok=True)

    print(f"Using template: {template_name}")
    print("Rendering template with data...")

    # Render template with data
    html_content = render_template(template_dir, template_name, data)

    print("Generating PDF resume...")

    # Generate PDF from rendered HTML
    HTML(string=html_content, base_url=str(template_dir)).write_pdf(str(output_file))

    # Apply custom metadata if provided
    if metadata:
        print("Applying PDF metadata...")
        apply_pdf_metadata(output_file, metadata)

    print(f"Resume PDF generated successfully: {output_file}")
    print(f"File size: {output_file.stat().st_size / 1024:.1f} KB")


def list_templates():
    """Print available templates."""
    print("Available templates:")
    for name, filename in TEMPLATES.items():
        print(f"  {name:12} -> {filename}")


def main():
    script_dir = Path(__file__).parent
    default_data = script_dir / "resume_data.example.json"
    default_output = script_dir / "output" / "resume.pdf"

    parser = argparse.ArgumentParser(
        description="Generate a professional PDF resume from HTML template and JSON data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s -d resume_data.json
      Generate PDF using default template and your data

  %(prog)s -d data.json -t modern
      Use the modern sidebar template

  %(prog)s -d data.json -t classic -o MyResume.pdf
      Use classic template with custom output path

  %(prog)s -d data.json -m "author=John Doe" -m "title=Resume"
      Set PDF metadata fields

  %(prog)s -d data.json -m "keywords=python,developer,senior"
      Set multiple keywords (comma-separated)

  %(prog)s --list-templates
      Show all available template styles

Templates:
  default     - Blue theme with modern styling
  minimalist  - Clean grayscale design
  modern      - Bold sidebar with purple gradient
  classic     - Traditional serif with forest green accents

Metadata keys:
  title       - PDF document title
  author      - Document author name
  subject     - Document subject (alias: description)
  keywords    - Comma-separated keywords
  creator     - Creating application (alias: generator)
        """,
    )

    parser.add_argument(
        "-d",
        "--data",
        type=str,
        default=str(default_data),
        help=f"Path to JSON data file (default: {default_data.name})",
    )

    parser.add_argument(
        "-t",
        "--template",
        type=str,
        default="default",
        choices=list(TEMPLATES.keys()),
        help="Template style to use (default: default)",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=str(default_output),
        help=f"Path for output PDF file (default: {default_output})",
    )

    parser.add_argument("-v", "--verbose", action="store_true", help="Show verbose output")

    parser.add_argument("--list-templates", action="store_true", help="List available templates and exit")

    parser.add_argument(
        "-m",
        "--meta",
        action="append",
        metavar="KEY=VALUE",
        help="Set PDF metadata (can be used multiple times). "
        "Supported keys: title, author, description, subject, keywords, generator, creator",
    )

    parser.add_argument(
        "-s",
        "--hidden-text",
        type=str,
        default="",
        help="Custom hidden text to embed in the resume (same color as background, smallest font)",
    )

    args = parser.parse_args()

    if args.list_templates:
        list_templates()
        return 0

    # Validate data file exists
    data_path = Path(args.data)
    if not data_path.exists():
        print(f"Error: Data file not found: {args.data}")
        print("Create a JSON file with your resume data. See resume_data.example.json for format.")
        return 1

    # Load resume data
    try:
        data = load_resume_data(args.data)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in data file: {e}")
        return 1

    # Get template filename
    template_name = TEMPLATES[args.template]
    template_path = script_dir / template_name

    if not template_path.exists():
        print(f"Error: Template not found: {template_path}")
        return 1

    if args.verbose:
        print(f"Data file: {args.data}")
        print(f"Template: {args.template} ({template_name})")
        print(f"Output: {args.output}")
        print()

    # Parse metadata if provided
    metadata = parse_metadata(args.meta)

    if args.verbose and metadata:
        print(f"Metadata: {args.meta}")
        print()

    # Add hidden text to data if provided
    if args.hidden_text:
        data["hidden_text"] = args.hidden_text

    # Generate the PDF
    try:
        generate_resume_pdf(script_dir, template_name, data, args.output, metadata)
    except Exception as e:
        print(f"Error generating PDF: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
