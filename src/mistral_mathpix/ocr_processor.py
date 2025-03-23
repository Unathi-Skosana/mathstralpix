import os
import base64
from pathlib import Path
from mistralai import Mistral
from PIL import Image

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