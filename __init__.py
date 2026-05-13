from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os
from dotenv import load_dotenv

# Initialize extensions
db = SQLAlchemy()
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "dev_key")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # 1. INITIALIZE DATABASE
    db.init_app(app)

    # 2. INITIALIZE LOGIN MANAGER
    login_manager = LoginManager()
    login_manager.login_view = 'main.login' # Where to redirect if not logged in
    login_manager.init_app(app)

    # 3. USER LOADER
    from .models import User
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # 4. REGISTER BLUEPRINTS
    from .routes import main
    app.register_blueprint(main)

    # Create database tables if they don't exist
    with app.app_context():
        db.create_all()

    return app