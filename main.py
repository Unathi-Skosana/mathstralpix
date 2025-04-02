#!/usr/bin/env python3
# /// script
# requires-python = ">=3.8"
# dependencies = [
#     "pillow",   # For image handling
#     "mistralai",  # Mistral AI client
#     "python-dotenv",  # For environment variables
#     "pylatexenc",  # For LaTeX to unicode conversion
#     "kivy",  # For modern UI
# ]
# ///
import os
import re
import subprocess
import sys
import tempfile
import threading
from datetime import datetime
from pathlib import Path
import base64

from dotenv import load_dotenv
from mistralai import Mistral
from PIL import Image

# Kivy imports
os.environ['KIVY_NO_CONSOLELOG'] = '1'  # Reduce console output
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.image import Image as KivyImage
from kivy.uix.popup import Popup
from kivy.core.clipboard import Clipboard
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.properties import StringProperty, ObjectProperty, BooleanProperty

# Define the directory for saving LaTeX renders
LATEX_RENDERS_DIR = Path.home() / "pix" / "latex-renders"

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

def sanitize_latex(text: str) -> str:
    """
    Sanitize LaTeX input to prevent common rendering errors.
    
    Args:
        text: Raw LaTeX text
        
    Returns:
        str: Sanitized LaTeX text
    """
    # Remove any document environments
    text = re.sub(r'\\begin{document}.*?\\end{document}', '', text, flags=re.DOTALL)
    text = re.sub(r'\\documentclass.*?\n', '', text)
    
    # Remove any standalone \begin{document} or \end{document}
    text = re.sub(r'\\begin{document}', '', text)
    text = re.sub(r'\\end{document}', '', text)
    
    # Replace aligned environment with align environment
    text = re.sub(r'\\begin{aligned}', r'\\begin{align}', text)
    text = re.sub(r'\\end{aligned}', r'\\end{align}', text)
    
    # Ensure math environments are properly closed
    environments = ['align', 'equation', 'matrix', 'bmatrix', 'cases']
    for env in environments:
        # Count occurrences of \begin and \end for this environment
        begins = len(re.findall(fr'\\begin{{{env}}}', text))
        ends = len(re.findall(fr'\\end{{{env}}}', text))
        
        # If there are unmatched environments, remove them
        if begins != ends:
            text = re.sub(fr'\\begin{{{env}}}|\\end{{{env}}}', '', text)
    
    # Clean up any leftover newlines and spaces
    text = re.sub(r'\s+', ' ', text)
    text = text.strip()
    
    return text

