# Resume Builder

A flexible, data-driven resume generator that creates professional PDF resumes from customizable HTML templates and JSON data.

## Project Overview

This project generates tailored PDF resumes using:
- **Jinja2 templating** for dynamic content rendering
- **WeasyPrint** for high-quality HTML-to-PDF conversion
- **JSON data files** for easy content management
- **Multiple design templates** for different styles and industries

## Project Structure

```
resume-builder/
├── CLAUDE.md                        # This file - project documentation
├── DESIGN_VARIANTS.md               # Documentation of design variants
├── README.md                        # Quick start guide
├── generate_resume.py               # Python script to generate PDF from HTML + JSON
├── resume_data.example.json         # Example data file (copy and customize)
├── resume_template.html             # Default template (blue theme)
├── resume_template_minimalist.html  # Minimalist design (grayscale)
├── resume_template_modern.html      # Modern sidebar design (purple gradient)
├── resume_template_classic.html     # Classic professional (forest green)
├── pyproject.toml                   # UV project configuration
└── output/                          # Generated PDFs (created automatically)
```

## Quick Start

### 1. Create Your Data File

Copy the example and fill in your information:

```bash
cp resume_data.example.json my_resume.json
```

Edit `my_resume.json` with your personal details, experience, skills, etc.

### 2. Generate Your Resume

```bash
# Using default template
uv run generate_resume.py -d my_resume.json

# Using a specific template
uv run generate_resume.py -d my_resume.json -t modern

# Custom output path
uv run generate_resume.py -d my_resume.json -o ~/Documents/Resume.pdf
```

### 3. Available Templates

```bash
uv run generate_resume.py --list-templates
```

- `default` - Blue theme with modern styling
- `minimalist` - Clean grayscale design
- `modern` - Bold sidebar with purple gradient
- `classic` - Traditional serif with forest green accents

## Usage

### Command-Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--data PATH` | `-d` | JSON data file with resume content |
| `--template NAME` | `-t` | Template style (default, minimalist, modern, classic) |
| `--output PATH` | `-o` | Output PDF file path |
| `--meta KEY=VALUE` | `-m` | Set PDF metadata (can be used multiple times) |
| `--hidden-text TEXT` | `-s` | Custom hidden text embedded in the resume (background-colored, smallest font) |
| `--verbose` | `-v` | Show verbose output |
| `--list-templates` | | List available templates |
| `--help` | `-h` | Show help message |

### Examples

```bash
# Generate with default template
uv run generate_resume.py -d my_resume.json

# Use modern template with custom output
uv run generate_resume.py -d my_resume.json -t modern -o Modern_Resume.pdf

# Generate multiple versions
uv run generate_resume.py -d my_resume.json -t default -o Resume_Default.pdf
uv run generate_resume.py -d my_resume.json -t classic -o Resume_Classic.pdf
uv run generate_resume.py -d my_resume.json -t modern -o Resume_Modern.pdf

# Verbose mode
uv run generate_resume.py -d my_resume.json -v

# Add hidden text (invisible, for ATS keywords etc.)
uv run generate_resume.py -d my_resume.json -s "additional keywords here"

# Set PDF metadata
uv run generate_resume.py -d my_resume.json -m "author=John Doe" -m "title=Resume"

# Set multiple keywords (comma-separated)
uv run generate_resume.py -d my_resume.json -m "keywords=python,developer,senior"
```

### PDF Metadata

The `-m` / `--meta` option sets PDF document properties that are visible in PDF readers under "Document Properties". Each key=value pair sets one property.

**Supported metadata keys:**

| Key | Description |
|-----|-------------|
| `title` | PDF document title |
| `author` | Document author name |
| `subject` | Document subject/description |
| `keywords` | Comma-separated keywords for searchability |
| `creator` | Creating application name |
| `producer` | PDF producer name |

## JSON Data Format

The resume data file uses the following structure:

