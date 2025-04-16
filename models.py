from datetime import datetime
from app import db

class Story(db.Model):
    """Model for storing generated stories."""
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=True)
    content = db.Column(db.Text, nullable=False)
    image_analysis = db.Column(db.Text, nullable=True)
    image_path = db.Column(db.String(500), nullable=True)
    audio_path = db.Column(db.String(500), nullable=True)
    prompt = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Story {self.id}: {self.title or "Untitled"}>'
    
    def to_dict(self):
        """Convert story to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'image_analysis': self.image_analysis,
            'image_path': self.image_path,
            'audio_path': self.audio_path,
            'prompt': self.prompt,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }