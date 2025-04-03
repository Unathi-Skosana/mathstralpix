A poor man's version of [Mathpix](https://mathpix.com/) using Mistral's OCR API.

## System Dependencies

- flameshot - for screen capture
- xclip - for clipboard operations
- libnotify-bin/libnotify - for desktop notifications
- texlive-core/pdflatex - for LaTeX rendering
- poppler/pdftoppm - for PDF to image conversion

## Setup

1. Create a `.env` file with your Mistral API key:

   ```
   MISTRAL_API_KEY=your_api_key_here
   ```

2. Run the script:
   ```bash
   uv run main.py
   ```

