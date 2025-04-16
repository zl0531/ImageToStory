import os
import base64
from PIL import Image
import io
import logging

logger = logging.getLogger(__name__)

# List of allowed image extensions
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def validate_image(file):
    """
    Validate if the uploaded file is an allowed image type.
    
    Args:
        file: The file object from the request
        
    Returns:
        Boolean indicating if the file is a valid image
    """
    if file.filename == '':
        return False
        
    # Check if the extension is allowed
    return '.' in file.filename and \
           file.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def process_image(image_path, max_size=1024):
    """
    Process an image file:
    - Resize if necessary while preserving aspect ratio
    - Convert to base64 for API use
    
    Args:
        image_path: Path to the image file
        max_size: Maximum dimension (width or height) in pixels
        
    Returns:
        Base64 encoded image string
    """
    try:
        # Open image
        with Image.open(image_path) as img:
            # Convert to RGB if it's not (e.g., PNG with transparency)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Get dimensions
            width, height = img.size
            
            # Resize if the image is larger than max_size
            if width > max_size or height > max_size:
                # Calculate new dimensions
                if width > height:
                    new_width = max_size
                    new_height = int(height * (max_size / width))
                else:
                    new_height = max_size
                    new_width = int(width * (max_size / height))
                
                # Resize image
                img = img.resize((new_width, new_height), Image.LANCZOS)
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            return base64.b64encode(buffer.getvalue()).decode('utf-8')
            
    except Exception as e:
        logger.error(f"Error processing image: {str(e)}")
        raise Exception(f"Failed to process the image: {str(e)}")
