import os
import uuid
import logging
import base64
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

def save_temp_file(file_obj):
    """
    Save an uploaded file to a temporary location.

    Args:
        file_obj: The file object from the request

    Returns:
        Path to the saved temporary file
    """
    try:
        # Create a unique filename
        original_filename = secure_filename(file_obj.filename)
        # Get the file extension
        ext = original_filename.rsplit('.', 1)[1].lower() if '.' in original_filename else ''
        # Create a unique filename with the original extension
        unique_filename = f"{uuid.uuid4().hex}.{ext}"

        # Ensure the temporary directory exists
        os.makedirs('tmp', exist_ok=True)

        # Create the full path
        temp_path = os.path.join('tmp', unique_filename)

        # Save the file
        file_obj.save(temp_path)

        return temp_path

    except Exception as e:
        logger.error(f"Error saving temporary file: {str(e)}")
        raise Exception(f"Failed to save the uploaded file: {str(e)}")

def remove_temp_file(file_path):
    """
    Remove a temporary file.

    Args:
        file_path: Path to the file to be removed
    """
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        logger.error(f"Error removing temporary file {file_path}: {str(e)}")
        # We don't raise an exception here as this is a cleanup operation
        # and shouldn't prevent the rest of the application from working

def save_base64_image(base64_data, prefix="img_"):
    """
    Save a base64 encoded image to a file.

    Args:
        base64_data: Base64 encoded image data
        prefix: Prefix for the filename

    Returns:
        Tuple of (file_id, file_path)
    """
    try:
        # Create a unique ID and filename
        file_id = uuid.uuid4().hex
        filename = f"{prefix}{file_id}.jpg"

        # Ensure the temporary directory exists
        os.makedirs('tmp', exist_ok=True)

        # Create the full path
        file_path = os.path.join('tmp', filename)

        # Decode and save the image
        with open(file_path, 'wb') as f:
            f.write(base64.b64decode(base64_data))

        logger.info(f"Saved base64 image to {file_path}")
        return file_id, file_path

    except Exception as e:
        logger.error(f"Error saving base64 image: {str(e)}")
        raise Exception(f"Failed to save the base64 image: {str(e)}")

def get_base64_image(file_id, prefix="img_"):
    """
    Read a file and return its contents as base64.

    Args:
        file_id: The ID of the file to read
        prefix: Prefix used when saving the file

    Returns:
        Base64 encoded image data
    """
    try:
        # Construct the filename
        filename = f"{prefix}{file_id}.jpg"
        file_path = os.path.join('tmp', filename)

        # Check if the file exists
        if not os.path.exists(file_path):
            logger.error(f"Image file not found: {file_path}")
            raise FileNotFoundError(f"Image file not found: {file_path}")

        # Read and encode the file
        with open(file_path, 'rb') as f:
            image_data = f.read()

        # Convert to base64
        base64_data = base64.b64encode(image_data).decode('utf-8')
        logger.info(f"Read image from {file_path}")
        return base64_data

    except Exception as e:
        logger.error(f"Error reading image file: {str(e)}")
        raise Exception(f"Failed to read the image file: {str(e)}")
