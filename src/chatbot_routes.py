import os
import re
import faiss
import json
import openai
import pickle
import logging
import numpy as np
import pandas as pd
from flask import Blueprint, request, jsonify, session, render_template
from cryptography.fernet import Fernet
from dotenv import load_dotenv

# === Blueprint ===
chatbot_bp = Blueprint("chatbot", __name__)
logger = logging.getLogger(__name__)

# === Config Paths ===
CSV_PATH = "global-uk-tariff - Copy (2).xlsx"
FAISS_INDEX_PATH = "hs_code_index.faiss"
DF_PICKLE_PATH = "hs_code_data.pkl"
CACHE_FILE = "cache.pkl"
OPENAI_EMBEDDING_MODEL = "text-embedding-3-small"
ENCRYPTED_KEY_FILE = "encrypted_api_key_parts.txt"
KEY_FILE = "encryption_key.key"

# === Load Environment ===
load_dotenv()

# === OpenAI Key Decryption ===
def load_encryption_key():
    with open(KEY_FILE, "rb") as key_file:
        return key_file.read()

def decrypt_api_key_parts(encrypted_file_path, encryption_key):
    cipher = Fernet(encryption_key)
    with open(encrypted_file_path, "rb") as encrypted_file:
        encrypted_data = encrypted_file.read().split(b'\n')
        return cipher.decrypt(encrypted_data[0]).decode() + cipher.decrypt(encrypted_data[1]).decode()

encryption_key = load_encryption_key()
openai.api_key = decrypt_api_key_parts(ENCRYPTED_KEY_FILE, encryption_key)

# === Load Data & Index ===
df = pd.read_pickle(DF_PICKLE_PATH)
index = faiss.read_index(FAISS_INDEX_PATH)

# === In-Memory Cache ===
cache = {}

def load_cache():
    global cache
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'rb') as f:
                cache = pickle.load(f)
        except Exception:
            cache = {}
            save_cache()

def save_cache():
    global cache
    with open(CACHE_FILE, 'wb') as f:
        pickle.dump(cache, f)

# === HS CODE LOGIC ===
def get_embedding(text: str) -> list:
    response = openai.Embedding.create(input=text, model=OPENAI_EMBEDDING_MODEL)
    return response['data'][0]['embedding']

def extract_product(text: str) -> str:
    pattern = r"\b(importing|exporting|shipping|buying|sending|dealing with|looking for|sourcing|trading)\b\s+(.*)"
    match = re.search(pattern, text.lower())
    return match.group(2).strip() if match else text.strip().lower()

def extract_keywords_from_descriptions(descriptions):
    materials = set()
    usages = set()
    material_keywords = ['steel', 'iron', 'plastic', 'rubber', 'aluminum', 'copper', 'glass', 'wood', 'textile', 'cotton', 'leather', 'ceramic', 'brass', 'metal']
    usage_keywords = ['machinery', 'vehicle', 'construction', 'furniture', 'electrical', 'medical', 'food', 'chemical', 'packaging', 'agriculture', 'tools', 'automobile', 'electronics']

    for desc in descriptions:
        lower = desc.lower()
        for mat in material_keywords:
            if mat in lower: materials.add(mat)
        for use in usage_keywords:
            if use in lower: usages.add(use)

    return list(materials), list(usages)

def format_hscode_results(matches_df):
    if matches_df.empty:
        return " Sorry, no results found for that product."

    result = "** Top HS Code Matches:**\n"
    top = matches_df.head(3)
    for _, row in top.iterrows():
        result += f"\n HS Code: `{row['commodity']}`\n"
        result += f"• Description: {row['description']}\n"
        result += f"• UK Duty: {row.get('ukgt_duty_rate', 'N/A')}\n"
        result += f"• VAT: {row.get('VAT Rate', 'N/A')}\n"
        result += f"• Rule of Origin EU-UK: {row.get('Product-specific rule of origin', 'N/A')}\n"
        result += f"• Rule of Origin Japan: {row.get('Product-specific rule of origin japan', 'N/A')}\n"
        
    return result

