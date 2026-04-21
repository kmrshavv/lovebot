import streamlit as st
import pickle, random, time
import json

from openai import OpenAI
import google.generativeai as genai
from serpapi import GoogleSearch

from pypdf import PdfReader

# ==============================
# CONFIG
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
    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    SERP_KEY = st.secrets["SERPAPI_KEY"]
except Exception as e:
    st.error(f"❌ API Error: {e}")
    st.stop()

# ==============================
# SESSION STATE
# ==============================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "knowledge" not in st.session_state:
    st.session_state.knowledge = ""

if "show_password" not in st.session_state:
    st.session_state.show_password = False

# ==============================
# GOOGLE SEARCH
# ==============================
def google_search(q):
    try:
        res = GoogleSearch({
            "q": q,
            "api_key": SERP_KEY,
            "num": 3
        }).get_dict()

        return " ".join(r.get("snippet","") for r in res.get("organic_results", []))
    except:
        return ""

# ==============================
# FILE LEARNING
# ==============================
def read_pdf(file):
    text = ""
    pdf = PdfReader(file)
    for page in pdf.pages:
        text += page.extract_text() or ""
    return text

# ==============================
# GEMINI BACKUP
# ==============================
def gemini_reply(prompt):
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        res = model.generate_content(prompt)
        return res.text
    except:
        return None

# ==============================
# MAIN AI
# ==============================
def smart_reply(user_input):
    try:
        history = st.session_state.messages[-6:]
        search = google_search(user_input)
        knowledge = st.session_state.knowledge[:3000]

        system = f"""
You are LoveBot 💖

Talk like a real human:
- short replies
- emotional
- no repetition

Use knowledge if helpful:
{knowledge}
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system},
                *history,
                {"role": "user", "content": f"{user_input}\n{search}"}
            ],
            temperature=0.8
        )

        return response.choices[0].message.content

    except Exception as e:
        st.warning("⚠️ OpenAI failed, switching to backup")
        gem = gemini_reply(user_input)
        if gem:
            return gem
        return "I'm thinking… something feels off 💭"

# ==============================
# UI
# ==============================
st.title("💖 LoveBot")
st.caption("Hello my Love ❤️")

# ==============================
# FILE UPLOAD (LEARNING)
# ==============================
st.subheader("📂 Teach LoveBot")

uploaded = st.file_uploader("Upload PDF / Text", type=["pdf","txt"])

if uploaded:
    if uploaded.type == "application/pdf":
        text = read_pdf(uploaded)
    else:
        text = uploaded.read().decode("utf-8")

    st.session_state.knowledge += "\n" + text
    st.success("Learned from your file 💡")

# ==============================
# CHAT DISPLAY
# ==============================
for msg in st.session_state.messages:
    if msg["role"] == "user":
        st.markdown(f"🟢 {msg['content']}")
    else:
        st.markdown(f"🤖 {msg['content']}")

# ==============================
# INPUT
# ==============================
user_input = st.chat_input("Type your message 💬")

# ==============================
# MAIN LOGIC
# ==============================
if user_input:

    st.session_state.messages.append({"role":"user","content":user_input})

    # Photo trigger
    if any(w in user_input.lower() for w in ["photo","memory","pics"]):
        answer = "I have something special ❤️ Enter passkey 🔐"
        st.session_state.show_password = True

    else:
        matches = df[df["question"].str.lower().str.contains(user_input.lower())]

        if len(user_input) < 12 and not matches.empty:
            answer = matches.sample().iloc[0]["answer"]
        else:
            answer = smart_reply(user_input)

    with st.spinner("Thinking 💭"):
        time.sleep(0.6)

    answer += random.choice([" ❤️"," 💖"," 🥺",""])

    st.session_state.messages.append({"role":"assistant","content":answer})

    st.rerun()

# ==============================
# 🔐 PASSWORD PHOTO VAULT
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

with col2:
    if st.button("💌 Surprise"):
        st.success(random.choice([
            "You are everything 💖",
            "He loves you forever ❤️",
            "You complete him 💞"
        ]))