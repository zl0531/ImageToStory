import os
import logging
from flask import Flask, render_template, request, jsonify, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from services.ai_service import analyze_image_and_generate_story, regenerate_story
from services.image_service import process_image, validate_image
from services.tts_service import generate_speech
from utils.file_utils import save_temp_file, remove_temp_file
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
    return render_template('index.html')

@app.route('/stories')
def list_stories():
    """Display a list of all stored stories."""
    from services.db_service import get_all_stories
    stories = get_all_stories()
    return render_template('stories.html', stories=stories)

@app.route('/stories/<int:story_id>')
def view_story(story_id):
    """Display a single story."""
    from services.db_service import get_story_by_id
    story = get_story_by_id(story_id)
    if not story:
        return render_template('error.html', error="Story not found"), 404
    return render_template('view_story.html', story=story)

@app.route('/upload', methods=['POST'])
def upload():
    """Handle image upload and story generation."""
    try:
        # Check if an image file was sent
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': 'No image uploaded'}), 400
        
        image_file = request.files['image']
        
        # Validate the image
        if not validate_image(image_file):
            return jsonify({'success': False, 'error': 'Invalid image format. Please upload a JPEG, PNG, or GIF.'}), 400
        
        # Save file temporarily
        temp_path = save_temp_file(image_file)
        
        # Process image for Gemini
        base64_image = process_image(temp_path)
        
        # Store base64 image in session for potential regeneration
        session['base64_image'] = base64_image
        
        # Generate a story based on the image
        image_analysis, story = analyze_image_and_generate_story(base64_image)
        
        # Save the story to the database
        from services.db_service import save_story
        saved_story = save_story(content=story, image_analysis=image_analysis)
        
        # Store the story ID in the session for later use
        session['current_story_id'] = saved_story.id
        
        # Clean up the temporary file
        remove_temp_file(temp_path)
        
        return jsonify({
            'success': True, 
            'imageAnalysis': image_analysis,
            'story': story,
            'storyId': saved_story.id,
            'imageData': f"data:image/jpeg;base64,{base64_image}"
        })
    
    except Exception as e:
        logger.exception("Error processing upload")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/regenerate', methods=['POST'])
def regenerate():
    """Regenerate a story based on the previously uploaded image."""
    try:
        # Get data from request
        data = request.json
        custom_prompt = data.get('prompt', '')
        
        # Check if we have an image in the session
        if 'base64_image' not in session:
            return jsonify({'success': False, 'error': 'No image found. Please upload an image first.'}), 400
        
        base64_image = session['base64_image']
        
        # Regenerate story
        story = regenerate_story(base64_image, custom_prompt)
        
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
        
        # Generate speech
        audio_path = generate_speech(text)
        
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
