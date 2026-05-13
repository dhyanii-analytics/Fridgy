from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from .models import User, ChatHistory
from . import db
from flask_login import login_user, logout_user, login_required, current_user
from datetime import datetime


main = Blueprint('main', __name__)

# --- INTERNAL HELPER TO KEEP TIMES CONSISTENT ACROSS APP ---
def get_current_meal_type():
    hour = datetime.now().hour
    #  specific time windows:
    if 4 <= hour < 7:
        return "Pre-Breakfast"
    elif 7 <= hour < 10:
        return "Breakfast"
    elif 12 <= hour < 14:
        return "Lunch"
    elif 18 <= hour < 20:
        return "Dinner"
    elif hour >= 23 or hour < 3:
        return "Midnight Snack"
    # Fallbacks for in-between times:
    elif 10 <= hour < 12:
        return "Morning Snack"
    elif 14 <= hour < 18:
        return "Evening Tea"
    elif 20 <= hour < 23:
        return "Late Night Bite"
    else:
        return "Meal"

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/how-it-works')
def how_it_works():
    return render_template('how_it_works.html')

@main.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Email already exists.', category='error')
            return redirect(url_for('main.signup'))

        new_user = User(
            name=request.form.get('name'),
            email=email,
            password=request.form.get('password'),
            age_group=request.form.get('age_group'),
            gender=request.form.get('gender'),
            profession=request.form.get('profession'),
            goal=request.form.get('goal'),
            cuisine=request.form.get('cuisine'),
            diet_type=request.form.get('diet_type'),
            diseases=request.form.get('diseases'),
            allergies=request.form.get('allergies'),
            dislikes=request.form.get('dislikes')
        )
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('main.login'))

    return render_template('signup.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.password == password:
            login_user(user, remember=True)
            
            if user.is_admin:
                return redirect(url_for('main.admin_dashboard'))
            else:
                return redirect(url_for('main.dashboard'))
        else:
            flash('Login failed. Check your details.', category='error')
            
    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@main.route('/dashboard')
@login_required
def dashboard():
    meal_type = get_current_meal_type()

    # REDIRECT ADMIN TO ADMIN HOME (3 BOTS)
    if current_user.is_admin:
        return render_template('admin_home.html', user=current_user, meal_type=meal_type)

    # REGULAR USER DASHBOARD
    return render_template('dashboard.html', user=current_user, meal_type=meal_type)

@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        current_user.name = request.form.get('name')
        current_user.profession = request.form.get('profession')
        current_user.goal = request.form.get('goal')
        current_user.cuisine = request.form.get('cuisine')
        current_user.diet_type = request.form.get('diet_type')
        current_user.allergies = request.form.get('allergies')
        current_user.dislikes = request.form.get('dislikes')
        current_user.diseases = request.form.get('diseases')

        db.session.commit()
        flash('Preferences updated! Fridgy is now adapting to your new tastes.', category='success')
        return redirect(url_for('main.profile'))

    return render_template('profile.html', user=current_user)

@main.route('/generate-recipe', methods=['POST'])
@login_required
def generate_recipe():
    from .chatbot import get_ai_response

    user_input = request.form.get('user_input', 'Surprise me')
    guest_count = request.form.get('guest_count', 1)
    photo = request.files.get('fridge_photo')
    mode = session.get('mode', 'Quick')
    
    # Sync with the new meal time logic
    meal_type = get_current_meal_type()
    
    ai_msg, yt_url = get_ai_response(current_user, user_input, guest_count, photo, mode, meal_type)

    new_chat = ChatHistory(
        user_id=current_user.id,
        message=user_input if int(guest_count) <= 1 else f"Party for {guest_count}: {user_input}",
        response=ai_msg,
        youtube_url=yt_url,
        timestamp=datetime.now()
    )
    db.session.add(new_chat)
    db.session.commit()
    
    return render_template('recipe_result.html', response=ai_msg, link=yt_url, user=current_user)

@main.route('/chat')
@login_required
def chat():
    mode = request.args.get('mode', 'Quick')
    session['mode'] = mode
    return render_template('chat.html', user=current_user, mode=mode)

@main.route('/get-chat-response', methods=['POST'])
@login_required
def get_chat_response():
    from .chatbot import get_ai_response

    user_msg = request.form.get('message', '')
    photo = request.files.get('fridge_photo')
    mode = session.get('mode', 'Quick')
    
    if not user_msg and photo:
        user_msg = "What can I cook with these ingredients?"

    # Sync with the new meal time logic
    meal_type = get_current_meal_type()
    
    ai_msg, yt_url = get_ai_response(current_user, user_msg, 1, photo, mode, meal_type)
    
    new_chat = ChatHistory(
        user_id=current_user.id, 
        message=user_msg, 
        response=ai_msg, 
        youtube_url=yt_url,
        timestamp=datetime.now()  
    )
    db.session.add(new_chat)
    db.session.commit()

    return jsonify({"response": ai_msg, "youtube_url": yt_url})
    
@main.route('/history')
@login_required
def history():
    if current_user.is_admin:
        chats = ChatHistory.query.order_by(ChatHistory.timestamp.desc()).all()
    else:
        chats = ChatHistory.query.filter_by(user_id=current_user.id).order_by(ChatHistory.timestamp.desc()).all()
    
    return render_template('history.html', chats=chats, user=current_user)

@main.route('/delete-history/<int:chat_id>')
@login_required
def delete_history(chat_id):
    chat = ChatHistory.query.get_or_404(chat_id)
    if chat.user_id == current_user.id:
        db.session.delete(chat)
        db.session.commit()
    return redirect(url_for('main.history'))

@main.route('/admin')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('main.dashboard'))

    user_count = User.query.count()
    chat_count = ChatHistory.query.count()
    all_users = User.query.order_by(User.id.desc()).all()

    # REAL DATABASE DATA FOR CHART
    # We create a list of 7 zeros (Mon-Sun)
    weekly_data = [0] * 7
    all_chats = ChatHistory.query.all()
    
    for chat in all_chats:
        # .weekday() returns 0 for Monday, 6 for Sunday
        day_index = chat.timestamp.weekday()
        weekly_data[day_index] += 1

    return render_template('admin.html', 
                           user_count=user_count, 
                           chat_count=chat_count, 
                           users=all_users,
                           weekly_data=weekly_data)


@main.route('/admin/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    if not current_user.is_admin:
        return redirect(url_for('main.dashboard'))
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully.')
    return redirect(url_for('main.admin_dashboard'))

