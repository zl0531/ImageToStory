import os
import logging
import json
from flask import Flask, render_template, request, jsonify, session, send_from_directory, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from services.ai_service import analyze_image_and_generate_story, regenerate_story
from services.image_service import process_image, validate_image
from services.tts_service import generate_speech
from utils.file_utils import save_temp_file, remove_temp_file, save_base64_image, get_base64_image
import base64

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Check if Google API Key is set
if not os.environ.get("GOOGLE_API_KEY"):
    logger.warning("GOOGLE_API_KEY environment variable is not set. The application may not function correctly.")

# Create the database base class
class Base(DeclarativeBase):
    pass

# Initialize the database
db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# Initialize the app with the database extension
db.init_app(app)

@app.route('/')
def index():
    """Render the main page of the application."""
    # Get the preferred language from the session or default to English
    language = session.get('language', 'en')
    return render_template('index.html', language=language)

@app.route('/set-language/<lang>')
def set_language(lang):
    """Set the user's preferred language."""
    # Only accept valid language codes
    if lang in ['en', 'zh']:
        session['language'] = lang
    return redirect(request.referrer or url_for('index'))

@app.route('/stories')
def list_stories():
    """Display a list of all stored stories."""
    from services.db_service import get_all_stories
    stories = get_all_stories()
    # Get the preferred language from the session or default to English
    language = session.get('language', 'en')
    return render_template('stories.html', stories=stories, language=language)

@app.route('/stories/<int:story_id>')
def view_story(story_id):
    """Display a single story."""
    from services.db_service import get_story_by_id
    story = get_story_by_id(story_id)
    if not story:
        return render_template('error.html', error="Story not found"), 404
    # Get the preferred language from the session or default to English
    language = session.get('language', 'en')
    return render_template('view_story.html', story=story, language=language)

@app.route('/upload', methods=['POST'])
def upload():
    """Handle image upload and story generation."""
    try:
        logger.info("Received upload request")

        # Check if an image file was sent
        if 'image' not in request.files:
            logger.warning("No image file in request")
            return jsonify({'success': False, 'error': 'No image uploaded'}), 400

        image_file = request.files['image']
        logger.info(f"Received image: {image_file.filename}, Content type: {image_file.content_type}")

        # Validate the image
        if not validate_image(image_file):
            logger.warning(f"Invalid image format: {image_file.filename}")
            return jsonify({'success': False, 'error': 'Invalid image format. Please upload a JPEG, PNG, or GIF.'}), 400

        # Save file temporarily
        logger.info("Saving image to temporary file")
        temp_path = save_temp_file(image_file)
        logger.info(f"Image saved to: {temp_path}")

        # Process image for Gemini
        logger.info("Processing image for Gemini API")
        try:
            base64_image = process_image(temp_path)
            logger.info("Image successfully processed and converted to base64")

            # Save the base64 image to a file instead of session
            logger.info("Saving base64 image to file")
            image_id, image_path = save_base64_image(base64_image)
            logger.info(f"Image saved with ID: {image_id}")

            # Store only the image ID in session
            session['image_id'] = image_id
            logger.info("Image ID stored in session")
        except Exception as img_error:
            logger.error(f"Error processing image: {str(img_error)}", exc_info=True)
            return jsonify({'success': False, 'error': f"Error processing image: {str(img_error)}"}), 500

        # Get the preferred language from the session
        language = session.get('language', 'en')
        logger.info(f"Using language: {language}")

        # Generate a story based on the image and language
        logger.info("Generating story from image")
        try:
            image_analysis, story = analyze_image_and_generate_story(base64_image, language=language)
            logger.info("Successfully generated story and image analysis")
        except Exception as ai_error:
            logger.error(f"Error in AI processing: {str(ai_error)}", exc_info=True)
            return jsonify({'success': False, 'error': f"Error generating story: {str(ai_error)}"}), 500

        # Save the story to the database
        logger.info("Saving story to database")
        try:
            from services.db_service import save_story
            saved_story = save_story(content=story, image_analysis=image_analysis)
            logger.info(f"Story saved with ID: {saved_story.id}")
        except Exception as db_error:
            logger.error(f"Database error: {str(db_error)}", exc_info=True)
            return jsonify({'success': False, 'error': f"Error saving to database: {str(db_error)}"}), 500

        # Store the story ID in the session for later use
        session['current_story_id'] = saved_story.id

        # Clean up the temporary file
        logger.info(f"Cleaning up temporary file: {temp_path}")
        remove_temp_file(temp_path)

        # Prepare response
        logger.info("Preparing successful response")
        response_data = {
            'success': True,
            'imageAnalysis': image_analysis,
            'story': story,
            'storyId': saved_story.id,
            'imageData': f"data:image/jpeg;base64,{base64_image}"
        }

        # Log response size
        response_size_kb = (len(json.dumps(response_data)) - len(base64_image)) / 1024
        logger.info(f"Response size (excluding base64 image): {response_size_kb:.2f} KB")

        return jsonify(response_data)

    except Exception as e:
        logger.exception(f"Unhandled error in upload: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/regenerate', methods=['POST'])
def regenerate():
    """Regenerate a story based on the previously uploaded image."""
    try:
        # Get data from request
        data = request.json
        custom_prompt = data.get('prompt', '')

        # Check if we have an image ID in the session
        if 'image_id' not in session:
            logger.warning("No image ID found in session")
            return jsonify({'success': False, 'error': 'No image found. Please upload an image first.'}), 400

        # Get the image ID from session
        image_id = session['image_id']
        logger.info(f"Retrieved image ID from session: {image_id}")

        # Get the base64 image from file
        try:
            logger.info(f"Loading image with ID: {image_id}")
            base64_image = get_base64_image(image_id)
            logger.info("Successfully loaded image from file")
        except Exception as img_error:
            logger.error(f"Error loading image: {str(img_error)}", exc_info=True)
            return jsonify({'success': False, 'error': f"Error loading image: {str(img_error)}"}), 500

        # Get the preferred language from the session
        language = session.get('language', 'en')

        # Regenerate story with language preference
        story = regenerate_story(base64_image, custom_prompt, language=language)

        # Save the regenerated story to the database
        from services.db_service import save_story
        saved_story = save_story(content=story, prompt=custom_prompt)

        # Update the story ID in the session
        session['current_story_id'] = saved_story.id

        return jsonify({
            'success': True,
            'story': story,
            'storyId': saved_story.id
        })

    except Exception as e:
        logger.exception("Error regenerating story")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/generate-speech', methods=['POST'])
def text_to_speech():
    """Generate speech from text."""
    try:
        # Get data from request
        data = request.json
        text = data.get('text', '')
        story_id = data.get('storyId') or session.get('current_story_id')

        if not text:
            return jsonify({'success': False, 'error': 'No text provided'}), 400

        # Get the preferred language from the session
        language = session.get('language', 'en')

        # Map our language codes to gTTS language codes
        tts_lang = 'zh-CN' if language == 'zh' else 'en'

        # Generate speech with proper language
        audio_path = generate_speech(text, lang=tts_lang)

        # If we have a story ID, update the story with the audio path
        if story_id:
            from services.db_service import update_story_audio
            update_story_audio(story_id, audio_path)

        return jsonify({
            'success': True,
            'audioPath': audio_path,
            'storyId': story_id
        })

    except Exception as e:
        logger.exception("Error generating speech")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/static/audio/<filename>')
def serve_audio(filename):
    """Serve audio files."""
    return send_from_directory('static/audio', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
