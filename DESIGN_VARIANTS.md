# Resume Design Variants

This document describes the four design variants available for your resume.

## Overview

All four variants use the same JSON data but with different visual presentations to suit different contexts and industries.

## Variant 1: Default (Blue Theme)

**Template:** `resume_template.html`
**CLI Option:** `-t default`

### Design Characteristics
- **Style:** Modern, professional
- **Font:** Segoe UI (sans-serif)
- **Colors:** Navy blue and bright blue accents
- **Layout:** Single column, traditional top-down flow

### Key Features
- Clean section separators with blue borders
- 3-column skills grid
- Blue accent highlights
- Professional header with contact row

### Best For
- Technology companies
- Software engineering roles
- Startups
- General professional use

### Color Palette
- Primary: `#2c3e50` (Navy blue)
- Accent: `#3498db` (Bright blue)
- Background: `#ecf0f1` (Light gray)

## Variant 2: Minimalist (Grayscale)

**Template:** `resume_template_minimalist.html`
**CLI Option:** `-t minimalist`

### Design Characteristics
- **Style:** Clean, modern, minimal
- **Font:** Helvetica Neue, Arial (sans-serif)
- **Colors:** Black, gray, subtle accents
- **Layout:** Single column, traditional top-down flow

### Key Features
- Ultra-light typography (300 weight header)
- Subtle gray tones and thin borders
- Generous white space
- 4-column skills grid
- Clean section separators (1px lines)

### Best For
- Tech startups and modern companies
- Design-conscious organizations
- Companies valuing simplicity
- ATS-friendly applications

### Color Palette
- Headers: `#000` (Black)
- Body text: `#2c2c2c` (Dark gray)
- Accents: `#666` (Medium gray)
- Backgrounds: `#f8f9fa` (Light gray)
- Borders: `#e0e0e0` (Border gray)

## Variant 3: Modern Sidebar (Purple Gradient)

**Template:** `resume_template_modern.html`
**CLI Option:** `-t modern`

### Design Characteristics
- **Style:** Bold, contemporary, creative
- **Font:** Segoe UI (sans-serif)
- **Colors:** Purple gradient sidebar, vibrant accents
- **Layout:** Two-column with colored sidebar

### Key Features
- Eye-catching purple gradient sidebar (left)
- Skills, certifications, and contact in sidebar
- White main content area (right)
- Rounded skill badges
- Modern glassmorphism effects

### Best For
- Creative tech companies
- Startups with modern branding
- Design-forward organizations
- Standing out in competitive pools

### Color Palette
- Gradient: `#667eea` to `#764ba2` (Purple gradient)
- Headers: `#667eea` (Accent purple)
- Sidebar: White text on gradient
- Skill badges: Semi-transparent white
- Body text: `#444` (Dark gray)

## Variant 4: Classic Professional (Forest Green)

**Template:** `resume_template_classic.html`
**CLI Option:** `-t classic`

### Design Characteristics
- **Style:** Traditional, corporate, formal
- **Font:** Georgia, Times New Roman (serif)
- **Colors:** Forest green accents, professional
- **Layout:** Single column, centered header

### Key Features
- Serif typography for traditional feel
- Double-line border under header
- Centered, formal header layout
- Forest green accent color
- Text indentation on summary
- Bullet points with custom markers

### Best For
- Corporate environments
- Finance, consulting, legal sectors
- Traditional industries
- Conservative organizations
- Government positions

### Color Palette
- Primary: `#1a4d2e` (Forest green)
- Secondary: `#2c5f2d` (Medium green)
- Body text: `#1a1a1a` (Near black)
- Backgrounds: `#f5f5f5` (Off-white)
- Borders: Forest green double lines

## Comparison Table

| Feature | Default | Minimalist | Modern | Classic |
|---------|---------|------------|--------|---------|
| **Layout** | Single column | Single column | Two column | Single column |
| **Font Style** | Sans-serif | Sans-serif | Sans-serif | Serif |
| **Color Scheme** | Blue | Grayscale | Purple gradient | Forest green |
| **Personality** | Professional | Clean, modern | Creative, bold | Traditional |
| **ATS-Friendly** | Excellent | Excellent | Good | Excellent |
| **Visual Impact** | Medium | Subtle | High | Professional |

## How to Generate Each Variant

```bash
# Default (Blue)
uv run generate_resume.py -d my_resume.json -t default -o Resume_Default.pdf

# Minimalist (Grayscale)
uv run generate_resume.py -d my_resume.json -t minimalist -o Resume_Minimalist.pdf

# Modern (Purple Sidebar)
uv run generate_resume.py -d my_resume.json -t modern -o Resume_Modern.pdf

# Classic (Forest Green)
uv run generate_resume.py -d my_resume.json -t classic -o Resume_Classic.pdf
```

## Recommendations by Industry

### Technology & Startups
1. Modern (first choice for creative roles)
2. Default (safe choice)
3. Minimalist (design-focused companies)

### Finance & Consulting
1. Classic (first choice)
2. Minimalist (modern alternative)
3. Default (acceptable)

### Design & Creative
1. Modern (first choice)
2. Minimalist (clean alternative)
3. Default (fallback)

### Enterprise & Corporate
1. Classic (first choice)
2. Default (modern option)
3. Minimalist (acceptable)

## Customization Tips

### Changing Colors

**Default:** Edit blue values in CSS
```css
color: #2c3e50;  /* Primary */
color: #3498db;  /* Accent */
```

**Minimalist:** Edit grayscale values
```css
color: #666;     /* Accent */
border: #e0e0e0; /* Borders */
```

**Modern:** Modify gradient colors
```css
background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
```

**Classic:** Change forest green
```css
color: #1a4d2e;  /* Primary */
```

### Adjusting Layout

**Single Column (Default/Minimalist/Classic):**
```css
.container {
    max-width: 850px;
    padding: 40px;
}
```

**Two Column (Modern):**
```css
.sidebar { width: 280px; }
.main-content { flex: 1; }
```

### Typography Changes

Each variant uses different font stacks:
- **Default:** `'Segoe UI', Tahoma, Geneva, Verdana, sans-serif`
- **Minimalist:** `'Helvetica Neue', Arial, sans-serif`
- **Modern:** `'Segoe UI', Tahoma, Geneva, Verdana, sans-serif`
- **Classic:** `Georgia, 'Times New Roman', serif`
