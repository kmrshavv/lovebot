import streamlit as st
import pickle
import random
import os
import numpy as np

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

# ================= CONFIG =================
st.set_page_config(page_title="LoveBot 💖", layout="centered")

# ================= CLEAN UI =================
st.markdown("""
<style>
html, body, [class*="css"] {
    font-family: 'Segoe UI', sans-serif;
}

/* Remove extra space */
.block-container {
    padding-bottom: 120px;
}

/* Bottom bar */
.bottom-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: #0e1117;
    padding: 10px 16px;
    border-top: 1px solid #2a2a2a;
    z-index: 999;
}

/* Chat input */
.stChatInput textarea {
    background: #1a1d24 !important;
    border-radius: 10px !important;
}

/* Upload button */
div[data-testid="stFileUploader"] button {
    height: 42px;
    border-radius: 8px;
    background-color: #262730;
    color: white;
}

/* Hide uploader label */
div[data-testid="stFileUploader"] > label {
    display: none;
}
</style>
""", unsafe_allow_html=True)

# ================= API =================
GEMINI_KEY = st.secrets.get("GEMINI_API_KEY")
SERP_KEY = st.secrets.get("SERPAPI_KEY")
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

# ================= PDF =================
def read_pdf(file):
    try:
        reader = PdfReader(file)
        return " ".join([p.extract_text() or "" for p in reader.pages])
    except:
        return ""

# ================= EMOTION =================
def detect_emotion(text):
    text = text.lower()
    if any(w in text for w in ["sad", "cry", "alone"]):
        return "sad"
    if any(w in text for w in ["love", "miss"]):
        return "love"
    if any(w in text for w in ["angry", "hate"]):
        return "angry"
    return "neutral"

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

        idx = np.argsort(sims)[-top_k:][::-1]
        return df.iloc[idx]["answer"].tolist()

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

# ================= AI =================
def generate_reply(user_input):
    emotion = detect_emotion(user_input)
    semantic = semantic_search(user_input)
    memory = st.session_state.knowledge[-5:]

    prompt = f"""
You are LoveBot 💖

Emotion: {emotion}
User: {user_input}
Knowledge: {semantic}
Memory: {memory}

Reply naturally in 2-3 lines.
"""

    return stream_reply(prompt)

# ================= HEADER =================
st.markdown("<h2 style='text-align:center;'>💖 LoveBot</h2>", unsafe_allow_html=True)

# ================= CHAT =================
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ================= BOTTOM BAR =================
st.markdown('<div class="bottom-bar">', unsafe_allow_html=True)

col1, col2 = st.columns([6,1])

with col1:
    user_input = st.chat_input("Type your message... 💬")

with col2:
    uploaded_files = st.file_uploader(
        "📎",
        type=["pdf","txt"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

st.markdown('</div>', unsafe_allow_html=True)

# ================= UPLOAD =================
if uploaded_files:
    chunks = []
    for file in uploaded_files:
        text = read_pdf(file) if file.type == "application/pdf" else file.read().decode("utf-8","ignore")
        chunks.extend([text[i:i+500] for i in range(0,len(text),500)])

    st.session_state.knowledge = (st.session_state.knowledge + chunks)[-50:]
    st.toast("Learned from files ✅")

# ================= CHAT LOGIC =================
if user_input:
    st.session_state.messages.append({"role":"user","content":user_input})

    with st.chat_message("assistant"):
        placeholder = st.empty()
        full = ""

        for chunk in generate_reply(user_input):
            full += chunk
            placeholder.markdown(full + "▌")

        placeholder.markdown(full)

    st.session_state.messages.append({"role":"assistant","content":full})

# ================= ACTIONS =================
colA, colB = st.columns(2)

with colA:
    if st.button("Clear Chat"):
        st.session_state.messages = []
        st.session_state.knowledge = []
        st.rerun()

with colB:
    if st.button("Surprise"):
        st.success(random.choice([
            "You mean everything 💖",
            "I'm always here ❤️",
            "You make me smile 🌹"
        ]))