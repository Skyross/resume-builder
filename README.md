# Resume Builder

[![CI](https://github.com/skyross/resume-builder/actions/workflows/ci.yml/badge.svg)](https://github.com/skyross/resume-builder/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/skyross/resume-builder/graph/badge.svg)](https://codecov.io/gh/skyross/resume-builder)
[![Python 3.14+](https://img.shields.io/badge/python-3.14+-blue.svg)](https://www.python.org/downloads/)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A data-driven resume generator that creates professional PDF resumes from customizable HTML templates.

## Features

- **4 Professional Templates**: Default (blue), Minimalist (grayscale), Modern (purple sidebar), Classic (green serif)
- **JSON Data Input**: Keep your resume content separate from styling
- **Jinja2 Templating**: Flexible, powerful template system
- **High-Quality PDFs**: WeasyPrint produces print-ready output
- **Easy Customization**: Modify templates or create your own

## Quick Start

```bash
# 1. Create your data file
cp resume_data.example.json my_resume.json
# Edit my_resume.json with your information

# 2. Generate your resume
uv run generate_resume.py -d my_resume.json

# 3. Try different templates
uv run generate_resume.py -d my_resume.json -t modern
uv run generate_resume.py -d my_resume.json -t classic
uv run generate_resume.py -d my_resume.json -t minimalist
```

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for Python package management:

```bash
git clone <repository-url>
cd resume-builder
uv run generate_resume.py --help
```

## Usage

```bash
# Basic usage
uv run generate_resume.py -d my_resume.json

# Choose a template
uv run generate_resume.py -d my_resume.json -t modern

# Custom output path
uv run generate_resume.py -d my_resume.json -o ~/Desktop/Resume.pdf

# List available templates
uv run generate_resume.py --list-templates

# Verbose output
uv run generate_resume.py -d my_resume.json -v
```

## Command-Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--data PATH` | `-d` | JSON data file with resume content |
| `--template NAME` | `-t` | Template: default, minimalist, modern, classic |
| `--output PATH` | `-o` | Output PDF path (default: output/resume.pdf) |
| `--meta KEY=VALUE` | `-m` | Set PDF metadata (can be used multiple times) |
| `--hidden-text TEXT` | `-s` | Hidden text (background-colored, 1px font) |
| `--verbose` | `-v` | Show detailed output |
| `--list-templates` | | List all available templates |

### PDF Metadata

Set PDF document properties using `-m` / `--meta`:

```bash
# Set author and title
uv run generate_resume.py -d my_resume.json -m "author=John Doe" -m "title=Resume"

# Set keywords for searchability
uv run generate_resume.py -d my_resume.json -m "keywords=python,developer,senior"
```

Supported metadata keys: `title`, `author`, `subject`, `keywords`, `creator`, `producer`

## Templates

| Template | Style | Best For |
|----------|-------|----------|
| `default` | Blue, modern | Tech companies, startups |
| `minimalist` | Grayscale, clean | Design-conscious orgs |
| `modern` | Purple sidebar, bold | Creative roles |
| `classic` | Green, serif | Corporate, finance |

See [DESIGN_VARIANTS.md](DESIGN_VARIANTS.md) for detailed template comparison.

## Data Format

Create a JSON file with your resume content:

```json
{
  "name": "Your Name",
  "title": "Your Job Title",
  "contact": {
    "email": "email@example.com",
    "linkedin": "linkedin.com/in/profile",
    "location": "City, Country"
  },
  "summary": "Professional summary...",
  "experience": [...],
  "skills": [...],
  "certifications": [...],
  "education": [...]
}
```

See `resume_data.example.json` for a complete example.

## Documentation

- **[CLAUDE.md](CLAUDE.md)** - Full documentation with JSON schema details
- **[DESIGN_VARIANTS.md](DESIGN_VARIANTS.md)** - Template comparison and recommendations

## Dependencies

- Python 3.14+
- jinja2
- weasyprint
- pypdf

## License

MIT License
