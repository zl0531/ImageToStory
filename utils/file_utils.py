import os
import uuid
import logging
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
