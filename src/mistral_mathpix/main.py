#!/usr/bin/env python3
import os
import sys
import subprocess
import tempfile
import re
from pathlib import Path
from dotenv import load_dotenv
from pnglatex import pnglatex
from mistral_mathpix.ocr_processor import process_image

def capture_screen() -> Path:
    """
    Use Flameshot to capture a screen area and save it to a temporary file.
    
    Returns:
        Path: Path to the captured image file
    """
    # Create a temporary file for the screenshot
    temp_file = Path(tempfile.mktemp(suffix='.png'))
    
    try:
        # Run Flameshot in GUI mode and save to the temporary file
        subprocess.run(['flameshot', 'gui', '--raw'], 
                      stdout=open(temp_file, 'wb'),
                      check=True)
        
        # Check if the file was created and has content
        if temp_file.exists() and temp_file.stat().st_size > 0:
            return temp_file
        else:
            print("No screenshot was taken or the file is empty")
            return None
    except subprocess.CalledProcessError:
        print("Error running Flameshot. Please make sure it's installed:")
        print("sudo apt install flameshot  # For Ubuntu/Debian")
        print("sudo pacman -S flameshot    # For Arch Linux")
        return None
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        return None

def looks_like_latex(text: str) -> bool:
    """
    Check if the text appears to be LaTeX code.
    
    Args:
        text: Text to check
        
    Returns:
        bool: True if text appears to be LaTeX
    """
    # Common LaTeX patterns
    latex_patterns = [
        r'\\[a-zA-Z]+{',  # Commands with braces
        r'\\[a-zA-Z]+\[',  # Commands with optional arguments
        r'\$\$.*\$\$',    # Display math mode
        r'\$.*\$',        # Inline math mode
        r'\\begin{.*}',   # Environment begin
        r'\\end{.*}',     # Environment end
        r'\\[',           # Display math mode
        r'\\]',           # Display math mode
        r'\\(',           # Inline math mode
        r'\\)',           # Inline math mode
    ]
    
    # Check if any pattern matches
    return any(re.search(pattern, text) for pattern in latex_patterns)

def render_latex(text: str, output_dir: Path) -> Path:
    """
    Render LaTeX code to PNG.
    
    Args:
        text: LaTeX code to render
        output_dir: Directory to save the rendered PNG
        
    Returns:
        Path: Path to the rendered PNG file, or None if rendering failed
    """
    try:
        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create a temporary file for the rendered image
        output_file = output_dir / "latex_render.png"
        
        # Ensure the text is properly wrapped in math mode if it isn't already
        if not any(text.strip().startswith(p) for p in [r'\[', '$$', '$']):
            text = r'\[' + text + r'\]'
        
        # Render the LaTeX code
        output_path = pnglatex(text, str(output_file))
        return output_path if output_path.exists() else None
        
    except Exception as e:
        print(f"Error rendering LaTeX: {e}")
        return None

def main():
    # Load environment variables
    load_dotenv()
    
    # Check for Mistral API key
    if not os.getenv("MISTRAL_API_KEY"):
        print("Error: MISTRAL_API_KEY environment variable not set")
        sys.exit(1)
    
    # Create temporary directory for rendered LaTeX
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_dir_path = Path(temp_dir)
        
        # Capture screen area
        image_path = capture_screen()
        if not image_path:
            sys.exit(1)
        
        try:
            # Process the image with OCR
            text = process_image(str(image_path))
            print("\nExtracted Text:")
            print("--------------")
            print(text)
            
            # Check if the text looks like LaTeX
            if text and text != "No text found in image" and looks_like_latex(text):
                print("\nDetected LaTeX code! Rendering...")
                rendered_path = render_latex(text, temp_dir_path)
                
                if rendered_path:
                    # Open the rendered image with the default image viewer
                    try:
                        subprocess.run(['xdg-open', str(rendered_path)], check=True)
                        print("Rendered LaTeX opened in image viewer!")
                    except subprocess.CalledProcessError:
                        print("Couldn't open the rendered image. The file is saved at:", rendered_path)
            
            # Copy to clipboard if there's text
            if text and text != "No text found in image":
                try:
                    subprocess.run(['xclip', '-selection', 'clipboard'], 
                                 input=text.encode(), 
                                 check=True)
                    print("\nText copied to clipboard!")
                except subprocess.CalledProcessError:
                    print("\nCouldn't copy to clipboard. Please install xclip:")
                    print("sudo apt install xclip     # For Ubuntu/Debian")
                    print("sudo pacman -S xclip       # For Arch Linux")
        finally:
            # Clean up the screenshot file
            image_path.unlink(missing_ok=True)

if __name__ == "__main__":
    main() 
