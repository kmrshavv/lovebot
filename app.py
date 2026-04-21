import streamlit as st
import pickle
import random
import time
import json
import openai
import google.generativeai as genai
from serpapi import GoogleSearch

# Google Drive
from pydrive2.auth import GoogleAuth
from pydrive2.drive import GoogleDrive
from google.oauth2.service_account import Credentials

# ==============================
# PAGE CONFIG
# ==============================
st.set_page_config(page_title="LoveBot 💖", layout="wide")

# ==============================
# LOAD MODEL
# ==============================
model, vectorizer, df = pickle.load(open("model.pkl", "rb"))

# ==============================
# API KEYS
# ==============================
try:
    openai.api_key = st.secrets["OPENAI_API_KEY"]
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    SERP_KEY = st.secrets["SERPAPI_KEY"]
except Exception as e:
    st.error(f"❌ API Error: {e}")
    st.stop()

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
        results = GoogleSearch({
            "q": query,
            "api_key": SERP_KEY,
            "num": 3
        }).get_dict()

        return " ".join(r.get("snippet", "") for r in results.get("organic_results", []))
    except:
        return ""

# ==============================
# EMOTION
# ==============================
def detect_emotion(text):
    text = text.lower()

    if any(w in text for w in ["sad", "hurt", "miss"]):
        return "sad"
    elif "love" in text:
        return "love"
    elif any(w in text for w in ["why", "how", "what"]):
        return "curious"
    return "normal"

# ==============================
# GEMINI BACKUP
# ==============================
def gemini_reply(user_input):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        res = model.generate_content(user_input)
        return res.text
    except Exception as e:
        print("Gemini error:", e)
        return None

# ==============================
# 🧠 MAIN BRAIN
# ==============================
def smart_reply(user_input):
    try:
        emotion = detect_emotion(user_input)
        history = st.session_state.messages[-6:]
        search_info = google_search(user_input)

        system_prompt = f"""
You are LoveBot 💖 (human-like AI)

Emotion: {emotion}

Rules:
- Talk like a real human
- Keep replies short & emotional
- Avoid repeating lines
- Refer to Rishav as "he"
"""

        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                *history,
                {"role": "user", "content": f"{user_input}\n{search_info}"}
            ],
            temperature=0.9
        )

        return response["choices"][0]["message"]["content"]

    except Exception as e:
        print("OpenAI failed:", e)

        # 🔥 fallback Gemini
        gemini_ans = gemini_reply(user_input)

        if gemini_ans:
            return gemini_ans

        return "Something went wrong 💔"

# ==============================
# UI
# ==============================
st.markdown("## 💖 LoveBot")
st.markdown("Hello my Love ❤️")

# ==============================
# CHAT DISPLAY
# ==============================
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"🟢 **You:** {msg['content']}")
    else:
        st.markdown(f"🤖 **LoveBot:** {msg['content']}")

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
    if any(w in user_input.lower() for w in ["photo", "pics"]):
        answer = "He wants to show you something special ❤️ Enter passkey 🔐"
        st.session_state.show_password = True

    else:
        matches = df[df["question"].str.lower().str.contains(user_input.lower())]

        if len(user_input) < 15 and not matches.empty:
            answer = matches.sample().iloc[0]["answer"]
        else:
            answer = smart_reply(user_input)

    with st.spinner("Thinking 💭"):
        time.sleep(0.8)

    answer += random.choice([" 💖", " ❤️", " 🥺", ""])

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
# BUTTONS
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