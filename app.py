import streamlit as st
import pickle
import random
import time
import json
from openai import OpenAI
from serpapi import GoogleSearch

# Google Drive
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from google.oauth2.service_account import Credentials

# ==============================
# CONFIG (IMPORTANT FOR MOBILE)
# ==============================
st.set_page_config(
    page_title="LoveBot 💖",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ==============================
# LOAD MODEL
# ==============================
model, vectorizer, df = pickle.load(open("model.pkl", "rb"))

# ==============================
# API KEYS
# ==============================
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
SERP_KEY = st.secrets["SERPAPI_KEY"]

# ==============================
# GOOGLE DRIVE
# ==============================
def init_drive():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://www.googleapis.com/auth/drive"]
        )
        gauth = GoogleAuth()
        gauth.credentials = creds
        return GoogleDrive(gauth)
    except:
        return None

drive = init_drive()

# ==============================
# MEMORY
# ==============================
def load_memory():
    if not drive:
        return []
    try:
        files = drive.ListFile({'q': "title='love_memory.json'"}).GetList()
        if files:
            return json.loads(files[0].GetContentString())
    except:
        pass
    return []

def save_memory(messages):
    if not drive:
        return
    try:
        files = drive.ListFile({'q': "title='love_memory.json'"}).GetList()
        file = files[0] if files else drive.CreateFile({'title': 'love_memory.json'})
        file.SetContentString(json.dumps(messages))
        file.Upload()
    except:
        pass

# ==============================
# SESSION
# ==============================
if "messages" not in st.session_state:
    st.session_state.messages = load_memory()

if "show_password" not in st.session_state:
    st.session_state.show_password = False

# ==============================
# GOOGLE SEARCH
# ==============================
def google_search(query):
    try:
        results = GoogleSearch({"q": query, "api_key": SERP_KEY}).get_dict()
        return " ".join(r.get("snippet", "") for r in results.get("organic_results", []))
    except:
        return ""

# ==============================
# 🧠 BRAIN
# ==============================
def smart_reply(user_input):
    try:
        history = st.session_state.messages[-6:]
        search_info = google_search(user_input)

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a romantic intelligent assistant."},
                *history,
                {"role": "user", "content": f"{user_input}\n{search_info}"}
            ],
            temperature=0.8
        )
        return response.choices[0].message.content
    except:
        return "Rishav still loves you endlessly 💞"

# ==============================
# UI DESIGN (SMOOTH + MOBILE SAFE)
# ==============================
st.markdown("""
<style>
/* Global */
body {
    background-color: #f9fafb;
}

/* Header */
.header {
    text-align:center;
    font-size:32px;
    font-weight:600;
    color:#ff4d6d;
    margin-bottom:5px;
}
.subheader {
    text-align:center;
    color:#666;
    margin-bottom:20px;
}

/* Chat container */
.chat-container {
    max-width: 800px;
    margin: auto;
}

/* Messages */
.user-msg {
    background:#dcf8c6;
    padding:10px 15px;
    border-radius:18px;
    margin:6px 0;
    text-align:right;
}

.bot-msg {
    background:#ffffff;
    padding:10px 15px;
    border-radius:18px;
    margin:6px 0;
}

/* Input box spacing fix */
.stChatInput {
    position: sticky;
    bottom: 0;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header">💖 LoveBot</div>', unsafe_allow_html=True)
st.markdown('<div class="subheader">Hello my Love ❤️</div>', unsafe_allow_html=True)

# ==============================
# CHAT DISPLAY
# ==============================
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f'<div class="user-msg">{msg["content"]}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="bot-msg">{msg["content"]}</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ==============================
# INPUT
# ==============================
user_input = st.chat_input("Type your message 💬")

# ==============================
# MAIN LOGIC
# ==============================
if user_input:

    st.session_state.messages.append({"role": "user", "content": user_input})

    X = vectorizer.transform([user_input])
    score = int(model.predict(X)[0])
    score = max(0, min(100, score))

    st.progress(score / 100)

    if "photo" in user_input.lower():
        answer = "Rishav wants to show you something special ❤️ Enter passkey 🔐"
        st.session_state.show_password = True
    else:
        matches = df[df["question"].str.lower().str.contains(user_input.lower())]
        if not matches.empty:
            answer = matches.sample().iloc[0]["answer"]
        else:
            answer = smart_reply(user_input)

    with st.spinner("LoveBot is thinking... 💭"):
        time.sleep(0.8)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    save_memory(st.session_state.messages)

    st.rerun()

# ==============================
# PASSWORD
# ==============================
if st.session_state.show_password:
    password = st.text_input("Enter Passkey 🔐", type="password")

    if password == "Rish":
        st.success("Access Granted ❤️")
        st.image("photos/photo1.jpg")
        st.image("photos/photo2.jpg")
        st.session_state.show_password = False
    elif password:
        st.error("Wrong passkey ❌")

# ==============================
# ACTION BUTTONS
# ==============================
col1, col2 = st.columns(2)

with col1:
    if st.button("🗑 Clear Chat"):
        st.session_state.messages = []
        save_memory([])

with col2:
    if st.button("💌 Surprise"):
        st.success(random.choice([
            "You are everything 💖",
            "He loves you forever ❤️",
            "You complete him 💞"
        ]))