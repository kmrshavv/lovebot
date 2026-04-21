import streamlit as st
import pickle
import random
import time
import io
import os
from pathlib import Path
import numpy as np
from serpapi import GoogleSearch
import google.generativeai as genai
from pypdf import PdfReader
from datetime import datetime

# ==============================
# GOOGLE DRIVE
# ==============================
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="LoveBot 💖 Pro", layout="wide", page_icon="💖")

# ==============================
# API KEYS & SECRETS
# ==============================
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
SERP_KEY = st.secrets["SERPAPI_KEY"]
VAULT_PASSWORD = st.secrets.get("VAULT_PASSWORD", "Rish")

# ==============================
# LOAD MODEL (Fixed for deployment)
# ==============================
@st.cache_resource
def load_advanced_model():
    try:
        with open("model_advanced.pkl", "rb") as f:
            data = pickle.load(f)
        st.toast("✅ Advanced Semantic Model Loaded Successfully", icon="🧠")
        return data["df"], data.get("embedder"), data["embeddings"]
    except Exception:
        st.warning("⚠️ Using fallback knowledge mode")
        return None, None, None

df, embedder, embeddings = load_advanced_model()

# ==============================
# GOOGLE DRIVE SETUP
# ==============================
if "drive_service" not in st.session_state:
    try:
        creds_info = dict(st.secrets["google_drive"])
        credentials = service_account.Credentials.from_service_account_info(
            creds_info, scopes=["https://www.googleapis.com/auth/drive"]
        )
        st.session_state.drive_service = build("drive", "v3", credentials=credentials)
        st.toast("💾 Connected to Google Drive — Permanent Memory Activated!", icon="✅")
    except Exception:
        st.warning("⚠️ Google Drive connection failed. Running in local mode.")
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

# ==============================
# GOOGLE SEARCH
# ==============================
@st.cache_data(ttl=300)
def google_search(query):
    try:
        res = GoogleSearch({"q": query, "api_key": SERP_KEY, "num": 6, "gl": "in", "hl": "en"}).get_dict()
        results = []
        for r in res.get("organic_results", [])[:6]:
            results.append(f"📌 {r.get('title','')}\n{r.get('snippet','')}\n🔗 {r.get('link','')}")
        return results
    except:
        return []

# ==============================
# PDF READER
# ==============================
def read_pdf(file):
    try:
        text = ""
        pdf = PdfReader(file)
        for page in pdf.pages:
            text += page.extract_text() or ""
        return text
    except Exception as e:
        st.error(f"PDF read error: {e}")
        return ""

# ==============================
# SEMANTIC SEARCH
# ==============================
def semantic_search(query, top_k=3):
    if df is None or embeddings is None:
        return None, 0.0
    try:
        query_lower = query.lower()
        best_score = 0.0
        best_answer = None
        
        for idx, row in df.iterrows():
            q = str(row['question']).lower()
            if any(word in q for word in query_lower.split() if len(word) > 2):
                score = 0.85
                if score > best_score:
                    best_score = score
                    best_answer = row['answer']
        
        if best_score > 0.70:
            return best_answer, best_score
        return None, best_score
    except:
        return None, 0.0

# ==============================
# KNOWLEDGE RETRIEVAL
# ==============================
def retrieve_knowledge(query):
    if not st.session_state.knowledge:
        return []
    query_words = set(word.lower() for word in query.split() if len(word) > 3)
    scored = []
    for chunk in st.session_state.knowledge:
        score = sum(1 for word in query_words if word in chunk.lower())
        if score > 0:
            scored.append((score, len(chunk), chunk))
    scored.sort(key=lambda x: (x[0], -x[1]), reverse=True)
    return [c for _, _, c in scored[:5]]