class LatexEditorApp(App):
    """
    Kivy application for LaTeX equation editing and rendering
    """
    def __init__(self, latex_text="", **kwargs):
        super(LatexEditorApp, self).__init__(**kwargs)
        self.latex_text = sanitize_latex(latex_text)
        self.output_file = None
        self.result_callback = None
        
    def set_callback(self, callback):
        """Set a callback function to run when closing"""
        self.result_callback = callback
    
    def build(self):
        self.title = 'LaTeX Equation Editor'
        Window.size = (900, 700)
        Window.minimum_width, Window.minimum_height = 600, 500
        
        # Main layout
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        # Editor section
        editor_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.5))
        editor_layout.add_widget(Label(text='LaTeX Equation Editor',
                                       size_hint=(1, 0.1),
                                       font_size='18sp',
                                       halign='left'))
        
        # Clean the LaTeX for editing
        edited_text = self.latex_text
        if edited_text.startswith('$$') and edited_text.endswith('$$'):
            edited_text = edited_text[2:-2].strip()
        elif edited_text.startswith('$') and edited_text.endswith('$'):
            edited_text = edited_text[1:-1].strip()
        elif edited_text.startswith(r'\[') and edited_text.endswith(r'\]'):
            edited_text = edited_text[2:-2].strip()
        elif edited_text.startswith(r'\(') and edited_text.endswith(r'\)'):
            edited_text = edited_text[2:-2].strip()
        
        self.editor = TextInput(text=edited_text, multiline=True, 
                               font_name='RobotoMono-Regular')
        editor_layout.add_widget(self.editor)
        
        # Buttons section
        buttons_layout = BoxLayout(orientation='horizontal', 
                                  size_hint=(1, 0.1),
                                  spacing=10, padding=5)
        
        render_btn = Button(text='Render', size_hint=(1, 1))
        render_btn.bind(on_press=self.render_equation)
        buttons_layout.add_widget(render_btn)
        
        save_btn = Button(text='Save', size_hint=(1, 1))
        save_btn.bind(on_press=self.save_image)
        buttons_layout.add_widget(save_btn)
        
        copy_btn = Button(text='Copy LaTeX', size_hint=(1, 1))
        copy_btn.bind(on_press=self.copy_to_clipboard)
        buttons_layout.add_widget(copy_btn)
        
        reset_btn = Button(text='Reset', size_hint=(1, 1))
        reset_btn.bind(on_press=self.reset_editor)
        buttons_layout.add_widget(reset_btn)
        
        close_btn = Button(text='Close', size_hint=(1, 1))
        close_btn.bind(on_press=self.close_app)
        buttons_layout.add_widget(close_btn)
        
        # Preview section
        preview_layout = BoxLayout(orientation='vertical', size_hint=(1, 0.5))
        preview_layout.add_widget(Label(text='LaTeX Preview',
                                       size_hint=(1, 0.1),
                                       font_size='18sp',
                                       halign='left'))
        self.preview = KivyImage(size_hint=(1, 0.9))
        preview_layout.add_widget(self.preview)
        
        # Status bar
        self.status_bar = Label(text='Ready', size_hint=(1, 0.05), 
                               halign='left', valign='middle')
        self.status_bar.bind(size=self.status_bar.setter('text_size'))
        
        # Add all sections to main layout
        layout.add_widget(editor_layout)
        layout.add_widget(buttons_layout)
        layout.add_widget(preview_layout)
        layout.add_widget(self.status_bar)
        
        # Auto-render on start
        Clock.schedule_once(lambda dt: self.render_equation(None), 0.5)
        
        return layout
    
    def render_equation(self, instance):
        """Render the LaTeX equation"""
        self.status_bar.text = "Rendering equation..."
        
        # Run rendering in a separate thread to avoid blocking UI
        threading.Thread(target=self._render_thread, daemon=True).start()
    
    def _render_thread(self):
        try:
            # Get the LaTeX code from the editor
            latex = self.editor.text.strip()
            
            # Create a temporary directory for rendering
            with tempfile.TemporaryDirectory() as tmpdir:
                temp_dir = Path(tmpdir)
                tex_file = temp_dir / "equation.tex"
                
                # Wrap in math mode if not already
                if not any(latex.startswith(p) for p in ['$', r'\[', r'\begin{']):
                    # Use display math mode
                    latex_content = f"${latex}$"
                else:
                    latex_content = latex
                
                # Create a minimal LaTeX document
                tex_content = r"""
\documentclass[preview,border=10pt]{standalone}
\usepackage{amsmath}
\usepackage{amsfonts}
\usepackage{amssymb}
\usepackage{color}
\begin{document}
""" + latex_content + r"""
\end{document}
"""
                
                # Write the tex file
                tex_file.write_text(tex_content)
                
                # Compile to PDF
                process = subprocess.run(
                    ['pdflatex', '-interaction=nonstopmode', str(tex_file.name)],
                    cwd=tmpdir,
                    capture_output=True,
                    text=True
                )
                
                if process.returncode != 0:
                    Clock.schedule_once(
                        lambda dt: self._update_status(
                            f"Error rendering LaTeX: {process.stderr}"
                        ), 0
                    )
                    return
                
                # Convert PDF to PNG for preview
                pdf_file = temp_dir / "equation.pdf"
                png_file = temp_dir / "equation.png"
                
                # Use pdftoppm for better quality
                try:
                    subprocess.run(
                        ['pdftoppm', '-png', '-r', '150', str(pdf_file), 
                         str(png_file).replace('.png', '')],
                        check=True,
                        capture_output=True
                    )
                    png_file = Path(str(png_file).replace('.png', '-1.png'))
                except:
                    # Fallback to convert
                    subprocess.run(
                        ['convert', '-density', '150', str(pdf_file), str(png_file)],
                        check=True,
                        capture_output=True
                    )
                
                # Save to permanent location
                if png_file.exists():
                    # Ensure output directory exists
                    LATEX_RENDERS_DIR.mkdir(parents=True, exist_ok=True)
                    
                    # Create output filename with timestamp
                    self.output_file = LATEX_RENDERS_DIR / f"latex_render_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    
                    # Copy to permanent location
                    with open(png_file, 'rb') as src_file:
                        with open(self.output_file, 'wb') as dst_file:
                            dst_file.write(src_file.read())
                    
                    # Update UI with the new image (must be done on main thread)
                    Clock.schedule_once(
                        lambda dt: self._update_preview(str(self.output_file)), 0
                    )
                    
                    Clock.schedule_once(
                        lambda dt: self._update_status(
                            f"Rendered equation saved to {self.output_file}"
                        ), 0
                    )
                else:
                    Clock.schedule_once(
                        lambda dt: self._update_status(
                            "Error: Could not generate preview image"
                        ), 0
                    )
        
        except Exception as e:
            Clock.schedule_once(
                lambda dt: self._update_status(f"Error: {str(e)}"), 0
            )
    
    def _update_preview(self, image_path):
        """Update the preview image (called on main thread)"""
        self.preview.source = image_path
        self.preview.reload()
    
    def _update_status(self, message):
        """Update the status bar (called on main thread)"""
        self.status_bar.text = message
    
    def save_image(self, instance):
        """Save the rendered equation to a file"""
        if hasattr(self, 'output_file') and self.output_file and self.output_file.exists():
            self.status_bar.text = f"Image saved to {self.output_file}"
            
            # Show a popup
            content = BoxLayout(orientation='vertical', padding=10, spacing=10)
            content.add_widget(Label(text=f"LaTeX render saved to:\n{self.output_file}"))
            
            btn = Button(text='OK', size_hint=(1, 0.3))
            content.add_widget(btn)
            
            popup = Popup(title='Image Saved',
                        content=content,
                        size_hint=(0.8, 0.3))
            
            # Dismiss the popup when the button is pressed
            btn.bind(on_press=popup.dismiss)
            
            popup.open()
            
            # Try to open the image in default viewer
            try:
                subprocess.run(['xdg-open', str(self.output_file)], check=False)
            except:
                pass
        else:
            self.status_bar.text = "No rendered image to save"
            
            # Show warning popup
            content = BoxLayout(orientation='vertical', padding=10, spacing=10)
            content.add_widget(Label(text="Render the equation first"))
            
            btn = Button(text='OK', size_hint=(1, 0.3))
            content.add_widget(btn)
            
            popup = Popup(title='Warning',
                        content=content,
                        size_hint=(0.6, 0.3))
            
            # Dismiss the popup when the button is pressed
            btn.bind(on_press=popup.dismiss)
            
            popup.open()
    
    def copy_to_clipboard(self, instance):
        """Copy the LaTeX to clipboard"""
        Clipboard.copy(self.editor.text.strip())
        self.status_bar.text = "LaTeX copied to clipboard"
    
    def reset_editor(self, instance):
        """Reset the editor to the original content"""
        # Clean the original latex for editing
        edited_text = self.latex_text
        if edited_text.startswith('$$') and edited_text.endswith('$$'):
            edited_text = edited_text[2:-2].strip()
        elif edited_text.startswith('$') and edited_text.endswith('$'):
            edited_text = edited_text[1:-1].strip()
        elif edited_text.startswith(r'\[') and edited_text.endswith(r'\]'):
            edited_text = edited_text[2:-2].strip()
        elif edited_text.startswith(r'\(') and edited_text.endswith(r'\)'):
            edited_text = edited_text[2:-2].strip()
            
        self.editor.text = edited_text
        self.status_bar.text = "Editor reset to original content"
    
    def close_app(self, instance):
        """Close the application"""
        # Call result callback if set
        if self.result_callback:
            self.result_callback(self.output_file)
        
        # Stop the app
        self.stop()
    
    def on_stop(self):
        """Called when the app is closing"""
        # Call result callback if set and not already called
        if self.result_callback:
            self.result_callback(self.output_file)

