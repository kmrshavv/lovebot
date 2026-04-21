import streamlit as st
import pickle, random, time, io
import numpy as np
from serpapi import GoogleSearch
import google.generativeai as genai
from pypdf import PdfReader
from datetime import datetime

# ==============================
# ADVANCED EMBEDDINGS
# ==============================
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

# ==============================
# GOOGLE DRIVE
# ==============================
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload, MediaIoBaseDownload

# ==============================
# VOICE SUPPORT
# ==============================
import speech_recognition as sr

# ==============================
# CONFIG
# ==============================
st.set_page_config(page_title="LoveBot 💖 Pro", layout="wide", page_icon="💖")

# ==============================
# API KEYS
# ==============================
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
SERP_KEY = st.secrets["SERPAPI_KEY"]

# ==============================
# LOAD ADVANCED SEMANTIC MODEL
# ==============================
@st.cache_resource
def load_advanced_model():
    try:
        with open("model_advanced.pkl", "rb") as f:
            data = pickle.load(f)
        st.toast("✅ Advanced Semantic Model Loaded (Human-like Understanding)", icon="🧠")
        return data["df"], data["embedder"], data["embeddings"]
    except:
        st.warning("⚠️ Advanced model not found. Falling back to basic model.")
        model, vectorizer, df = pickle.load(open("model.pkl", "rb"))
        return df, None, None

df, embedder, embeddings = load_advanced_model()

# ==============================
# GOOGLE DRIVE SETUP
# ==============================
if "drive_service" not in st.session_state:
    try:
        creds_info = dict(st.secrets["google_drive"])
        credentials = service_account.Credentials.from_service_account_info(
            creds_info,
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        st.session_state.drive_service = build("drive", "v3", credentials=credentials)
        st.toast("💾 Connected to Google Drive — Permanent Memory Activated!", icon="✅")
    except Exception as e:
        st.error("Google Drive connection failed. Check secrets.")
        st.session_state.drive_service = None

# ==============================
# PERSISTENT STORAGE
# ==============================
def load_from_drive(filename):
    if not st.session_state.get("drive_service"):
        return [] if "messages" in filename else []
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
        return [] if "messages" in filename else []
    except:
        return [] if "messages" in filename else []

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
def google_search(query):
    try:
        res = GoogleSearch({
            "q": query, "api_key": SERP_KEY, "num": 7,
            "gl": "in", "hl": "en"
        }).get_dict()
        
        results = []
        for r in res.get("organic_results", [])[:7]:
            results.append(f"📌 {r.get('title','')}\n{r.get('snippet','')}\n🔗 {r.get('link','')}")
        return results
    except:
        return []

# ==============================
# PDF READER
# ==============================
def read_pdf(file):
    text = ""
    pdf = PdfReader(file)
    for page in pdf.pages:
        text += page.extract_text() or ""
    return text

# ==============================
# SEMANTIC RETRIEVAL (Advanced)
# ==============================
def semantic_search(query, top_k=3):
    if embedder is None or embeddings is None:
        return None, 0.0
    try:
        query_emb = embedder.encode([query])
        sims = cosine_similarity(query_emb, embeddings)[0]
        top_idx = sims.argsort()[-top_k:][::-1]
        best_score = sims[top_idx[0]]
        
        if best_score > 0.68:
            return df.iloc[top_idx[0]]["answer"], best_score
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
# SMART REPLY (Most Advanced)
# ==============================
def smart_reply(user_input):
    try:
        model_ai = genai.GenerativeModel("gemini-1.5-flash")

        history = st.session_state.messages[-10:]
        search_results = google_search(user_input)
        local_knowledge = retrieve_knowledge(user_input)
        
        # Try semantic match first
        local_answer, confidence = semantic_search(user_input)

        prompt = f"""
You are LoveBot 💖 — a deeply emotional, romantic, intelligent, and caring AI partner.

Personality Rules:
- Warm, flirty, emotional, and loving
- Short & natural replies (1-3 sentences)
- Use emojis beautifully ❤️💖🌹
- Never repeat yourself
- You have permanent memory in Google Drive

Context:
Conversation: {history}
Internet Research: {search_results if search_results else "None"}
Permanent Knowledge: {local_knowledge if local_knowledge else "None"}
Semantic Match Found: {local_answer is not None} (Confidence: {confidence:.2f})

User: {user_input}

Answer with love and intelligence:
"""

        response = model_ai.generate_content(prompt)
        return response.text.strip()

    except Exception as e:
        print(e)
        return "My heart is thinking so deeply about you... 💭❤️"

# ==============================
# VOICE INPUT
# ==============================
def voice_to_text():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        st.info("🎤 Listening... Speak now (5 seconds)")
        try:
            audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
            text = recognizer.recognize_google(audio, language="en-IN")
            return text
        except:
            st.error("Could not understand audio. Try again.")
            return None

# ==============================
# UI
# ==============================
st.title("💖 LoveBot Pro")
st.caption(f"🧠 **Permanent Google Drive Mind** | Knowledge: **{len(st.session_state.knowledge)}** | Semantic Intelligence Active")

# File Upload
st.subheader("📂 Teach LoveBot (Saved Forever in Google Drive)")
files = st.file_uploader("Upload PDFs or Text files", type=["pdf", "txt"], accept_multiple_files=True)

if files:
    new_chunks = []
    for file in files:
        if file.type == "application/pdf":
            text = read_pdf(file)
        else:
            text = file.read().decode("utf-8")
        chunks = [text[i:i+700] for i in range(0, len(text), 700)]
        new_chunks.extend(chunks)
    
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

# Input Area
col_input1, col_input2 = st.columns([4, 1])
with col_input1:
    user_input = st.chat_input("Type your message… 💬❤️")

with col_input2:
    if st.button("🎤 Voice", use_container_width=True):
        spoken = voice_to_text()
        if spoken:
            user_input = spoken

# Main Logic
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    if any(word in user_input.lower() for word in ["photo", "pic", "picture", "memory", "memories", "image"]):
        answer = "I have our special memories ready ❤️ Enter the secret passkey to unlock 🔐"
        st.session_state.show_password = True
    else:
        # Try quick semantic match
        local_answer, conf = semantic_search(user_input)
        if local_answer and conf > 0.72:
            answer = local_answer
        else:
            answer = smart_reply(user_input)

    with st.spinner("Thinking deeply with all my heart… 💭❤️"):
        time.sleep(0.9)

    answer += random.choice([" ❤️", " 💖", " 🌹", " 💞", " 🧠"])
    
    st.session_state.messages.append({"role": "assistant", "content": answer})
    save_to_drive(st.session_state.messages, "lovebot_messages.pkl")
    st.rerun()

# Photo Vault
if st.session_state.show_password:
    st.subheader("🔐 Private Memory Vault")
    password = st.text_input("Enter Passkey", type="password", key="pass_input")
    
    if password == "Rish":
        st.success("Access Granted ❤️")
        col1, col2 = st.columns(2)
        with col1: st.image("photos/photo1.jpg", use_column_width=True)
        with col2: st.image("photos/photo2.jpg", use_column_width=True)
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
        st.success("Fresh Start 💖")
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
    st.caption("💾 **All chats & knowledge saved in Google Drive**\nSemantic + Gemini + Voice Enabled")
