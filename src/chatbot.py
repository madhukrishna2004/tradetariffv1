import os
import openai
import pickle
import logging
import pyttsx3
import speech_recognition as sr
from flask import Blueprint, request, jsonify, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import logging
import math
import os
from concurrent.futures.thread import ThreadPoolExecutor
import re
from elasticapm.contrib.flask import ElasticAPM
import flask
from flask import request, Response, jsonify, render_template, send_from_directory
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration
from whitenoise import WhiteNoise
import openai
from dotenv import load_dotenv
from cryptography.fernet import Fernet
from src import decorators, utils
from flask import Flask, request, redirect, session, render_template, flash
import openai
import os
import pandas as pd
import requests
from datetime import datetime
from fpdf import FPDF
from io import BytesIO
from flask import Flask, request, jsonify, send_file
from datetime import timedelta
from datetime import datetime
logger = logging.getLogger(__name__)
import json
import os
import openai
import pickle
import logging
import pyttsx3
import speech_recognition as sr
from flask import Flask, render_template, request, jsonify, session
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
# Load environment variables from .env file
load_dotenv()
# Load environment variables
load_dotenv()

# Initialize Blueprint
chatbot_bp = Blueprint('chatbot', __name__)


# Generate a key for encryption (make sure to store this key securely for later decryption)
def generate_encryption_key():
    return Fernet.generate_key()

# Save the encryption key securely (You should store this somewhere safe and private)
def save_encryption_key(key):
    with open("encryption_key.key", "wb") as key_file:
        key_file.write(key)

# Load the encryption key (use this when you need to decrypt)
def load_encryption_key():
    with open("encryption_key.key", "rb") as key_file:
        return key_file.read()

# Encrypt the parts of the API key
def encrypt_api_key_parts(part1, part2, encryption_key):
    cipher = Fernet(encryption_key)
    encrypted_part1 = cipher.encrypt(part1.encode())
    encrypted_part2 = cipher.encrypt(part2.encode())
    
    # Save the encrypted parts to a file
    with open("encrypted_api_key_parts.txt", "wb") as encrypted_file:
        encrypted_file.write(encrypted_part1 + b'\n' + encrypted_part2)

# Decrypt the API key parts and combine them
def decrypt_api_key_parts(encrypted_file_path, encryption_key):
    cipher = Fernet(encryption_key)
    
    # Read the encrypted parts from the file
    with open(encrypted_file_path, "rb") as encrypted_file:
        encrypted_data = encrypted_file.read().split(b'\n')
        encrypted_part1 = encrypted_data[0]
        encrypted_part2 = encrypted_data[1]
    
    # Decrypt the parts
    decrypted_part1 = cipher.decrypt(encrypted_part1).decode()
    decrypted_part2 = cipher.decrypt(encrypted_part2).decode()
    
    # Combine the decrypted parts to form the API key
    return decrypted_part1 + decrypted_part2

#Encrypt and save API key parts if not already done (run this separately first)
#Example for encrypting and saving the API key parts:
part1 = "sk-proj-Jcgx4YzLqRFQq9F9MXwTfq2sk_q1HwfklOFIviaF45ockbK_K7HIUDUngcXZH6ka3jI0kxXYU1T3"
part2 = "BlbkFJjKGwgEWutYmHyXYAzNCozAUvZVgvDT8wzlhe2sNmugk628iD4XHcmflri96tUZbi-E4J24l14A"
encryption_key = generate_encryption_key()
save_encryption_key(encryption_key)
encrypt_api_key_parts(part1, part2, encryption_key)

# Load the encryption key
encryption_key = load_encryption_key()

# Decrypt and combine the API key parts
openai.api_key = decrypt_api_key_parts("encrypted_api_key_parts.txt", encryption_key)


# Cache Memory Setup (Pickle)
CACHE_FILE = 'cache.pkl'
cache = {}

# Logging Configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_cache():
    """Load cache from file if it exists"""
    global cache
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'rb') as f:
                cache = pickle.load(f)
            logger.info("Cache loaded successfully.")
        except (EOFError, pickle.UnpicklingError):
            cache = {}  # Reset cache if corrupted
            save_cache()
            logger.warning("Cache was corrupted. Resetting.")

def save_cache():
    """Save cache to file"""
    global cache
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(cache, f)
        f.flush()  # Ensure data is written
    logger.info("Cache saved successfully.")

@chatbot_bp.route('/ask', methods=['POST'])
def ask():
    """Handles chatbot interaction with conversation context"""
    global cache

    user_input = request.json.get('user_input')
    if not user_input:
        return jsonify({"error": "Empty input received."})

    session_id = session.get('session_id', 'default')  # Assign a session ID (default for now)

    if session_id not in cache:
        cache[session_id] = []  # Create conversation history for this session

    conversation = cache[session_id]  # Retrieve conversation history

    # Append user's input to the conversation history
    conversation.append({"role": "user", "content": user_input})

    logger.info(f"Processing conversation history for session: {session_id}")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=conversation,  # Send full conversation history
            max_tokens=150
        )

        if "choices" in response and len(response["choices"]) > 0:
            answer = response["choices"][0]["message"]["content"].strip()
        else:
            return jsonify({"error": "Unexpected OpenAI API response format."})

    except Exception as e:
        logger.error(f"Failed to get response from OpenAI: {e}")
        return jsonify({"error": "Failed to get response from OpenAI."})

    # Append AI response to conversation history
    conversation.append({"role": "assistant", "content": answer})

    # Save updated conversation in cache
    cache[session_id] = conversation
    save_cache()

    return jsonify({"response": answer})

# Load cache on startup
load_cache()
