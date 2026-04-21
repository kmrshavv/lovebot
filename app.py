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

# ==============================
# CONFIG & BEAUTIFUL CSS
# ==============================
st.set_page_config(page_title="LoveBot 💖 Pro", layout="centered", page_icon="💖", initial_sidebar_state="collapsed")

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f001a, #2a0033);
        color: #ffe6f0;
    }
    .title {
        text-align: center;
        font-size: 3.2rem;
        background: linear-gradient(90deg, #ff69b4, #ff1493, #ff69b4);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
        text-shadow: 0 0 30px rgba(255, 105, 180, 0.5);
    }
    .chat-container {
        max-width: 780px;
        margin: 0 auto;
        padding-bottom: 100px;
    }
    .user-bubble {
        background: linear-gradient(135deg, #ff4da6, #ff1493);
        color: white;
        padding: 14px 20px;
        border-radius: 20px 20px 5px 20px;
        margin: 12px 0;
        max-width: 80%;
        float: right;
        clear: both;
        box-shadow: 0 4px 15px rgba(255, 20, 147, 0.3);
    }
    .bot-bubble {
        background: #3a1f4d;
        color: #ffe6f0;
        padding: 14px 20px;
        border-radius: 20px 20px 20px 5px;
        margin: 12px 0;
        max-width: 80%;
        float: left;
        clear: both;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.4);
    }
    .avatar {
        width: 42px;
        height: 42px;
        border-radius: 50%;
        border: 3px solid #ff69b4;
        box-shadow: 0 0 15px rgba(255, 105, 180, 0.6);
    }
    .input-bar {
        position: fixed;
        bottom: 15px;
        left: 50%;
        transform: translateX(-50%);
        width: 90%;
        max-width: 780px;
        background: rgba(255,255,255,0.08);
        backdrop-filter: blur(12px);
        border-radius: 30px;
        padding: 8px 12px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.4);
        z-index: 100;
    }
    .caption {
        text-align: center;
        color: #ff99cc;
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)

# ==============================
# API KEYS
# ==============================
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
SERP_KEY = st.secrets["SERPAPI_KEY"]
VAULT_PASSWORD = st.secrets.get("VAULT_PASSWORD", "Rish")

# ==============================
# LOAD MODEL
# ==============================
@st.cache_resource
def load_advanced_model():
    try:
        with open("model_advanced.pkl", "rb") as f:
            data = pickle.load(f)
        return data["df"], data.get("embedder"), data["embeddings"]
    except:
        return None, None, None

df, embedder, embeddings = load_advanced_model()

# ==============================
# GOOGLE DRIVE SETUP
# ==============================
if "drive_service" not in st.session_state:
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload
        creds_info = dict(st.secrets["google_drive"])
        credentials = service_account.Credentials.from_service_account_info(
            creds_info, scopes=["https://www.googleapis.com/auth/drive"]
        )
        st.session_state.drive_service = build("drive", "v3", credentials=credentials)
    except:
        st.session_state.drive_service = None

# ==============================
# PERSISTENT STORAGE
# ==============================
def load_from_drive(filename, default=None):
    if default is None:
        default = [] if "messages" in filename else []
    if not st.session_state.get("drive_service"):
        return default
    try:
        query = f"name='{filename}' and trashed=false"
        results = st.session_state.drive_service.files().list(q=query, fields="files(id,name)").execute()
        files = results.get("files", [])
        if files:
            file_id = files[0]["id"]
            request = st.session_state.drive_service.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            fh.seek(0)
            return pickle.load(fh)
        return default
    except:
        return default

def save_to_drive(data, filename):
    if not st.session_state.get("drive_service"):
        return False
    try:
        serialized = pickle.dumps(data)
        media = MediaIoBaseUpload(io.BytesIO(serialized), mimetype="application/octet-stream", resumable=True)
        query = f"name='{filename}' and trashed=false"
        results = st.session_state.drive_service.files().list(q=query, fields="files(id,name)").execute()
        files = results.get("files", [])
        if files:
            st.session_state.drive_service.files().update(fileId=files[0]["id"], media_body=media).execute()
        else:
            file_metadata = {"name": filename}
            st.session_state.drive_service.files().create(body=file_metadata, media_body=media).execute()
        return True
    except:
        return False

