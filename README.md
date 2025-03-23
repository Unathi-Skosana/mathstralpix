# Mistral OCR Desktop Tool

A command-line tool that combines Flameshot's screen capture capabilities with Mistral's OCR to extract and process text from screen captures. It also includes automatic LaTeX rendering for mathematical expressions.

## Features

- Screen area selection using Flameshot
- Text extraction using Mistral OCR
- Automatic LaTeX detection and rendering
- Automatic clipboard copying of extracted text
- Saves rendered LaTeX equations as PNG files

## Requirements

### System Dependencies

```bash
# For Ubuntu/Debian
sudo apt install flameshot xclip texlive-full

# For Arch Linux
sudo pacman -S flameshot xclip texlive-most
```

### Python Setup

1. Make sure you have Python 3.8+ installed
2. Install uv (if not already installed):
   ```bash
   pip install uv
   ```

## Installation

1. Clone this repository
2. Create a virtual environment and install dependencies:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -e .
   ```
3. Create a `.env` file with your Mistral API key:
   ```
   MISTRAL_API_KEY=your_api_key_here
   ```

## Usage

1. Run the application:
   ```bash
   python -m mistral_mathpix.main
   ```

2. The workflow:
   - Flameshot will open for screen area selection
   - Select the area containing text or LaTeX equations
   - The text will be extracted and copied to your clipboard
   - If LaTeX is detected:
     - It will be rendered as a PNG image
     - The image will open in your default viewer
     - The render will be saved in `~/pix/latex-renders/`

## Output Locations

- LaTeX renders are saved in: `~/pix/latex-renders/`
- Each render is saved with a timestamp: `latex_render_YYYYMMDD_HHMMSS.png`

## Development

- Uses Mistral AI's OCR API for text extraction
- Integrates with Flameshot for screen capture
- Uses pnglatex for LaTeX rendering
- Written in Python with type hints
- Follows modern Python practices 