def launch_latex_editor(latex_text):
    """
    Launch the LaTeX editor as a separate process
    
    Args:
        latex_text: LaTeX text to edit
        
    Returns:
        Path: Path to the rendered image, or None if rendering failed
    """
    result_file = None
    
    def set_result(file_path):
        nonlocal result_file
        result_file = file_path
    
    # Create and run the Kivy app
    app = LatexEditorApp(latex_text=latex_text)
    app.set_callback(set_result)
    app.run()
    
    return result_file

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
            print("\nDetected LaTeX code! Opening editor...")
            
            # Copy to clipboard
            try:
                subprocess.run(['xclip', '-selection', 'clipboard'], 
                             input=text.encode(), check=True)
            except:
                pass
            
            # Launch the LaTeX editor
            output_file = launch_latex_editor(text)
            
            # Check if a file was created
            if output_file and Path(output_file).exists():
                    latex_detected = True
                    success_msg += f"\nLaTeX rendered and saved to: {Path(output_file).name}"
        else:
            # Copy to clipboard if there's text but no LaTeX
            try:
                subprocess.run(['xclip', '-selection', 'clipboard'], 
                            input=text.encode(), 
                            check=True)
                print("\nText copied to clipboard!")
            except subprocess.CalledProcessError:
                print("\nCouldn't copy to clipboard. Please install xclip:")
                print("sudo apt install xclip     # For Ubuntu/Debian")
                print("sudo pacman -S xclip       # For Arch Linux")
                send_notification(
                    "Clipboard Error",
                    "Text extracted but couldn't be copied to clipboard",
                    "critical"
                )
            
        # Send success notification
        send_notification(
            "OCR Successful",
            success_msg,
            "normal"
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