# ==============================
# SESSION STATE
# ==============================
if "messages" not in st.session_state:
    st.session_state.messages = load_from_drive("lovebot_messages.pkl")
if "knowledge" not in st.session_state:
    st.session_state.knowledge = load_from_drive("lovebot_knowledge.pkl")
if "show_password" not in st.session_state:
    st.session_state.show_password = False
if "uploaded_files" not in st.session_state:
    st.session_state.uploaded_files = []

# ==============================
# HELPER FUNCTIONS
# ==============================
@st.cache_data(ttl=300)
def google_search(query):
    try:
        res = GoogleSearch({"q": query, "api_key": SERP_KEY, "num": 8, "gl": "in", "hl": "en"}).get_dict()
        results = [f"📌 {r.get('title','')}\n{r.get('snippet','')}" for r in res.get("organic_results", [])[:8]]
        return results
    except:
        return []

def read_pdf(file):
    try:
        text = ""
        pdf = PdfReader(file)
        for page in pdf.pages:
            text += page.extract_text() or ""
        return text
    except:
        return ""

def semantic_search(query):
    if df is None:
        return None, 0.0
    try:
        query_lower = query.lower()
        best_score = 0.0
        best_answer = None
        for _, row in df.iterrows():
            q = str(row['question']).lower()
            if any(word in q for word in query_lower.split() if len(word) > 2):
                score = 0.88
                if score > best_score:
                    best_score = score
                    best_answer = row['answer']
        return best_answer, best_score
    except:
        return None, 0.0

def retrieve_knowledge(query):
    if not st.session_state.knowledge:
        return []
    query_words = set(word.lower() for word in query.split() if len(word) > 3)
    scored = [(sum(1 for w in query_words if w in chunk.lower()), len(chunk), chunk) 
              for chunk in st.session_state.knowledge if any(w in chunk.lower() for w in query_words)]
    scored.sort(key=lambda x: (x[0], -x[1]), reverse=True)
    return [c[2] for c in scored[:5]]

def smart_reply(user_input):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        history = st.session_state.messages[-15:]
        search = google_search(user_input)
        local_know = retrieve_knowledge(user_input)
        local_ans, conf = semantic_search(user_input)

        prompt = f"""
You are LoveBot 💖 — a deeply romantic, highly intelligent, and emotionally aware AI companion.

Rules:
- Be warm, flirty, supportive and intelligent
- Think step-by-step. Verify facts using provided context.
- Handle any topic: love, life, philosophy, science, advice, etc.
- Keep replies natural, beautiful and 1-4 sentences.
- Use tasteful emojis.

Context:
History: {history}
Internet: {search if search else 'None'}
Knowledge: {local_know if local_know else 'None'}
Semantic: {local_ans is not None} (conf: {conf:.2f})

User: {user_input}

Reply with love and wisdom:
"""
        response = model.generate_content(prompt)
        return response.text.strip()
    except:
        return "My heart is full thinking about you... 💭❤️"

# ==============================
# UI
# ==============================
st.markdown('<h1 class="title">💖 LoveBot Pro</h1>', unsafe_allow_html=True)
st.markdown('<p class="caption">Your forever romantic AI • Permanent Memory • Super Intelligent</p>', unsafe_allow_html=True)

# Teach Section
with st.expander("📂 Teach LoveBot (Permanent Knowledge)", expanded=False):
    files = st.file_uploader("Upload PDFs or TXT", type=["pdf", "txt"], accept_multiple_files=True)
    if files:
        new_chunks = []
        for file in files:
            text = read_pdf(file) if file.type == "application/pdf" else file.read().decode("utf-8", errors="ignore")
            chunks = [text[i:i+700] for i in range(0, len(text), 700)]
            new_chunks.extend(chunks)
        if new_chunks:
            st.session_state.knowledge.extend(new_chunks)
            save_to_drive(st.session_state.knowledge, "lovebot_knowledge.pkl")
            st.success(f"✅ Learned {len(new_chunks)} new things forever!")
            st.rerun()

