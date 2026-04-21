import streamlit as st
import pickle, random, time
from serpapi import GoogleSearch
import google.generativeai as genai
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
genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
SERP_KEY = st.secrets["SERPAPI_KEY"]

# ==============================
# SESSION
# ==============================
if "messages" not in st.session_state:
    st.session_state.messages = []

if "knowledge" not in st.session_state:
    st.session_state.knowledge = []

if "show_password" not in st.session_state:
    st.session_state.show_password = False

# ==============================
# GOOGLE SEARCH
# ==============================
def google_search(query):
    try:
        res = GoogleSearch({
            "q": query,
            "api_key": SERP_KEY,
            "num": 3
        }).get_dict()

        return [r.get("snippet","") for r in res.get("organic_results", [])]
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
# KNOWLEDGE RETRIEVAL
# ==============================
def retrieve_knowledge(query):
    relevant = []
    for chunk in st.session_state.knowledge:
        if any(word in chunk.lower() for word in query.lower().split()):
            relevant.append(chunk)
    return relevant[:5]

# ==============================
# 🧠 SMART AI
# ==============================
def smart_reply(user_input):
    try:
        model_ai = genai.GenerativeModel("gemini-1.5-flash")

        history = st.session_state.messages[-5:]
        search_results = google_search(user_input)
        local_knowledge = retrieve_knowledge(user_input)

        prompt = f"""
You are LoveBot 💖

Behave like a real human:
- emotional
- short replies
- intelligent
- no repetition

Think before answering.

Conversation:
{history}

Internet:
{search_results}

Knowledge:
{local_knowledge}

User: {user_input}
"""

        response = model_ai.generate_content(prompt)
        return response.text

    except Exception as e:
        print(e)
        return "I'm thinking deeply… something interrupted me 💭"

# ==============================
# UI
# ==============================
st.title("💖 LoveBot Pro")
st.caption("Smarter. Learns. Thinks. Remembers. 🧠")

# ==============================
# 📂 FILE UPLOAD
# ==============================
st.subheader("📂 Teach LoveBot")

files = st.file_uploader(
    "Upload PDF / Text",
    type=["pdf","txt"],
    accept_multiple_files=True
)

if files:
    for file in files:
        if file.type == "application/pdf":
            text = read_pdf(file)
        else:
            text = file.read().decode("utf-8")

        chunks = [text[i:i+500] for i in range(0, len(text), 500)]
        st.session_state.knowledge.extend(chunks)

    st.success("Learned from files 💡")

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
user_input = st.chat_input("Ask anything… 💬")

# ==============================
# MAIN LOGIC
# ==============================
if user_input:
    st.session_state.messages.append({"role":"user","content":user_input})

    # PHOTO TRIGGER
    if any(w in user_input.lower() for w in ["photo","memory","pics"]):
        answer = "I have something special ❤️ Enter passkey 🔐"
        st.session_state.show_password = True
    else:
        matches = df[df["question"].str.lower().str.contains(user_input.lower())]

        if len(user_input) < 10 and not matches.empty:
            answer = matches.sample().iloc[0]["answer"]
        else:
            answer = smart_reply(user_input)

    with st.spinner("Thinking 🧠💭"):
        time.sleep(0.7)

    answer += random.choice([" ❤️"," 💖"," 🧠",""])

    st.session_state.messages.append({"role":"assistant","content":answer})
    st.rerun()

# ==============================
# 🔐 PHOTO VAULT
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
    if st.button("🗑 Clear"):
        st.session_state.messages = []
        st.session_state.knowledge = []

with col2:
    if st.button("💌 Surprise"):
        st.success(random.choice([
            "You are everything 💖",
            "He loves you forever ❤️",
            "You complete him 💞"
        ]))