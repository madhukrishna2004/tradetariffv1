from flask import Blueprint, render_template

chatbot_bp = Blueprint('chatbot', __name__, template_folder='templates')

@chatbot_bp.route('/')
def chatbot_ui():
    return render_template('index.html')  # Ensure chatbot.html exists
