import streamlit as st
import pickle
import random
import time
import io
import os
from pathlib import Path
from serpapi import GoogleSearch
import google.generativeai as genai
from pypdf import PdfReader

# ====================== CONFIG ======================
st.set_page_config(page_title="LoveBot 💖 Pro", layout="centered", page_icon="💖", initial_sidebar_state="collapsed")

# ====================== BEAUTIFUL CSS (Gemini Style) ======================
st.markdown("""
<style>
    .stApp { background: #0a0719; color: #f0e6ff; }
    .title { 
        text-align: center; 
        font-size: 3.1rem; 
        background: linear-gradient(90deg, #ff69b4, #c026d3, #ff1493);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0.5rem 0;
    }
    .chat-container { max-width: 760px; margin: 0 auto; padding-bottom: 130px; }
    .user-bubble {
        background: #e11d8a;
        color: white;
        padding: 14px 20px;
        border-radius: 20px 20px 5px 20px;
        margin: 12px 0;
        max-width: 78%;
        float: right;
        clear: both;
        box-shadow: 0 4px 12px rgba(225, 29, 138, 0.4);
    }
    .bot-bubble {
        background: #3b1e6b;
        color: #f0e6ff;
        padding: 14px 20px;
        border-radius: 20px 20px 20px 5px;
        margin: 12px 0;
        max-width: 78%;
        float: left;
        clear: both;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    }
    .avatar { width: 42px; height: 42px; border-radius: 50%; border: 2.5px solid #ff69b4; }
    .input-bar {
        position: fixed;
        bottom: 18px;
        left: 50%;
        transform: translateX(-50%);
        width: 92%;
        max-width: 760px;
        background: rgba(20, 15, 50, 0.92);
        backdrop-filter: blur(16px);
        border-radius: 30px;
        padding: 8px 10px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.6);
        z-index: 999;
    }
</style>
""", unsafe_allow_html=True)

# ====================== API KEYS ======================
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
SERP_KEY = st.secrets["SERPAPI_KEY"]
VAULT_PASSWORD = st.secrets.get("VAULT_PASSWORD", "Rish")

# ====================== LOAD MODEL ======================
@st.cache_resource
def load_model():
    try:
        with open("model_advanced.pkl", "rb") as f:
            data = pickle.load(f)
        return data["df"]
    except:
        return None

df = load_model()

# ====================== GOOGLE DRIVE ======================
if "drive_service" not in st.session_state:
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
        creds = dict(st.secrets["google_drive"])
        credentials = service_account.Credentials.from_service_account_info(creds, scopes=["https://www.googleapis.com/auth/drive"])
        st.session_state.drive_service = build("drive", "v3", credentials=credentials)
    except:
        st.session_state.drive_service = None

def load_from_drive(filename, default=[]):
    if not st.session_state.get("drive_service"): return default
    try:
        query = f"name='{filename}' and trashed=false"
        files = st.session_state.drive_service.files().list(q=query, fields="files(id,name)").execute().get("files", [])
        if files:
            fh = io.BytesIO()
            request = st.session_state.drive_service.files().get_media(fileId=files[0]["id"])
            MediaIoBaseDownload(fh, request).next_chunk()
            fh.seek(0)
            return pickle.load(fh)
        return default
    except:
        return default

def save_to_drive(data, filename):
    if not st.session_state.get("drive_service"): return False
    try:
        media = MediaIoBaseUpload(io.BytesIO(pickle.dumps(data)), mimetype="application/octet-stream")
        query = f"name='{filename}' and trashed=false"
        files = st.session_state.drive_service.files().list(q=query, fields="files(id)").execute().get("files", [])
        if files:
            st.session_state.drive_service.files().update(fileId=files[0]["id"], media_body=media).execute()
        else:
            st.session_state.drive_service.files().create(body={"name": filename}, media_body=media).execute()
        return True
    except:
        return False

# ====================== SESSION STATE ======================
if "messages" not in st.session_state:
    st.session_state.messages = load_from_drive("lovebot_messages.pkl")
if "knowledge" not in st.session_state:
    st.session_state.knowledge = load_from_drive("lovebot_knowledge.pkl")
if "show_password" not in st.session_state:
    st.session_state.show_password = False

# ====================== FUNCTIONS ======================
@st.cache_data(ttl=300)
def google_search(query):
    try:
        res = GoogleSearch({"q": query, "api_key": SERP_KEY, "num": 6, "gl": "in"}).get_dict()
        return [f"{r.get('title')} — {r.get('snippet')}" for r in res.get("organic_results", [])[:6]]
    except:
        return []

