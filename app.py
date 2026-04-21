import streamlit as st
import pickle
import random
import time
import os
import numpy as np
import re

# ================= SAFE IMPORTS =================
try:
    from serpapi import GoogleSearch
except:
    GoogleSearch = None

try:
    import google.generativeai as genai
except:
    genai = None

from pypdf import PdfReader

# ================= PAGE CONFIG =================
st.set_page_config(page_title="LoveBot God Mode 💖", layout="centered")

# ================= API =================
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY", None)
SERP_KEY = st.secrets.get("SERPAPI_KEY", None)
VAULT_PASSWORD = st.secrets.get("VAULT_PASSWORD", "Rish")

if genai and GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

# ================= LOAD MODEL =================
@st.cache_resource
def load_model():
    try:
        with open("model_advanced.pkl", "rb") as f:
            return pickle.load(f)
    except:
        return None

model_data = load_model()

# ================= SESSION =================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "knowledge" not in st.session_state:
    st.session_state.knowledge = []

if "vault_open" not in st.session_state:
    st.session_state.vault_open = False

# ================= PDF =================
def read_pdf(file):
    try:
        reader = PdfReader(file)
        return " ".join([p.extract_text() or "" for p in reader.pages])
    except:
        return ""

# ================= EMOTION DETECTION =================
def detect_emotion(text):
    text = text.lower()

    emotions = {
        "love": ["love", "miss you", "hug", "kiss", "forever"],
        "sad": ["sad", "cry", "hurt", "alone", "miss"],
        "happy": ["happy", "excited", "great", "amazing"],
        "angry": ["angry", "hate", "annoyed", "frustrated"],
        "flirty": ["baby", "jaan", "cutie", "hot", "date"]
    }

    scores = {k: 0 for k in emotions}

    for emotion, words in emotions.items():
        for w in words:
            if w in text:
                scores[emotion] += 1

    return max(scores, key=scores.get)

# ================= SEMANTIC SEARCH =================
def semantic_search(query, top_k=3):
    if not model_data:
        return []

    try:
        embedder = model_data["embedder"]
        embeddings = model_data["embeddings"]
        df = model_data["df"]

        q_vec = embedder.encode([query])[0]

        sims = np.dot(embeddings, q_vec) / (
            np.linalg.norm(embeddings, axis=1) * np.linalg.norm(q_vec)
        )

        top_idx = np.argsort(sims)[-top_k:][::-1]

        return df.iloc[top_idx]["answer"].tolist()

    except:
        return []

# ================= GOOGLE =================
def google_search(query):
    if not GoogleSearch or not SERP_KEY:
        return []

    try:
        res = GoogleSearch({
            "q": query,
            "api_key": SERP_KEY,
            "num": 3
        }).get_dict()

        return [r.get("snippet", "") for r in res.get("organic_results", [])[:3]]
    except:
        return []

# ================= STREAM =================
def stream_reply(prompt):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(prompt, stream=True)

        for chunk in response:
            if hasattr(chunk, "text"):
                yield chunk.text

    except:
        fallback = "I'm here for you ❤️"
        for c in fallback:
            yield c

# ================= MAIN AI =================
def generate_reply(user_input):

    emotion = detect_emotion(user_input)

    semantic_context = semantic_search(user_input)
    memory_context = st.session_state.knowledge[-5:]
    web_context = google_search(user_input)

    prompt = f"""
You are LoveBot 💖 — emotionally intelligent AI.

Detected Emotion: {emotion}

User:
{user_input}

Relevant Knowledge:
{semantic_context}

Memory:
{memory_context}

Internet:
{web_context}

Rules:
- Adapt tone based on emotion
- If sad → comforting
- If love → romantic
- If angry → calm and supportive
- If flirty → playful

Reply in 2–4 lines.
"""

    return stream_reply(prompt)

# ================= UI =================
st.markdown("<h1 style='text-align:center;'>💖 LoveBot GOD+</h1>", unsafe_allow_html=True)

# ================= CHAT =================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ================= INPUT =================
col1, col2 = st.columns([6, 1])

with col1:
    user_input = st.chat_input("Type your message... 💌")

with col2:
    uploaded_files = st.file_uploader(
        "📎",
        type=["pdf", "txt"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

# ================= UPLOAD =================
if uploaded_files:
    chunks = []

    for file in uploaded_files:
        if file.type == "application/pdf":
            text = read_pdf(file)
        else:
            text = file.read().decode("utf-8", errors="ignore")

        chunks.extend([text[i:i+500] for i in range(0, len(text), 500)])

    st.session_state.knowledge = (st.session_state.knowledge + chunks)[-50:]
    st.success("Learned successfully!")

# ================= CHAT FLOW =================
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})

    if any(w in user_input.lower() for w in ["photo", "image", "memory"]):
        reply = "🔐 Private memory. Enter passkey 💖"
        st.session_state.vault_open = True

        with st.chat_message("assistant"):
            st.write(reply)

        st.session_state.messages.append({"role": "assistant", "content": reply})

    else:
        with st.chat_message("assistant"):
            placeholder = st.empty()
            full_text = ""

            for chunk in generate_reply(user_input):
                full_text += chunk
                placeholder.markdown(full_text + "▌")

            placeholder.markdown(full_text)

        st.session_state.messages.append({"role": "assistant", "content": full_text})

# ================= VAULT =================
if st.session_state.vault_open:
    st.subheader("🔐 Private Vault")

    pwd = st.text_input("Enter Passkey", type="password")

    if pwd == VAULT_PASSWORD:
        st.success("Access Granted ❤️")

        if os.path.exists("photos"):
            imgs = os.listdir("photos")
            cols = st.columns(2)

            for i, img in enumerate(imgs):
                path = os.path.join("photos", img)
                if os.path.isfile(path):
                    with cols[i % 2]:
                        st.image(path, use_column_width=True)

        st.session_state.vault_open = False

    elif pwd:
        st.error("Wrong passkey ❌")

# ================= ACTION =================
colA, colB = st.columns(2)

with colA:
    if st.button("🗑 Clear Chat"):
        st.session_state.messages = []
        st.session_state.knowledge = []
        st.rerun()

with colB:
    if st.button("💌 Surprise"):
        st.success(random.choice([
            "You’re everything to me 💖",
            "I’m always with you ❤️",
            "You make my world better 🌹"
        ]))
        st.balloons()