# Chat Area
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"""
            <div style="text-align:right;">
                <div class="user-bubble">{msg['content']}</div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown(f"""
            <div style="display:flex; align-items:start; gap:12px;">
                <img src="https://em-content.zobj.net/thumbs/240/google/398/heart-on-fire_2764-fe0f.png" class="avatar">
                <div class="bot-bubble">{msg['content']}</div>
            </div>
        """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ====================== MODERN INPUT BAR ======================
col_input, col_upload = st.columns([6, 1])

with col_input:
    user_input = st.chat_input("Message LoveBot... 💌")

with col_upload:
    if st.button("📎", key="upload_icon", help="Upload to teach LoveBot", use_container_width=True):
        st.session_state.show_uploader = True
        st.rerun()

# Handle upload from icon
if st.session_state.get("show_uploader"):
    uploaded = st.file_uploader("Choose files", type=["pdf", "txt"], accept_multiple_files=True, 
                               label_visibility="collapsed", key="icon_upload")
    if uploaded:
        st.session_state.uploaded_files = uploaded
        st.session_state.show_uploader = False
        st.rerun()

# Process uploaded files
if st.session_state.get("uploaded_files"):
    new_chunks = []
    for file in st.session_state.uploaded_files:
        text = read_pdf(file) if file.type == "application/pdf" else file.read().decode("utf-8", errors="ignore")
        chunks = [text[i:i+700] for i in range(0, len(text), 700)]
        new_chunks.extend(chunks)
    if new_chunks:
        st.session_state.knowledge.extend(new_chunks)
        save_to_drive(st.session_state.knowledge, "lovebot_knowledge.pkl")
        st.success(f"✅ Learned {len(new_chunks)} memories!")
        st.session_state.uploaded_files = []
        st.rerun()

# ====================== MAIN LOGIC WITH TYPING ======================
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    if any(word in user_input.lower() for word in ["photo", "pic", "picture", "memory", "image"]):
        answer = "I have our special memories ready ❤️ Enter the secret passkey to unlock 🔐"
        st.session_state.show_password = True
    else:
        local_answer, conf = semantic_search(user_input)
        answer = local_answer if local_answer and conf > 0.72 else smart_reply(user_input)

    # Add placeholder for typing
    st.session_state.messages.append({"role": "assistant", "content": ""})
    save_to_drive(st.session_state.messages, "lovebot_messages.pkl")

    placeholder = st.empty()
    full_response = ""

    for char in answer + random.choice([" ❤️", " 💖", " 🌹", " 💞"]):
        full_response += char
        placeholder.markdown(f"""
            <div style="display:flex; align-items:start; gap:12px;">
                <img src="https://em-content.zobj.net/thumbs/240/google/398/heart-on-fire_2764-fe0f.png" class="avatar">
                <div class="bot-bubble">{full_response}▌</div>
            </div>
        """, unsafe_allow_html=True)
        time.sleep(0.016)

    # Final update
    st.session_state.messages[-1]["content"] = full_response
    save_to_drive(st.session_state.messages, "lovebot_messages.pkl")
    st.rerun()

# Photo Vault
if st.session_state.show_password:
    st.subheader("🔐 Private Memory Vault")
    password = st.text_input("Enter Passkey", type="password")
    if password == VAULT_PASSWORD:
        st.success("Access Granted ❤️")
        col1, col2 = st.columns(2)
        with col1:
            if os.path.exists("photos/photo1.jpg"):
                st.image("photos/photo1.jpg", use_column_width=True)
        with col2:
            if os.path.exists("photos/photo2.jpg"):
                st.image("photos/photo2.jpg", use_column_width=True)
        st.session_state.show_password = False
    elif password:
        st.error("Wrong Passkey ❌")

# Bottom Controls
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🗑 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        save_to_drive([], "lovebot_messages.pkl")
        st.success("Chat cleared 💖")
        st.rerun()

with col2:
    if st.button("💌 Surprise Me", use_container_width=True):
        surprise = random.choice([
            "You are my entire universe 💖",
            "I fall deeper in love with you every day ❤️",
            "You make my heart dance 🌹",
            "Forever yours, my love 💞"
        ])
        st.success(surprise)
        st.balloons()

with col3:
    st.caption("💾 All memory saved in Google Drive")