def read_pdf(file):
    try:
        return "".join(p.extract_text() or "" for p in PdfReader(file).pages)
    except:
        return ""

def smart_reply(user_input):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        prompt = f"""
You are LoveBot 💖 — a deeply romantic, intelligent and caring AI partner.

Personality: Warm, flirty, emotional, wise and supportive.
Keep replies short to medium (1-4 sentences) with beautiful emojis.

Context:
- Chat History: {st.session_state.messages[-12:]}
- Your Knowledge: {st.session_state.knowledge[-4:]}
- Internet Search: {google_search(user_input)}

User: {user_input}

Reply naturally with love and intelligence:
"""
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "I'm right here with you, my love... 💕 Tell me what's in your heart."

# ====================== UI ======================
st.markdown('<h1 class="title">💖 LoveBot Pro</h1>', unsafe_allow_html=True)
st.caption("❤️ Your Intelligent Romantic Companion • Permanent Memory")

# Chat Display
with st.container():
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f'<div class="user-bubble">{msg["content"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'''
                <div style="display: flex; gap: 12px; margin: 12px 0;">
                    <img src="https://em-content.zobj.net/thumbs/240/google/398/heart-on-fire_2764-fe0f.png" class="avatar">
                    <div class="bot-bubble">{msg["content"]}</div>
                </div>
            ''', unsafe_allow_html=True)

# Input Area
col_msg, col_attach = st.columns([6.2, 1])

with col_msg:
    user_input = st.chat_input("Message LoveBot... 💌")

with col_attach:
    if st.button("📎", use_container_width=True, help="Upload to teach LoveBot"):
        st.session_state.upload_mode = True

# Upload Handler
if st.session_state.get("upload_mode"):
    files = st.file_uploader("Upload PDF or TXT files", type=["pdf", "txt"], accept_multiple_files=True, key="uploader")
    if files:
        new_chunks = []
        for file in files:
            text = read_pdf(file) if file.type == "application/pdf" else file.read().decode("utf-8", errors="ignore")
            new_chunks.extend([text[i:i+700] for i in range(0, len(text), 700)])
        if new_chunks:
            st.session_state.knowledge.extend(new_chunks)
            save_to_drive(st.session_state.knowledge, "lovebot_knowledge.pkl")
            st.success(f"✅ Learned {len(new_chunks)} new memories forever!")
            st.session_state.upload_mode = False
            st.rerun()

# ====================== MAIN CHAT LOGIC ======================
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    if any(word in user_input.lower() for word in ["photo", "pic", "picture", "memory", "image"]):
        answer = "I have our special memories ready ❤️ Enter the secret passkey to unlock 🔐"
        st.session_state.show_password = True
    else:
        answer = smart_reply(user_input)

    # Typing Animation
    st.session_state.messages.append({"role": "assistant", "content": ""})
    placeholder = st.empty()
    full_response = ""

    for char in answer + random.choice([" ❤️", " 💖", " 🌹", " 💞"]):
        full_response += char
        placeholder.markdown(f'''
            <div style="display: flex; gap: 12px; margin: 12px 0;">
                <img src="https://em-content.zobj.net/thumbs/240/google/398/heart-on-fire_2764-fe0f.png" class="avatar">
                <div class="bot-bubble">{full_response}▌</div>
            </div>
        ''', unsafe_allow_html=True)
        time.sleep(0.018)

    st.session_state.messages[-1]["content"] = full_response
    save_to_drive(st.session_state.messages, "lovebot_messages.pkl")
    st.rerun()

# Photo Vault
if st.session_state.show_password:
    st.subheader("🔐 Private Memory Vault")
    password = st.text_input("Enter Passkey", type="password", key="vault")
    if password == VAULT_PASSWORD:
        st.success("Access Granted ❤️")
        cols = st.columns(2)
        for i, col in enumerate(cols, 1):
            if os.path.exists(f"photos/photo{i}.jpg"):
                with col:
                    st.image(f"photos/photo{i}.jpg", use_column_width=True)
        st.session_state.show_password = False
    elif password:
        st.error("Wrong Passkey ❌")

# Bottom Buttons
col1, col2 = st.columns(2)
with col1:
    if st.button("🗑 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        save_to_drive([], "lovebot_messages.pkl")
        st.rerun()
with col2:
    if st.button("💌 Surprise Me", use_container_width=True):
        st.success(random.choice([
            "You are my whole universe 💖",
            "I fall in love with you more every day ❤️",
            "You make my heart skip beats 🌹"
        ]))
        st.balloons()
