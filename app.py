import os
from flask import Flask, render_template, request, jsonify, session, flash
from flask_login import current_user, login_required
from .models import User, ChatHistory 
from . import db
from .chatbot import get_ai_response #  the "brain" 
from datetime import datetime


# --- VERSION 1   ---
__version__ = "1.0.0"
__author__ = "Dhyanii Patel"
__status__ = "Prototype - Initial Release"
# -----------------------------------

# Initialize the app if this is your main entry point
app = Flask(__name__) 

@app.route('/get-chat-response', methods=['POST'])
@login_required 
def get_chat_response():
    # 1. CAPTURE USER INPUT 
    user_message = request.form.get('message', '')
    photo = request.files.get('fridge_photo') 
    mode = session.get('mode', 'Quick') 
    
    # 2. DYNAMIC TIME-BASED CONTEXT 
    hour = datetime.now().hour
    meal_type = "dinner" if hour >= 18 else "lunch" if hour >= 12 else "breakfast"

    # 3. CALL THE GROQ LOGIC 
    
    ai_response, youtube_link = get_ai_response(
        current_user, 
        user_message, 
        guest_count=1, 
        photo=photo, 
        mode=mode, 
        meal_type=meal_type
    )

    # 4. SAVE TO DATABASE 
    new_chat = ChatHistory(
        user_id=current_user.id,
        message=user_message,
        response=ai_response,
        youtube_url=youtube_link
    )
    db.session.add(new_chat)
    db.session.commit()
    
    # 5. RETURN RESPONSE 
    return jsonify({
        "response": ai_response,
        "youtube_url": youtube_link
    })