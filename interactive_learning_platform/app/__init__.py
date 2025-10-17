from flask import Flask
from config import Config
from flask_login import LoginManager
from flask_migrate import Migrate
from flask_cors import CORS
from app.models import db as models_db # Import the SQLAlchemy instance from models.py

# Initialize extensions outside of create_app
db = models_db # Use the imported db instance
migrate = Migrate()
login = LoginManager()
login.login_view = 'main.login' # 'main' is the blueprint name

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    CORS(app) # Enable CORS for all routes

    # Import and register blueprints
    from app.routes import main as main_bp
    app.register_blueprint(main_bp)

    # User loader for Flask-Login
    from app.models import User
    @login.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app

