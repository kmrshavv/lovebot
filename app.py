import streamlit as st
import pickle
import random
import os
import time
import json
from openai import OpenAI
from serpapi import GoogleSearch

# Google Drive (FIXED)
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from google.oauth2.service_account import Credentials

# ==============================
# LOAD MODEL
# ==============================
model, vectorizer, df = pickle.load(open("model.pkl", "rb"))

# ==============================
# API KEYS FROM SECRETS
# ==============================
try:
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    SERP_KEY = st.secrets["SERPAPI_KEY"]
except:
    st.error("❌ API keys not set in Streamlit Secrets")
    st.stop()

# ==============================
# GOOGLE DRIVE INIT (FIXED)
# ==============================
def init_drive():
    try:
        scope = ["https://www.googleapis.com/auth/drive"]

        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=scope
        )

        gauth = GoogleAuth()
        gauth.credentials = creds

        return GoogleDrive(gauth)
    except:
        return None

drive = init_drive()

if not drive:
    st.warning("⚠️ Drive not connected. Memory disabled.")

# ==============================
# MEMORY FUNCTIONS
# ==============================
def load_memory():
    if not drive:
        return []

    try:
        files = drive.ListFile({
            'q': "title='love_memory.json' and trashed=false"
        }).GetList()

        if files:
            return json.loads(files[0].GetContentString())
    except:
        pass

    return []

def save_memory(messages):
    if not drive:
        return

    try:
        files = drive.ListFile({
            'q': "title='love_memory.json' and trashed=false"
        }).GetList()

        file = files[0] if files else drive.CreateFile({'title': 'love_memory.json'})
        file.SetContentString(json.dumps(messages, indent=2))
        file.Upload()
    except:
        pass

# ==============================
# SESSION STATE
# ==============================
if "messages" not in st.session_state:
    st.session_state.messages = load_memory()

if "show_password" not in st.session_state:
    st.session_state.show_password = False

# ==============================
# GOOGLE SEARCH
# ==============================
def google_search(query):
    if not SERP_KEY:
        return ""

    try:
        params = {"q": query, "api_key": SERP_KEY, "num": 3}
        results = GoogleSearch(params).get_dict()
        return " ".join(r.get("snippet", "") for r in results.get("organic_results", []))
    except:
        return ""

# ==============================
# PERSONALIZATION
# ==============================
def personalize(text):
    text = text.replace(" I ", " Rishav ")
    text = text.replace(" my ", " his ")
    if "Rishav" not in text:
        text = "Rishav wants you to know, " + text
    return text

# ==============================
# UI
# ==============================
st.set_page_config(page_title="LoveBot 💖", page_icon="❤️")

st.markdown("""
<style>
body {
    background: #f8fafc;
}
.title {
    text-align:center;
    font-size:42px;
    font-weight:bold;
    color:#ff4d6d;
}
.subtitle {
    text-align:center;
    margin-bottom:25px;
    color:#555;
}
.user {
    background: #dcf8c6;
    padding: 10px 14px;
    border-radius: 18px;
    margin: 8px 0;
    max-width: 70%;
    margin-left: auto;
}
.bot {
    background: #ffffff;
    padding: 10px 14px;
    border-radius: 18px;
    margin: 8px 0;
    max-width: 70%;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="title">💖 LoveBot</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Hello my Love ❤️</div>', unsafe_allow_html=True)

# ==============================
# CHAT DISPLAY
# ==============================
for msg in st.session_state.messages:
    role_class = "user" if msg["role"] == "user" else "bot"
    st.markdown(f'<div class="{role_class}">{msg["content"]}</div>', unsafe_allow_html=True)

# ==============================
# INPUT
# ==============================
user_input = st.chat_input("Type your message 💬")

# ==============================
# MAIN LOGIC
# ==============================
if user_input:

    st.session_state.messages.append({"role": "user", "content": user_input})

    # Love score
    X = vectorizer.transform([user_input])
    score = int(model.predict(X)[0])
    score = max(0, min(100, score))
    st.progress(score / 100)

    # Photo trigger
    if any(word in user_input.lower() for word in ["photo", "memories", "pics"]):
        answer = "Rishav wants to show you something special ❤️ Enter passkey 🔐"
        st.session_state.show_password = True

    else:
        matches = df[df["question"].str.lower().str.contains(user_input.lower())]

        if not matches.empty:
            answer = personalize(matches.sample().iloc[0]["answer"])
        else:
            try:
                search_info = google_search(user_input)

                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are a romantic assistant."}
                    ] + st.session_state.messages[-5:] + [
                        {"role": "user", "content": f"{user_input}\n{search_info}"}
                    ]
                )

                answer = personalize(response.choices[0].message.content)

            except:
                answer = personalize("Rishav loves you endlessly 💞")

    # Typing delay
    with st.spinner("LoveBot is typing... 💭"):
        time.sleep(1)

    st.session_state.messages.append({"role": "assistant", "content": answer})
    save_memory(st.session_state.messages)

    st.markdown(f'<div class="bot">{answer}</div>', unsafe_allow_html=True)

# ==============================
# PASSWORD (PHOTO VAULT)
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
# BUTTONS
# ==============================
col1, col2 = st.columns(2)

with col1:
    if st.button("🗑 Clear Chat"):
        st.session_state.messages = []
        save_memory([])

with col2:
    if st.button("💌 Surprise"):
        st.success(personalize(random.choice([
            "You are the best thing 💖",
            "He loves you forever ❤️",
            "You complete him 💞"
        ])))