import os
from datetime import timedelta

class Config(object):
    # Fallback to a hardcoded key for development if not set in environment
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'a-very-secret-key-for-dev' 
    
    # Database configuration
    # Use instance folder for the database file
    basedir = os.path.abspath(os.path.dirname(__file__))
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Flask-Login configuration
    REMEMBER_COOKIE_DURATION = timedelta(days=7)
    
    # GenAI Configuration
    # The actual API key is in the environment variable. We will use the model slug.
    GENAI_MODEL = 'gpt-4.1-mini'
    
    # CORS Configuration
    CORS_HEADERS = 'Content-Type' 