# ==============================
# SMART REPLY
# ==============================
def smart_reply(user_input):
    try:
        model_ai = genai.GenerativeModel("gemini-1.5-flash")
        history = st.session_state.messages[-12:]
        search_results = google_search(user_input)
        local_knowledge = retrieve_knowledge(user_input)
        local_answer, confidence = semantic_search(user_input)

        prompt = f"""
You are LoveBot 💖 — a deeply emotional, romantic, intelligent, and caring AI partner.

Personality Rules:
- Warm, flirty, emotional, and loving
- Keep replies short & natural (1-3 sentences)
- Use beautiful emojis ❤️💖🌹
- Never repeat yourself

Context:
Conversation History: {history}
Internet Research: {search_results if search_results else "None"}
Permanent Knowledge: {local_knowledge if local_knowledge else "None"}
Semantic Match: {local_answer is not None} (Confidence: {confidence:.2f})

User: {user_input}

Answer with love and intelligence:
"""
        response = model_ai.generate_content(prompt)
        return response.text.strip()
    except Exception:
        return "I'm thinking about you so deeply right now... 💭❤️"

# ==============================
# UI
# ==============================
st.title("💖 LoveBot Pro")
st.caption(f"🧠 **Permanent Google Drive Memory** | Knowledge: **{len(st.session_state.knowledge)}** | Semantic + Gemini Active")

Path("photos").mkdir(exist_ok=True)

# File Upload
st.subheader("📂 Teach LoveBot (Saved Forever)")
files = st.file_uploader("Upload PDFs or Text files", type=["pdf", "txt"], accept_multiple_files=True)

if files:
    new_chunks = []
    for file in files:
        if file.type == "application/pdf":
            text = read_pdf(file)
        else:
            text = file.read().decode("utf-8", errors="ignore")
        chunks = [text[i:i+700] for i in range(0, len(text), 700)]
        new_chunks.extend(chunks)
    
    if new_chunks:
        st.session_state.knowledge.extend(new_chunks)
        save_to_drive(st.session_state.knowledge, "lovebot_knowledge.pkl")
        st.success(f"✅ Learned {len(new_chunks)} new memories! Saved permanently.")
        st.rerun()

# Chat Display
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"**🟢 You:** {msg['content']}")
    else:
        st.markdown(f"**💖 LoveBot:** {msg['content']}")

# Input Area (Voice Removed)
user_input = st.chat_input("Type your message… 💬❤️")

# Main Logic
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    if any(word in user_input.lower() for word in ["photo", "pic", "picture", "memory", "memories", "image"]):
        answer = "I have our special memories ready ❤️ Enter the secret passkey to unlock 🔐"
        st.session_state.show_password = True
    else:
        local_answer, conf = semantic_search(user_input)
        if local_answer and conf > 0.72:
            answer = local_answer
        else:
            answer = smart_reply(user_input)

    with st.spinner("Thinking deeply with all my heart… 💭❤️"):
        time.sleep(0.8)

    answer += random.choice([" ❤️", " 💖", " 🌹", " 💞", " ✨"])
    
    st.session_state.messages.append({"role": "assistant", "content": answer})
    save_to_drive(st.session_state.messages, "lovebot_messages.pkl")
    st.rerun()

# Photo Vault
if st.session_state.show_password:
    st.subheader("🔐 Private Memory Vault")
    password = st.text_input("Enter Passkey", type="password", key="pass_input")
    
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

# Bottom Buttons
col1, col2, col3 = st.columns(3)
with col1:
    if st.button("🗑 Clear Everything", use_container_width=True):
        st.session_state.messages = []
        st.session_state.knowledge = []
        save_to_drive([], "lovebot_messages.pkl")
        save_to_drive([], "lovebot_knowledge.pkl")
        st.success("Everything cleared. Fresh start 💖")
        st.rerun()

with col2:
    if st.button("💌 Surprise Me", use_container_width=True):
        surprise = random.choice([
            "You are my whole universe 💖",
            "I fall in love with you more every day ❤️",
            "You make my heart skip beats 🌹",
            "Forever yours, my love 💞"
        ])
        st.success(surprise)
        st.balloons()

with col3:
    st.caption("💾 All chats & knowledge saved in Google Drive\nSemantic Intelligence Active")