```json
{
  "name": "Your Name",
  "title": "Your Job Title",
  "contact": {
    "email": "your.email@example.com",
    "linkedin": "linkedin.com/in/yourprofile",
    "location": "City, Country",
    "phone": "+1 234 567 8900",
    "website": "yourwebsite.com"
  },
  "summary": "Your professional summary...",
  "experience": [
    {
      "company": "Company Name",
      "title": "Job Title",
      "start_date": "Jan 2020",
      "end_date": "Present",
      "highlights": [
        {"label": "Achievement:", "description": "Description here"},
        {"label": "", "description": "Another bullet point"}
      ]
    }
  ],
  "skills": ["Skill 1", "Skill 2", "Skill 3"],
  "certifications": ["Cert 1", "Cert 2"],
  "certifications_title": "Certifications",
  "education": [
    {
      "school": "University Name",
      "degree": "Degree, Field of Study",
      "start_year": "2010",
      "end_year": "2014"
    }
  ]
}
```

### Data Fields

| Field | Required | Description |
|-------|----------|-------------|
| `name` | Yes | Your full name |
| `title` | Yes | Professional title/headline |
| `contact` | Yes | Contact information object |
| `contact.email` | No | Email address |
| `contact.linkedin` | No | LinkedIn profile URL |
| `contact.location` | No | City, Country |
| `contact.phone` | No | Phone number |
| `contact.website` | No | Personal website |
| `summary` | Yes | Professional summary paragraph |
| `experience` | Yes | Array of work experience |
| `skills` | Yes | Array of skill strings |
| `certifications` | No | Array of certification strings |
| `certifications_title` | No | Custom title for certifications section |
| `education` | Yes | Array of education entries |

### Experience Entry Format

Each experience entry can use either bullet points or a description:

```json
// With bullet points (highlights)
{
  "company": "Company Name",
  "title": "Job Title",
  "start_date": "Jan 2020",
  "end_date": "Present",
  "highlights": [
    {"label": "Leadership:", "description": "Led a team of 5 engineers"},
    {"label": "", "description": "Implemented new features"}
  ]
}

// With plain description
{
  "company": "Company Name",
  "title": "Job Title",
  "start_date": "Jun 2018",
  "end_date": "Dec 2019",
  "description": "Brief description of responsibilities and achievements"
}
```

## Template Customization

### Modifying Colors

Each template has CSS variables you can customize:

**Default (Blue):**
```css
color: #2c3e50;  /* Primary - headers */
color: #3498db;  /* Accent - highlights */
```

**Modern (Purple):**
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

**Classic (Green):**
```css
color: #1a4d2e;  /* Forest green */
```

### Creating Custom Templates

1. Copy an existing template
2. Modify the CSS styling
3. Keep the Jinja2 template variables intact
4. Use with `-t` by adding to `TEMPLATES` in `generate_resume.py`

## Dependencies

- **Python**: 3.14+ (via pyenv/uv)
- **jinja2**: Template rendering
- **weasyprint**: HTML to PDF conversion
- **pypdf**: PDF utilities

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for Python package management:

```bash
# Clone the repository
git clone <repository-url>
cd resume-builder

# Dependencies are managed by uv automatically
uv run generate_resume.py --help
```

## Troubleshooting

### Data File Not Found
```
Error: Data file not found: /path/to/file.json
```
Ensure the path to your JSON file is correct.

### Invalid JSON
```
Error: Invalid JSON in data file
```
Validate your JSON syntax at [jsonlint.com](https://jsonlint.com).

### Font Warnings
```
Unable to revert mtime: /Library/Fonts
```
This is a harmless WeasyPrint warning. The PDF generates correctly.

### Missing Fields
If required fields are missing, the template may render with empty sections. Check your JSON has all required fields.

## Version History

### v2.0
- Complete rewrite with Jinja2 templating
- JSON-based data input
- Removed hardcoded personal information
- All templates now data-driven
- New CLI interface with template selection

### v1.x
- Initial implementation with hardcoded content
- Multiple design variants
- Basic CLI arguments

## License

MIT License - Feel free to use and modify for your own resumes.
