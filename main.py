#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "pillow",   # For image handling
#     "mistralai",  # Mistral AI client
#     "python-dotenv",  # For environment variables
#     "pnglatex",  # For rendering LaTeX to PNG
# ]
# ///
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
import base64

from dotenv import load_dotenv
from mistralai import Mistral
from PIL import Image
from pnglatex import pnglatex

def encode_image_to_base64(image_path: str) -> str:
    """
    Encode an image file to base64.
    
    Args:
        image_path: Path to the image file
    
    Returns:
        str: Base64 encoded image data
    """
    try:
        # First verify the image can be opened
        with Image.open(image_path) as img:
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img.convert('RGB')
            # Save as high-quality PNG
            img.save(image_path, 'PNG', quality=95)
        
        # Now encode the processed image
        with open(image_path, "rb") as image_file:
            return base64.b64encode(image_file.read()).decode('utf-8')
    except FileNotFoundError:
        print(f"Error: The file {image_path} was not found.")
        return None
    except Exception as e:
        print(f"Error encoding image: {e}")
        return None

def process_image(image_path: str) -> str:
    """
    Process an image using Mistral's OCR capabilities.
    
    Args:
        image_path: Path to the image file
    
    Returns:
        str: Extracted text from the image
    """
    # Initialize Mistral client
    client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
    
    # Encode image to base64
    base64_image = encode_image_to_base64(image_path)
    if not base64_image:
        return "Error: Failed to encode image"
    
    # Make the API call
    try:
        print(f"Processing image: {image_path}")
        response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "image_url",
                "image_url": f"data:image/png;base64,{base64_image}"
            }
        )
        
        # Debug response
        print(f"OCR Response: {response}")
        print(f"Number of pages: {len(response.pages)}")
        for i, page in enumerate(response.pages):
            print(f"Page {i} content: '{page.markdown}'")
            print(f"Page {i} dimensions: {page.dimensions}")
        
        # Extract the text from the response
        if not response.pages:
            return "Error: No text found in image"
            
        # Combine text from all pages
        extracted_text = "\n".join(
            page.markdown.strip()
            for page in response.pages
            if page.markdown and page.markdown.strip()
        )
        return extracted_text if extracted_text else "No text found in image"
        
    except Exception as e:
        error_msg = str(e)
        if "Document content must be a URL" in error_msg:
            return ("Error: Mistral OCR currently only supports HTTPS URLs. "
                   "Please use an image hosting service and provide a direct HTTPS URL to the image.")
        return f"Error processing image: {error_msg}" 

# Define the directory for saving LaTeX renders
LATEX_RENDERS_DIR = Path.home() / "Pictures" / "latex-renders"

def send_notification(title: str, message: str, urgency: str = "normal"):
    """
    Send a desktop notification using notify-send.
    
    Args:
        title: Notification title
        message: Notification message
        urgency: Notification urgency (low, normal, critical)
    """
    try:
        subprocess.run([
            'notify-send',
            f'--urgency={urgency}',
            '--app-name=Mistral OCR',
            title,
            message
        ], check=True)
    except subprocess.CalledProcessError:
        print("\nCouldn't send notification. Please install notify-send:")
        print("sudo apt install libnotify-bin     # For Ubuntu/Debian")
        print("sudo pacman -S libnotify           # For Arch Linux")
    except Exception as e:
        print(f"\nError sending notification: {e}")

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
            send_notification(
                "Screenshot Failed",
                "No screenshot was taken or the file is empty",
                "critical"
            )
            return None
    except subprocess.CalledProcessError:
        print("Error running Flameshot. Please make sure it's installed:")
        print("sudo apt install flameshot  # For Ubuntu/Debian")
        print("sudo pacman -S flameshot    # For Arch Linux")
        send_notification(
            "Screenshot Failed",
            "Error running Flameshot. Please make sure it's installed.",
            "critical"
        )
        return None
    except Exception as e:
        print(f"Error capturing screenshot: {e}")
        send_notification(
            "Screenshot Failed",
            f"Error capturing screenshot: {e}",
            "critical"
        )
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

def render_latex(text: str) -> Path:
    """
    Render LaTeX code to PNG.
    
    Args:
        text: LaTeX code to render
        
    Returns:
        Path: Path to the rendered PNG file, or None if rendering failed
    """
    try:
        # Create output directory if it doesn't exist
        LATEX_RENDERS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Create a filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = LATEX_RENDERS_DIR / f"latex_render_{timestamp}.png"
        
        # Ensure the text is properly wrapped in math mode if it isn't already
        if not any(text.strip().startswith(p) for p in [r'\[', '$$', '$']):
            text = r'\[' + text + r'\]'
        
        # Render the LaTeX code
        output_path = pnglatex(text, str(output_file))
        print(f"\nLaTeX render saved to: {output_path}")
        return output_path if output_path.exists() else None
        
    except Exception as e:
        print(f"Error rendering LaTeX: {e}")
        send_notification(
            "LaTeX Rendering Failed",
            f"Error rendering LaTeX: {e}",
            "critical"
        )
        return None

def main():
    # Load environment variables
    load_dotenv()
    
    # Check for Mistral API key
    if not os.getenv("MISTRAL_API_KEY"):
        print("Error: MISTRAL_API_KEY environment variable not set")
        send_notification(
            "Configuration Error",
            "MISTRAL_API_KEY environment variable not set",
            "critical"
        )
        sys.exit(1)
    
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
        
        if not text or text == "No text found in image":
            send_notification(
                "OCR Failed",
                "No text could be extracted from the image",
                "critical"
            )
            sys.exit(1)
        
        success_msg = "Text extracted and copied to clipboard"
        latex_detected = False
        
        # Check if the text looks like LaTeX
        if looks_like_latex(text):
            print("\nDetected LaTeX code! Rendering...")
            rendered_path = render_latex(text)
            
            if rendered_path:
                # Open the rendered image with the default image viewer
                try:
                    subprocess.run(['xdg-open', str(rendered_path)], check=True)
                    print("Rendered LaTeX opened in image viewer!")
                    latex_detected = True
                    success_msg += f"\nLaTeX rendered and saved to: {rendered_path.name}"
                except subprocess.CalledProcessError:
                    print("Couldn't open the rendered image. The file is saved at:", rendered_path)
        
        # Copy to clipboard if there's text
        try:
            subprocess.run(['xclip', '-selection', 'clipboard'], 
                         input=text.encode(), 
                         check=True)
            print("\nText copied to clipboard!")
            
            # Send success notification
            send_notification(
                "OCR Successful",
                success_msg,
                "normal"
            )
        except subprocess.CalledProcessError:
            print("\nCouldn't copy to clipboard. Please install xclip:")
            print("sudo apt install xclip     # For Ubuntu/Debian")
            print("sudo pacman -S xclip       # For Arch Linux")
            send_notification(
                "Clipboard Error",
                "Text extracted but couldn't be copied to clipboard",
                "critical"
            )
    except Exception as e:
        print(f"Error: {e}")
        send_notification(
            "OCR Failed",
            f"Error processing image: {e}",
            "critical"
        )
    finally:
        # Clean up the screenshot file
        image_path.unlink(missing_ok=True)

if __name__ == "__main__":
    main() 