def interactive_hscode_handler(session_id, user_input, cache):
    session_data = cache.get(session_id, {})
    step = session_data.get("step")

    if not step:
        product = extract_product(user_input)
        matches = df[df['description'].str.contains(product, case=False, na=False)]

        if matches.empty:
            try:
                embed = np.array([get_embedding(product)], dtype='float32')
                _, I = index.search(embed, 5)
                matches = df.iloc[I[0]]
            except Exception as e:
                return f" Search error: {e}"

        if isinstance(matches, pd.Series):
            matches = pd.DataFrame([matches])

        if len(matches) <= 3:
            return format_hscode_results(matches)

        materials, usages = extract_keywords_from_descriptions(matches['description'])

        session_data.update({
            "step": "awaiting_material",
            "product": product,
            "matches": matches.to_dict(orient="records"),
            "materials": materials,
            "usages": usages
        })
        cache[session_id] = session_data
        save_cache()

        opts = ', '.join(materials) if materials else "steel, plastic, rubber"
        return f" I found different types of {product}.\nWhat material is it made of? (e.g., {opts})"

    if step == "awaiting_material":
        material = user_input.strip().lower()
        matches_df = pd.DataFrame(session_data["matches"])
        filtered_matches = matches_df[matches_df['description'].str.contains(material, case=False, na=False)]

        if filtered_matches.empty:
            filtered_matches = matches_df

        if len(filtered_matches) <= 3:
            session_data.clear()
            session_data["conversation"] = cache.get(session_id, {}).get("conversation", [])
            cache[session_id] = session_data
            save_cache()
            return format_hscode_results(filtered_matches)

        usages, _ = extract_keywords_from_descriptions(filtered_matches['description'])

        session_data.update({
            "step": "awaiting_usage",
            "material": material,
            "matches": filtered_matches.to_dict(orient="records"),
            "usages": usages,
        })
        cache[session_id] = session_data
        save_cache()

        usage_opts = ', '.join(usages) if usages else "construction, packaging, electronics"
        return f" Thanks! What is it used for? (e.g., {usage_opts})"

    if step == "awaiting_usage":
        usage = user_input.strip().lower()
        matches_df = pd.DataFrame(session_data["matches"])
        filtered_matches = matches_df[matches_df['description'].str.contains(usage, case=False, na=False)]

        if filtered_matches.empty:
            filtered_matches = matches_df

        conversation = session_data.get("conversation", [])
        session_data.clear()
        session_data["conversation"] = conversation
        cache[session_id] = session_data
        save_cache()

        return format_hscode_results(filtered_matches)

#=== /ask ROUTE ===
@chatbot_bp.route('/ask', methods=['POST'])
def ask():
    global cache

    user_input = request.json.get('user_input')
    if not user_input:
        return jsonify({"error": "Empty input received."})

    session_id = session.get('session_id', 'default')
    if not isinstance(cache.get(session_id), dict):
        cache[session_id] = {"conversation": []}

    session_data = cache[session_id]
    conversation = session_data.get("conversation", [])
    session_data["conversation"] = conversation  # Ensure it's saved

    trigger_keywords = [
        'import', 'importing', 'export', 'exporting', 'buying', 'selling', 'trading', 'shipping', 'sending',
        'dealing with', 'looking for', 'sourcing', 'purchasing',
        'hs code', 'commodity', 'tariff', 'classification', 'chapter', 'heading', 'schedule b',
        'duty', 'vat', 'excise', 'origin', 'rule of origin', 'product origin', 'non-originating', 'originating',
        'preferential', 'zero duty', 'third country', 'trade agreement', 'fta', 'customs code', 'cn code',
        'steel', 'plastic', 'aluminum', 'rubber', 'glass', 'wood', 'textile', 'leather', 'machinery',
        'electrical', 'construction', 'parts', 'equipment', 'raw material', 'components', 'bolts', 'screws', 'nuts', 'fasteners'
    ]

    user_lower = user_input.lower()
    ongoing_wizard = session_data.get("step") is not None
    trigger_match = any(keyword in user_lower for keyword in trigger_keywords)

    if ongoing_wizard and any(k in user_lower for k in ['import', 'export', 'buying', 'selling', 'trading', 'sourcing', 'dealing with']):
        logger.info(f"🧹 Detected new product intent. Resetting session for: {session_id}")
        cache[session_id] = {"conversation": []}
        session_data = cache[session_id]
        conversation = session_data["conversation"]
        ongoing_wizard = False

    if trigger_match or ongoing_wizard:
        response = interactive_hscode_handler(session_id, user_input, cache)
        session_data["conversation"].append({"role": "assistant", "content": response})
        save_cache()
        return jsonify({"response": response})

    conversation.append({"role": "user", "content": user_input})
    logger.info(f"🔄 Fallback GPT conversation for session: {session_id}")

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o",
            messages=conversation,
            max_tokens=300
        )
        answer = response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        logger.error(f" AI API error: {e}")
        answer = " AI is currently unavailable. Please try again shortly."

    conversation.append({"role": "assistant", "content": answer})
    session_data["conversation"] = conversation
    cache[session_id] = session_data
    save_cache()

    return jsonify({"response": answer})

# === Load Cache at Startup ===
load_cache()

@chatbot_bp.route('/', methods=['GET'])
def chatbot_ui():
    return render_template('index.html')
