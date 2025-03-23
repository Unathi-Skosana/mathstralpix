# Mistral OCR Desktop Tool

A desktop tray application that allows you to extract text from any area of your screen using Mistral OCR.

## Features

- System tray icon for easy access
- Screen area selection
- Text extraction using Mistral OCR
- Copy results to clipboard
- Modern Qt-based UI

## Installation

1. Make sure you have Python 3.8+ installed
2. Install uv (if not already installed):
   ```bash
   pip install uv
   ```
3. Clone this repository
4. Create a virtual environment and install dependencies:
   ```bash
   uv venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   uv pip install -r requirements.txt
   ```
5. Create a `.env` file with your Mistral API key:
   ```
   MISTRAL_API_KEY=your_api_key_here
   ```

## Usage

1. Run the application:
   ```bash
   python src/main.py
   ```
2. Click the tray icon to start capture
3. Select an area on your screen
4. The extracted text will be displayed in a window and copied to your clipboard

## Development

- Built with PySide6 for the GUI
- Uses MSS for screen capture
- Integrates with Mistral API for OCR
- Modern Python practices and type hints 