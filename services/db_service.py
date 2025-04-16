import logging
from app import db
from models import Story

logger = logging.getLogger(__name__)

def save_story(content, image_analysis=None, image_path=None, audio_path=None, prompt=None, title=None):
    """
    Save a generated story to the database.
    
    Args:
        content: The story content
        image_analysis: Analysis of the image
        image_path: Path to the image file
        audio_path: Path to the audio narration
        prompt: Custom prompt used to generate the story
        title: Title of the story (optional)
        
    Returns:
        The saved Story object
    """
    try:
        story = Story(
            title=title,
            content=content,
            image_analysis=image_analysis,
            image_path=image_path,
            audio_path=audio_path,
            prompt=prompt
        )
        
        db.session.add(story)
        db.session.commit()
        
        logger.debug(f"Saved story with ID: {story.id}")
        return story
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error saving story to database: {str(e)}")
        raise

def get_all_stories():
    """
    Get all stories from the database.
    
    Returns:
        List of Story objects
    """
    try:
        return Story.query.order_by(Story.created_at.desc()).all()
    except Exception as e:
        logger.error(f"Error retrieving stories from database: {str(e)}")
        raise

def get_story_by_id(story_id):
    """
    Get a story by its ID.
    
    Args:
        story_id: The ID of the story
        
    Returns:
        Story object if found, None otherwise
    """
    try:
        return Story.query.get(story_id)
    except Exception as e:
        logger.error(f"Error retrieving story with ID {story_id}: {str(e)}")
        raise

def delete_story(story_id):
    """
    Delete a story from the database.
    
    Args:
        story_id: The ID of the story to delete
        
    Returns:
        True if successful, False otherwise
    """
    try:
        story = Story.query.get(story_id)
        if not story:
            return False
            
        db.session.delete(story)
        db.session.commit()
        
        logger.debug(f"Deleted story with ID: {story_id}")
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting story with ID {story_id}: {str(e)}")
        raise

def update_story_audio(story_id, audio_path):
    """
    Update the audio path for a story.
    
    Args:
        story_id: The ID of the story
        audio_path: Path to the audio file
        
    Returns:
        Updated Story object if successful, None otherwise
    """
    try:
        story = Story.query.get(story_id)
        if not story:
            return None
            
        story.audio_path = audio_path
        db.session.commit()
        
        logger.debug(f"Updated audio path for story with ID: {story_id}")
        return story
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating audio path for story with ID {story_id}: {str(e)}")
        raise