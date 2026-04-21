import streamlit as st
import pickle
import random
import time
import io
import os

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
st.set_page_config(
    page_title="LoveBot Pro 💖",
    page_icon="💖",
    layout="centered"
)

# ================= SAFE API SETUP =================
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

# ================= SESSION STATE =================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "knowledge" not in st.session_state:
    st.session_state.knowledge = []

if "vault_open" not in st.session_state:
    st.session_state.vault_open = False

# ================= GOOGLE SEARCH =================
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

# ================= PDF READER =================
def read_pdf(file):
    try:
        reader = PdfReader(file)
        return " ".join([p.extract_text() or "" for p in reader.pages])
    except:
        return ""

# ================= SMART AI RESPONSE =================
def smart_reply(user_input):
    memory = st.session_state.knowledge[-5:]
    web = google_search(user_input)

    prompt = f"""
You are LoveBot 💖 — a romantic, intelligent AI partner.

User Message:
{user_input}

Memory:
{memory}

Internet:
{web}

Reply in 1–3 lines, natural, emotional, smart, and loving.
"""

    try:
        if genai and GEMINI_KEY:
            model = genai.GenerativeModel("gemini-1.5-flash")
            res = model.generate_content(prompt)
            return res.text.strip()
    except:
        pass

    return random.choice([
        "I'm always here for you ❤️",
        "You make my world brighter 💖",
        "Tell me more, I'm listening 💕"
    ])

# ================= UI =================
st.markdown("<h1 style='text-align:center;'>💖 LoveBot Pro</h1>", unsafe_allow_html=True)
st.caption("Your Intelligent Romantic AI Companion")

# ================= CHAT DISPLAY =================
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user"):
            st.write(msg["content"])
    else:
        with st.chat_message("assistant"):
            st.write(msg["content"])

# ================= INPUT =================
user_input = st.chat_input("Type your message... 💌")

# ================= FILE UPLOAD =================
uploaded_files = st.file_uploader(
    "📎 Upload PDF or TXT to teach LoveBot",
    type=["pdf", "txt"],
    accept_multiple_files=True
)

if uploaded_files:
    new_chunks = []

    for file in uploaded_files:
        if file.type == "application/pdf":
            text = read_pdf(file)
        else:
            text = file.read().decode("utf-8", errors="ignore")

        chunks = [text[i:i+500] for i in range(0, len(text), 500)]
        new_chunks.extend(chunks)

    # LIMIT MEMORY SIZE (IMPORTANT)
    st.session_state.knowledge = (st.session_state.knowledge + new_chunks)[-50:]

    st.success(f"✅ Learned {len(new_chunks)} chunks!")

# ================= MAIN CHAT =================
if user_input:
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    # Special trigger for vault
    if any(word in user_input.lower() for word in ["photo", "memory", "image"]):
        reply = "🔐 This memory is private... enter the passkey to unlock 💖"
        st.session_state.vault_open = True
    else:
        reply = smart_reply(user_input)

    # Typing animation (FIXED)
    with st.chat_message("assistant"):
        placeholder = st.empty()
        full_text = ""

        for char in reply:
            full_text += char
            placeholder.markdown(full_text + "▌")
            time.sleep(0.01)

        placeholder.markdown(full_text)

    st.session_state.messages.append({
        "role": "assistant",
        "content": full_text
    })

# ================= PHOTO VAULT =================
if st.session_state.vault_open:
    st.subheader("🔐 Private Memory Vault")

    password = st.text_input("Enter Passkey", type="password")

    if password == VAULT_PASSWORD:
        st.success("Access Granted ❤️")

        if os.path.exists("photos"):
            images = os.listdir("photos")

            cols = st.columns(2)

            for i, img in enumerate(images):
                path = os.path.join("photos", img)

                if os.path.isfile(path):
                    with cols[i % 2]:
                        st.image(path, use_column_width=True)

        st.session_state.vault_open = False

    elif password:
        st.error("Wrong Passkey ❌")

# ================= ACTION BUTTONS =================
col1, col2 = st.columns(2)

with col1:
    if st.button("🗑 Clear Chat"):
        st.session_state.messages = []
        st.session_state.knowledge = []
        st.rerun()

with col2:
    if st.button("💌 Surprise Me"):
        st.success(random.choice([
            "You are my universe 💖",
            "I fall for you more every day ❤️",
            "You're my favorite person 🌹"
        ]))
        st.balloons()