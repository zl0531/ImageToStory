from app import app, db  # noqa: F401

# Import the models to ensure they are registered with SQLAlchemy
import models  # noqa: F401

# Create all database tables
with app.app_context():
    db.create_all()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
