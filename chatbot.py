import os
import base64
from groq import Groq
from datetime import datetime

# Initialize Groq Client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


# Defaults to Llama 4 Scout 17B (Active March 2026)
VISION_MODEL = os.environ.get("VISION_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")

def encode_image(image_file):
    """Encodes the uploaded image to base64 for the Vision model."""
    return base64.b64encode(image_file.read()).decode('utf-8')

def get_ai_response(user, user_input, guest_count, photo=None, mode="Quick", meal_type="dinner"):
    """
    Generates a personalized AI response using Groq Cloud.
    Prioritizes user_input over predefined defaults.
    """
    
    # 1. DYNAMIC OVERRIDE: Prioritize User Intent 
    request_text = user_input.lower()
    
    if "breakfast" in request_text:
        meal_type = "breakfast"
    elif "lunch" in request_text:
        meal_type = "lunch"
    elif "dinner" in request_text:
        meal_type = "dinner"
    
    is_weekly = "week" in request_text or "planner" in request_text
    diet = getattr(user, 'diet_type', 'Vegetarian') 
    
    # 2. GREETING LOGIC: Determine the time of day 
    hour = datetime.now().hour
    if hour < 12:
        greeting = "Good Morning"
    elif hour < 17:
        greeting = "Good Afternoon"
    else:
        greeting = "Good Evening"
    
    # 3. BUILD SYSTEM INSTRUCTIONS 
    system_prompt = f"""
    You are Fridgy, a professional culinary AI assistant. 
    
    MANDATORY GREETING: Start your response with "{greeting}, {user.name}! ✨"
    
    User Profile: {user.name}, a {user.profession} aiming for {user.goal}.
    Dietary Preference: {diet}.
    STRICT AVOIDANCE (Allergies/Dislikes/Diseases): {user.allergies}, {user.dislikes}, and {user.diseases}.
    
    Current Context: It is {datetime.now().hour}:{datetime.now().minute}.
    """

    # 4. APPLY DYNAMIC MODE LOGIC 
    if is_weekly:
        system_prompt += "\n- MODE: WEEKLY PLANNER. Generate a 7-day meal plan (Mon-Sun)."
        system_prompt += "\n- For each day, provide Breakfast, Lunch, and Dinner."
    elif mode == "Party" or int(guest_count) > 1:
        system_prompt += f"\n- MODE: PARTY. Scale for {guest_count} people."
        system_prompt += "\n- DISABLE all fitness talk. Focus on crowd-pleasing recipes."
    else:
        system_prompt += f"\n- MODE: {mode}. Focus on providing a great {meal_type}."
        system_prompt += f"\n- Mention how this supports their {user.goal}."

    system_prompt += """
    - Use Markdown for formatting.
    - Always offer: (A) Full Recipe, (B) Step-by-Step, (C) Ingredient Check.
    - VISION INSTRUCTIONS: Identify all ingredients in the photo. 
    - PRIORITIZE the ingredients seen in the photo for the recipe.
    - MANDATORY FOOTER: End every response with: "How was your experience? (1-5 stars) ⭐"
    """

    # 5. CONSTRUCT MULTIMODAL CONTENT
    # Required format: List containing text and image_url blocks
    user_content = [{"type": "text", "text": user_input}]
    
    if photo:
        base64_image = encode_image(photo)
        user_content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
        })

    # 6. CALL GROQ CLOUD
    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content},
            ],
            model=VISION_MODEL, 
            temperature=0.6,
        )
        
        ai_response = chat_completion.choices[0].message.content
        youtube_link = "https://www.youtube.com/results?search_query=" + user_input.replace(" ", "+")
        
        return ai_response, youtube_link

    except Exception as e:
        return f"Fridgy Error: {str(e)}", None