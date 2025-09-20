import os
from datetime import datetime

class Config:
    SECRET_KEY = 'your-secret-key-here'
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{os.path.join(BASE_DIR, "instance", "database.db")}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    
    @staticmethod
    def init_app(app):
        # Create necessary directories
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER']), exist_ok=True)
        os.makedirs(os.path.join(Config.BASE_DIR, 'instance'), exist_ok=True)

