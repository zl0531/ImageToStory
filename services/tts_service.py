import os
import uuid
import logging
from gtts import gTTS

logger = logging.getLogger(__name__)

def generate_speech(text, lang='en', output_dir='static/audio'):
    """
    Generate speech from text using Google's Text-to-Speech API.
    
    Args:
        text: The text to convert to speech
        lang: The language code (default: 'en' for English)
        output_dir: The directory to save the audio file
        
    Returns:
        The relative path to the generated audio file
    """
    try:
        # Ensure the output directory exists
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate a unique filename
        filename = f"{uuid.uuid4()}.mp3"
        filepath = os.path.join(output_dir, filename)
        
        # Generate speech
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(filepath)
        
        # Return the relative path for the web app
        return os.path.join('audio', filename)
    except Exception as e:
        logger.error(f"Error generating speech: {str(e)}")
        raise Exception(f"Failed to generate speech: {str(e)}")