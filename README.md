# Mistral OCR Desktop Tool

A Python script that combines Flameshot's screen capture capabilities with Mistral's OCR to extract and process text from screen captures. It also includes automatic LaTeX rendering for mathematical expressions.

## Features

- Screen area selection using Flameshot
- Text extraction using Mistral OCR
- Automatic LaTeX detection and rendering using Matplotlib
- Automatic clipboard copying of extracted text
- Saves rendered LaTeX equations as PNG files
- Desktop notifications for success and error states

## Requirements

### System Dependencies

```bash
# For Ubuntu/Debian
sudo apt install flameshot xclip libnotify-bin

# For Arch Linux
sudo pacman -S flameshot xclip libnotify
```

### Python Dependencies

Install the required Python packages:

```bash
pip install pillow mistralai python-dotenv matplotlib
```

## Setup

1. Clone this repository
2. Create a `.env` file with your Mistral API key:
   ```
   MISTRAL_API_KEY=your_api_key_here
   ```

## Usage

1. Make the script executable (optional):

   ```bash
   chmod +x main.py
   ```

2. Run the script:

   ```bash
   # If made executable:
   ./main.py

   # Or using Python directly:
   python main.py
   ```

3. The workflow:
   - Flameshot will open for screen area selection
   - Select the area containing text or LaTeX equations
   - The text will be extracted and copied to your clipboard
   - If LaTeX is detected:
     - It will be rendered as a PNG image using Matplotlib
     - The image will open in your default viewer
     - The render will be saved in `~/Pictures/latex-renders/`
   - Desktop notifications will inform you of success or any errors

## Output Locations

- LaTeX renders are saved in: `~/Pictures/latex-renders/`
- Each render is saved with a timestamp: `latex_render_YYYYMMDD_HHMMSS.png`

## Features in Detail

- Uses Mistral AI's OCR API for text extraction
- Integrates with Flameshot for screen capture
- Uses Matplotlib for high-quality LaTeX rendering
- Desktop notifications via libnotify
- Written in Python with type hints
- Follows modern Python practices

