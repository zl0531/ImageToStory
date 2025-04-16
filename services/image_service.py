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
        # Log the start of image processing
        logger.info(f"Processing image: {image_path}")
        logger.info(f"Maximum dimension set to: {max_size} pixels")

        # Check if file exists
        if not os.path.exists(image_path):
            logger.error(f"Image file not found: {image_path}")
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # Get file size
        file_size_kb = os.path.getsize(image_path) / 1024
        logger.info(f"Original file size: {file_size_kb:.2f} KB")

        # Open image
        logger.info("Opening image file")
        with Image.open(image_path) as img:
            # Log original image details
            width, height = img.size
            logger.info(f"Original dimensions: {width}x{height} pixels, Mode: {img.mode}")

            # Convert to RGB if it's not (e.g., PNG with transparency)
            if img.mode != 'RGB':
                logger.info(f"Converting image from {img.mode} to RGB")
                img = img.convert('RGB')

            # Resize if the image is larger than max_size
            if width > max_size or height > max_size:
                # Calculate new dimensions
                if width > height:
                    new_width = max_size
                    new_height = int(height * (max_size / width))
                else:
                    new_height = max_size
                    new_width = int(width * (max_size / height))

                logger.info(f"Resizing image from {width}x{height} to {new_width}x{new_height}")
                # Resize image
                img = img.resize((new_width, new_height), Image.LANCZOS)
            else:
                logger.info("Image is within size limits, no resizing needed")

            # Convert to base64
            logger.info("Converting image to base64")
            buffer = io.BytesIO()
            img.save(buffer, format="JPEG", quality=85)
            base64_data = base64.b64encode(buffer.getvalue()).decode('utf-8')

            # Log the size of the base64 data
            base64_size_kb = len(base64_data) / 1024
            logger.info(f"Base64 data size: {base64_size_kb:.2f} KB")

            if base64_size_kb > 1000:
                logger.warning(f"Large base64 data ({base64_size_kb:.2f} KB). This may cause memory issues.")

            return base64_data

    except Exception as e:
        logger.error(f"Error processing image: {str(e)}", exc_info=True)
        raise Exception(f"Failed to process the image: {str(e)}")
