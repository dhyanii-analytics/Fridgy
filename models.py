from . import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Credentials
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    name = db.Column(db.String(150))
    
    # Demographics captured in your Signup UI
    age_group = db.Column(db.String(20))
    gender = db.Column(db.String(20))
    profession = db.Column(db.String(100))
    
    # Tastes & Health captured in your Signup UI
    goal = db.Column(db.String(100))
    cuisine = db.Column(db.String(200))
    diseases = db.Column(db.String(500))
    allergies = db.Column(db.String(500))
    dislikes = db.Column(db.String(500))
    
    # Dietary Preference (Vegetarian, Non-Vegetarian, Vegan)
    diet_type = db.Column(db.String(50)) 

    #admin 
    is_admin = db.Column(db.Boolean, default=False)

class ChatHistory(db.Model):
    # Primary Key
    id = db.Column(db.Integer, primary_key=True)
    
    # Foreign Key linking to the User
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Chat Details
    message = db.Column(db.Text, nullable=False) # User's query or photo description
    response = db.Column(db.Text, nullable=False) # AI's recipe or advice
    youtube_url = db.Column(db.String(500)) # Saved YouTube link
    
    # Time of conversation
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

    # for admin to see user name 
    user = db.relationship('User', backref=db.backref('chat_history', lazy=True))