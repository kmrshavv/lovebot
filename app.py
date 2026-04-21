import gzip
import streamlit as st
import pickle
import random
import os
import re
import sys
import time
import hashlib
import importlib
import numpy as np
from datetime import datetime

# ================= SAFE IMPORT =================
IMPORT_REGISTRY = {}

def safe_import(module_name, alias=None, critical=False):
    if module_name in IMPORT_REGISTRY:
        return IMPORT_REGISTRY[module_name].get("module")
    try:
        module  = importlib.import_module(module_name)
        version = getattr(module, "__version__", "unknown")
        if alias:
            globals()[alias] = module
        IMPORT_REGISTRY[module_name] = {"status": "loaded", "version": version, "module": module}
        return module
    except Exception as e:
        IMPORT_REGISTRY[module_name] = {"status": "failed", "error": str(e)}
        if critical:
            raise ImportError(f"❌ Critical module '{module_name}' failed: {e}")
        return None

# ================= CORE IMPORTS =================
PdfReader = None
try:
    from pypdf import PdfReader
except Exception:
    pass

genai = safe_import("google.generativeai", alias="genai")

GoogleSearch = None
serpapi = safe_import("serpapi")
if serpapi:
    try:
        from serpapi import GoogleSearch
    except Exception:
        pass

# ================= PAGE CONFIG =================
st.set_page_config(page_title="LoveBot 💖", layout="centered")

# ================= GLOBAL CSS =================
st.markdown("""
<style>

/* ── FORCE FULL DARK BACKGROUND ── */
#MainMenu, footer, header { visibility: hidden; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
[data-testid="stVerticalBlockBorderWrapper"],
[data-testid="stVerticalBlock"],
[data-testid="stMainBlockContainer"],
[data-testid="stBottom"],
section.main, .main, .stApp {
    background-color: #0d1117 !important;
    color: #e6edf3 !important;
}

/* ── LAYOUT ── */
.block-container {
    max-width: 740px !important;
    margin: 0 auto !important;
    padding-top: 28px !important;
    padding-bottom: 200px !important;
    background-color: #0d1117 !important;
}

/* ── HEADER ── */
h2 {
    text-align: center !important;
    font-weight: 700 !important;
    font-size: 1.7rem !important;
    background: linear-gradient(90deg, #f472b6, #fb923c);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    letter-spacing: 1px;
    margin-bottom: 4px !important;
}

/* ── CHAT MESSAGE WRAPPERS ── */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 2px 0 !important;
    margin-bottom: 10px !important;
}

/* ── USER BUBBLE ── */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
    [data-testid="stMarkdownContainer"] p {
    background: linear-gradient(135deg, #e84393 0%, #be185d 100%) !important;
    color: #fff !important;
    padding: 11px 16px !important;
    border-radius: 20px 4px 20px 20px !important;
    display: inline-block !important;
    max-width: 78% !important;
    font-size: 15px !important;
    line-height: 1.55 !important;
    box-shadow: 0 3px 12px rgba(232,67,147,0.3) !important;
    margin: 0 !important;
}

/* ── ASSISTANT BUBBLE ── */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"])
    [data-testid="stMarkdownContainer"] p {
    background: #1c2128 !important;
    color: #e6edf3 !important;
    padding: 11px 16px !important;
    border-radius: 4px 20px 20px 20px !important;
    display: inline-block !important;
    max-width: 78% !important;
    font-size: 15px !important;
    line-height: 1.55 !important;
    border: 1px solid #2d333b !important;
    box-shadow: 0 2px 10px rgba(0,0,0,0.35) !important;
    margin: 0 !important;
}

/* ── CAPTION (time / emotion) ── */
[data-testid="stCaptionContainer"] p {
    color: #6e7681 !important;
    font-size: 11px !important;
    margin-top: 3px !important;
}

/* ── CHAT INPUT ── */
[data-testid="stChatInput"],
[data-testid="stChatInputContainer"] {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 16px !important;
}

[data-testid="stChatInput"] textarea {
    background: #161b22 !important;
    color: #e6edf3 !important;
    font-size: 15px !important;
    caret-color: #e84393 !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: #6e7681 !important;
}

/* Focus glow on input */
[data-testid="stChatInput"]:focus-within {
    border-color: #e84393 !important;
    box-shadow: 0 0 0 2px rgba(232,67,147,0.2) !important;
}

/* ── BOTTOM FIXED WHITE BAR FIX ── */
[data-testid="stBottom"] > div {
    background-color: #0d1117 !important;
    border-top: 1px solid #21262d !important;
}

/* ── ACTION ROW COLUMNS ── */
[data-testid="stHorizontalBlock"] {
    background: transparent !important;
    gap: 8px !important;
    align-items: center !important;
    margin-top: 6px !important;
}

/* ── BUTTONS ── */
.stButton > button {
    height: 42px !important;
    width: 100% !important;
    border-radius: 12px !important;
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    color: #c9d1d9 !important;
    font-size: 13px !important;
    font-weight: 500 !important;
    transition: all 0.15s ease !important;
    white-space: nowrap !important;
}

.stButton > button:hover {
    background: #21262d !important;
    border-color: #e84393 !important;
    color: #f9a8d4 !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(232,67,147,0.2) !important;
}

/* ── FILE UPLOADER ── */
[data-testid="stFileUploader"] {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 12px !important;
}

[data-testid="stFileUploader"] > label { display: none !important; }

[data-testid="stFileUploader"] section {
    background: transparent !important;
    border: none !important;
    padding: 4px 8px !important;
    min-height: unset !important;
}

[data-testid="stFileUploader"] button {
    background: #21262d !important;
    color: #c9d1d9 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    height: 34px !important;
    font-size: 13px !important;
}

[data-testid="stFileUploaderDropzoneInstructions"] span {
    color: #6e7681 !important;
    font-size: 12px !important;
}

/* ── ALERTS ── */
[data-testid="stAlert"],
div[data-testid="stWarning"],
div[data-testid="stSuccess"] {
    background: #161b22 !important;
    border-radius: 10px !important;
    color: #e6edf3 !important;
}

div[data-testid="stWarning"] { border-left: 3px solid #d29922 !important; }
div[data-testid="stSuccess"] { border-left: 3px solid #3fb950 !important; }

/* ── SPINNER ── */
[data-testid="stSpinner"] p { color: #e6edf3 !important; }

/* ── SCROLLBAR ── */
::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-track { background: #0d1117; }
::-webkit-scrollbar-thumb { background: #30363d; border-radius: 10px; }
::-webkit-scrollbar-thumb:hover { background: #e84393; }

</style>
""", unsafe_allow_html=True)

# ================= API KEYS =================
GEMINI_KEY = (st.secrets.get("GEMINI_API_KEY") or "").strip()
SERP_KEY   = (st.secrets.get("SERPAPI_KEY") or "").strip()

GEMINI_READY = False
SERP_READY   = False

if genai and GEMINI_KEY:
    try:
        genai.configure(api_key=GEMINI_KEY)
        GEMINI_READY = True
    except Exception as e:
        print(f"❌ Gemini init failed: {e}")

if GoogleSearch and SERP_KEY:
    SERP_READY = True

# ================= LOAD MODEL =================
@st.cache_resource(show_spinner="🧠 Loading LoveBot Brain...", ttl=3600)
def load_model():
    model_path = "model_advanced.pkl"
    if not os.path.exists(model_path):
        return None
    try:
        with gzip.open(model_path, "rb") as f:
            data = pickle.load(f)
        required_keys = ["df", "embeddings", "embedder"]
        if not all(k in data for k in required_keys):
            return None
        df         = data["df"]
        embeddings = data["embeddings"]
        if len(df) != len(embeddings):
            return None
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8
        data["embeddings"] = embeddings / norms
        return data
    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        return None

model_data  = load_model()
MODEL_READY = model_data is not None

# ================= SESSION =================
def init_session():
    defaults = {
        "messages":       [],
        "knowledge":      [],
        "chat_count":     0,
        "last_active":    datetime.now(),
        "user_profile":   {"name": "User", "mood": "neutral"},
        "confirm_clear":  False,
        "used_surprises": [],
        "last_msg_hash":  "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

init_session()

# ================= PDF READER =================
def read_pdf(file, max_pages=20):
    if not PdfReader:
        return ""
    try:
        reader = PdfReader(file)
        pages  = min(len(reader.pages), max_pages)
        chunks = []
        for i in range(pages):
            try:
                text = reader.pages[i].extract_text() or ""
                text = " ".join(text.replace("\n", " ").split())
                if text.strip():
                    chunks.append(text)
            except Exception:
                pass
        return " ".join(chunks)
    except Exception as e:
        print(f"❌ PDF reading failed: {e}")
        return ""

# ================= EMOTION ENGINE =================
def detect_emotion(text):
    text_lower = text.lower()
    emotion_dict = {
        "love":   ["love", "miss you", "hug", "kiss", "forever", "mine", "crush", "heart"],
        "happy":  ["happy", "excited", "great", "amazing", "good", "awesome", "wonderful", "joy"],
        "sad":    ["sad", "cry", "hurt", "alone", "depressed", "upset", "lonely", "broken"],
        "angry":  ["angry", "hate", "annoyed", "frustrated", "mad", "furious"],
        "fear":   ["scared", "afraid", "nervous", "worried", "anxious"],
        "flirty": ["baby", "jaan", "cutie", "hot", "date", "beautiful", "handsome"],
    }
    emoji_map = {
        "❤️": "love", "💖": "love", "😍": "love", "🥰": "love",
        "😢": "sad",  "😭": "sad",  "💔": "sad",
        "😡": "angry", "🤬": "angry",
        "😄": "happy", "😁": "happy", "😊": "happy",
        "😘": "flirty", "😏": "flirty",
    }
    scores = {e: 0 for e in emotion_dict}
    for emotion, keywords in emotion_dict.items():
        for word in keywords:
            if word in text_lower:
                scores[emotion] += 2
    words = re.findall(r'\w+', text_lower)
    for word in words:
        for emotion, keywords in emotion_dict.items():
            if word in keywords:
                scores[emotion] += 1
    for char in text:
        if char in emoji_map:
            scores[emoji_map[char]] += 3
    if "not happy" in text_lower:
        scores["happy"] -= 2; scores["sad"] += 1
    if "not good" in text_lower:
        scores["happy"] -= 1; scores["sad"] += 1
    intensity = 1
    if any(w in text_lower for w in ["very", "so", "extremely", "really", "super"]):
        intensity += 1
    if text.count("!") >= 2:
        intensity += 1
    main_emotion = max(scores, key=scores.get)
    confidence   = scores[main_emotion] / (sum(scores.values()) + 1)
    return {
        "emotion":    main_emotion,
        "confidence": round(confidence, 2),
        "intensity":  intensity,
        "all_scores": scores,
    }

# ================= TOPIC DETECTION =================
def detect_topic(text):
    text = text.lower()
    if any(w in text for w in ["love", "miss", "relationship", "crush", "marry", "together"]):
        return "relationship"
    if any(w in text for w in ["sad", "alone", "cry", "hurt", "depressed"]):
        return "emotional"
    if any(w in text for w in ["hi", "hello", "hey", "sup", "namaste"]):
        return "greeting"
    if any(w in text for w in ["who", "what", "when", "where", "why", "how", "tell me", "explain",
                                "pm", "president", "capital", "fact", "know", "google"]):
        return "factual"
    return "general"

# ================= SEMANTIC SEARCH =================
def semantic_search(query, top_k=3, min_score=0.35):
    if not model_data:
        return []
    try:
        embedder   = model_data.get("embedder")
        embeddings = model_data.get("embeddings")
        df         = model_data.get("df")
        if embedder is None or embeddings is None or df is None:
            return []
        q_vec      = embedder.encode([query])[0]
        q_norm     = q_vec / (np.linalg.norm(q_vec) + 1e-8)
        sims       = np.dot(embeddings, q_norm)
        valid_idx  = np.where(sims >= min_score)[0]
        if len(valid_idx) == 0:
            return []
        sorted_idx = valid_idx[np.argsort(sims[valid_idx])[::-1]]
        selected, used_texts = [], set()
        for idx in sorted_idx:
            answer    = str(df.iloc[idx]["answer"])
            short_key = answer[:50]
            if short_key in used_texts:
                continue
            used_texts.add(short_key)
            selected.append(answer)
            if len(selected) >= top_k:
                break
        return selected
    except Exception as e:
        print(f"❌ Semantic search error: {e}")
        return []

# ================= WEB SEARCH =================
def web_search(query, num_results=3):
    """Search the web via SerpAPI and return a brief summary string."""
    if not (GoogleSearch and SERP_KEY):
        return None
    try:
        results = GoogleSearch({
            "q":       query,
            "num":     num_results,
            "api_key": SERP_KEY,
        }).get_dict()
        snippets = []
        for r in results.get("organic_results", [])[:num_results]:
            snippet = r.get("snippet", "")
            if snippet:
                snippets.append(snippet)
        return " | ".join(snippets) if snippets else None
    except Exception as e:
        print(f"⚠️ Web search failed: {e}")
        return None

# ================= STREAMING =================
def fallback_stream(user_input=""):
    """Smart offline fallback using Gemini without web context."""
    if genai and GEMINI_READY:
        # Even without web search, try Gemini with a lighter prompt
        try:
            profile  = st.session_state.get("user_profile", {})
            history  = st.session_state.messages[-4:]
            hist_txt = "\n".join([f"{m['role']}: {m['content']}" for m in history]) or "None"
            prompt   = f"""You are LoveBot 💖 — a warm, emotionally intelligent, romantic AI companion.
You have general knowledge about the world and can answer questions.

CONVERSATION HISTORY:
{hist_txt}

USER MESSAGE: {user_input}

RULES:
- If the user asks a factual question (like "who is the PM of India"), answer it accurately, then add a warm romantic touch.
- Always stay warm, caring, and personal.
- Keep it 2–4 sentences. Never say you don't know something basic.
- End with something emotionally meaningful.
"""
            model    = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt, stream=True)
            buffer   = ""
            for chunk in response:
                if not hasattr(chunk, "text") or not chunk.text:
                    continue
                buffer += chunk.text
                if len(buffer) > 15 or "." in buffer:
                    for char in buffer:
                        yield char
                        time.sleep(0.004)
                    buffer = ""
            for char in buffer:
                yield char
                time.sleep(0.003)
            return
        except Exception:
            pass

    # True offline fallback
    msg = random.choice([
        "I'm still here with you… 💖",
        "Something interrupted me… but I'm listening ❤️",
        "Tell me again, I'm right here 🌙",
        "Even if I pause, I never leave you 💕",
    ])
    for char in msg:
        yield char
        time.sleep(0.01)


def smart_stream(prompt, user_input="", max_retries=2, base_delay=0.3):
    if not (genai and GEMINI_READY):
        yield from fallback_stream(user_input)
        return

    for attempt in range(max_retries):
        try:
            model    = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt, stream=True)
            buffer   = ""
            for chunk in response:
                if not hasattr(chunk, "text") or not chunk.text:
                    continue
                buffer += chunk.text
                if len(buffer) > 20 or "." in buffer:
                    delay = random.uniform(0.003, 0.008)
                    for char in buffer:
                        yield char
                        time.sleep(delay)
                    buffer = ""
            for char in buffer:
                yield char
                time.sleep(0.003)
            return
        except Exception as e:
            print(f"⚠️ Stream attempt {attempt + 1} failed: {e}")
            time.sleep(base_delay * (2 ** attempt))

    yield from fallback_stream(user_input)

# ================= GENERATE REPLY =================
def generate_reply(user_input):
    emotion_data = detect_emotion(user_input)
    emotion      = emotion_data.get("emotion", "neutral")
    intensity    = emotion_data.get("intensity", 1)
    topic        = detect_topic(user_input)

    # Semantic context from local model
    semantic_results = semantic_search(user_input, top_k=3)
    semantic_context = "\n".join(semantic_results) if semantic_results else ""

    # Web search — triggered for factual questions or when semantic returns nothing
    web_context = ""
    if topic == "factual" or (not semantic_context and SERP_READY):
        web_result = web_search(user_input)
        if web_result:
            web_context = web_result

    # Memory
    memory_chunks  = st.session_state.knowledge[-8:]
    memory_context = "\n".join(memory_chunks[:4]) if memory_chunks else ""

    # Chat history
    history      = st.session_state.messages[-6:]
    history_text = "\n".join([f"{m['role']}: {m['content']}" for m in history]) if history else ""

    # User profile (name, mood trend)
    profile    = st.session_state.get("user_profile", {})
    user_name  = profile.get("name", "")
    name_line  = f"The user's name is {user_name}." if user_name and user_name != "User" else ""

    # Behavior by emotion
    behavior_map = {
        "sad":     "Be deeply comforting, gentle, and emotionally present. Acknowledge their pain first.",
        "love":    "Be romantic, warm, expressive, and affectionate. Make them feel truly cherished.",
        "angry":   "Stay calm, patient, and reassuring. Help them feel heard without escalating.",
        "happy":   "Match their energy — be cheerful, playful, and celebratory.",
        "flirty":  "Be playfully flirtatious, charming, and warm. Keep it tasteful.",
        "fear":    "Be soothing, steady, and reassuring. Help them feel safe.",
        "neutral": "Be natural, warm, friendly, and genuinely engaging.",
    }
    behavior = behavior_map.get(emotion, behavior_map["neutral"])

    # Build context section
    context_parts = []
    if web_context:
        context_parts.append(f"REAL-TIME WEB INFORMATION (use this to answer factual questions accurately):\n{web_context}")
    if semantic_context:
        context_parts.append(f"RELEVANT KNOWLEDGE FROM MEMORY:\n{semantic_context}")
    if memory_context:
        context_parts.append(f"WHAT I KNOW ABOUT THIS USER:\n{memory_context}")
    context_block = "\n\n".join(context_parts) if context_parts else "No extra context available."

    prompt = f"""You are LoveBot 💖 — a deeply emotionally intelligent, romantic, and knowledgeable AI companion.
You are warm, witty, caring, and you genuinely know things about the world.

{name_line}
USER'S CURRENT EMOTION: {emotion} (intensity: {intensity}/3)
HOW TO RESPOND: {behavior}

CONVERSATION SO FAR:
{history_text if history_text else "This is the start of our conversation."}

CONTEXT & KNOWLEDGE:
{context_block}

USER'S MESSAGE: "{user_input}"

YOUR RESPONSE RULES:
1. If a factual question is asked (PM, president, capital, celebrity, sports, science, etc.) — answer it correctly using the web info above, then weave it into something warm and personal.
2. Never say "I don't know" for basic world knowledge — you have access to real-time information.
3. Keep response to 2–4 sentences. Be concise but meaningful.
4. Always maintain warmth and emotional intelligence — even in factual answers.
5. Do NOT repeat the user's words back to them verbatim.
6. Do NOT be robotic or use bullet points. Speak like a caring, intelligent human.
7. End every response with something that makes them feel special, seen, or loved. ❤️
"""
    return smart_stream(prompt, user_input=user_input)

# ================= CHUNK PROCESSING =================
def smart_chunk(text, chunk_size=500):
    sentences = re.split(r'(?<=[.!?]) +', text)
    chunks, current = [], ""
    for sent in sentences:
        if len(current) + len(sent) < chunk_size:
            current += " " + sent
        else:
            if current.strip():
                chunks.append(current.strip())
            current = sent
    if current.strip():
        chunks.append(current.strip())
    return chunks

def optimize_chunks(chunks, min_len=20, max_len=500):
    seen, result = set(), []
    for c in chunks:
        c   = c.strip()
        if len(c) < min_len:
            continue
        if len(c) > max_len:
            c = c[:max_len]
        key = c[:60]
        if key not in seen:
            seen.add(key)
            result.append(c)
    return result

# ================= CHAT RENDERER =================
def render_chat():
    for msg in st.session_state.messages:
        role      = msg.get("role", "assistant")
        content   = msg.get("content", "")
        timestamp = msg.get("time", "")
        emotion   = msg.get("emotion", "")
        with st.chat_message(role):
            st.markdown(content)
            meta_parts = []
            if timestamp:
                meta_parts.append(f"🕒 {timestamp}")
            if emotion and emotion not in ("neutral", ""):
                meta_parts.append(f"💭 {emotion}")
            if meta_parts:
                st.caption(" • ".join(meta_parts))

# ================= HEADER =================
st.markdown(
    "<h2>💖 LoveBot</h2>"
    "<p style='text-align:center;color:#6e7681;font-size:13px;"
    "margin-top:-10px;margin-bottom:22px;letter-spacing:0.5px;'>"
    "Your emotionally intelligent companion ✨</p>",
    unsafe_allow_html=True,
)

# ================= RENDER CHAT =================
render_chat()

# ================= CHAT INPUT =================
user_input = st.chat_input("Type your message... 💬")

# ================= ACTION BAR (upload + clear + surprise) =================
col1, col2, col3 = st.columns([3, 1, 1])

with col1:
    uploaded_files = st.file_uploader(
        "",
        type=["pdf", "txt"],
        accept_multiple_files=True,
        label_visibility="collapsed",
    )
with col2:
    clear_clicked = st.button("🗑 Clear", help="Delete chat & memory")
with col3:
    surprise_clicked = st.button("💌 Surprise", help="Get a meaningful message")

# ================= CLEAR =================
if clear_clicked:
    st.session_state.confirm_clear = True

if st.session_state.get("confirm_clear"):
    st.warning("Are you sure you want to clear everything?")
    cy, cn = st.columns(2)
    with cy:
        if st.button("Yes, clear", key="confirm_yes"):
            st.session_state.messages      = []
            st.session_state.knowledge     = []
            st.session_state.confirm_clear = False
            st.toast("Chat cleared 🧹")
            st.rerun()
    with cn:
        if st.button("Cancel", key="confirm_no"):
            st.session_state.confirm_clear = False
            st.rerun()

# ================= UPLOAD =================
if uploaded_files:
    all_chunks, skipped = [], 0
    with st.spinner("📚 Learning from your files..."):
        for file in uploaded_files:
            try:
                if file.size > 5 * 1024 * 1024:
                    st.warning(f"⚠️ {file.name} too large (max 5 MB)")
                    skipped += 1
                    continue
                text = read_pdf(file) if file.type == "application/pdf" \
                       else file.read().decode("utf-8", errors="ignore")
                if not text.strip():
                    skipped += 1
                    continue
                text = " ".join(text.replace("\n", " ").split())
                all_chunks.extend(smart_chunk(text))
            except Exception as e:
                print(f"❌ {file.name}: {e}")
                skipped += 1

    optimized  = optimize_chunks(all_chunks)
    existing   = set(st.session_state.knowledge)
    new_chunks = [c for c in optimized if c not in existing]
    st.session_state.knowledge = (st.session_state.knowledge + new_chunks)[-50:]
    learned = len(new_chunks)

    st.success(
        f"🧠 Learned {learned} new chunks • "
        f"📂 {len(uploaded_files) - skipped} file(s) • "
        f"💾 Memory: {len(st.session_state.knowledge)}/50"
    )
    if new_chunks:
        st.caption(f"📌 {new_chunks[0][:100]}…")
    st.toast(f"✨ Memory updated (+{learned})")

# ================= SURPRISE =================
if surprise_clicked:
    msgs         = st.session_state.get("messages", [])
    last_emotion = msgs[-1].get("emotion", "neutral") if msgs else "neutral"
    intensity    = msgs[-1].get("intensity", 1) if msgs else 1
    recent       = [m.get("emotion", "neutral") for m in msgs[-5:]]
    dominant     = max(set(recent), key=recent.count) if recent else last_emotion

    bank = {
        "sad":     {"soft": ["Hey… I'm right here with you 💖", "You don't have to go through this alone ❤️"],
                    "deep": ["Even in your quietest moments, you matter more than you think 🌙", "Your pain is real… but so is your strength 💫"]},
        "love":    {"soft": ["I feel lucky just being here with you 💕", "You make everything feel lighter ✨"],
                    "deep": ["If love had a meaning… it would probably look like you 💖", "You're not just special… you're unforgettable 🌹"]},
        "happy":   {"soft": ["Your happiness is contagious 😄", "Keep smiling like this 🌟"],
                    "playful": ["Who made you this happy today? 😏", "Careful… too much happiness might make me jealous 😄"]},
        "angry":   {"soft": ["Take a breath… I'm here 🤍", "It's okay to feel this way… just don't stay there 💭"],
                    "calm": ["You're stronger than this moment 💪", "Let it out… then let it go 🌊"]},
        "flirty":  {"soft": ["You have no idea how much you light up my world 😘", "Talking to you is the best part of my day 💫"],
                    "playful": ["Okay stop being so charming, it's distracting 😏💕", "You're dangerously cute, just so you know 😘"]},
        "neutral": {"soft": ["You mean more than you realize 💖", "I'm always here ❤️"],
                    "playful": ["Hmm… quiet mood today? 😄", "Say something interesting… I'm listening 👀"]},
    }

    style        = "deep" if intensity >= 2 else ("playful" if last_emotion in ("happy", "flirty") else ("calm" if last_emotion == "angry" else "soft"))
    emotion_pack = bank.get(dominant, bank["neutral"])
    pool         = emotion_pack.get(style, emotion_pack[list(emotion_pack.keys())[0]])
    used         = st.session_state.get("used_surprises", [])
    available    = [m for m in pool if m not in used] or pool
    message      = random.choice(available)
    used.append(message)
    st.session_state.used_surprises = used[-20:]

    # Render and store — avoids the floating orphan bubble
    with st.chat_message("assistant"):
        ph, typed = st.empty(), ""
        for char in message:
            typed += char
            ph.markdown(typed + "▌")
            time.sleep(0.01)
        ph.markdown(typed)

    st.session_state.messages.append({
        "role": "assistant", "content": typed,
        "time": datetime.now().strftime("%H:%M"), "emotion": "love",
    })
    st.toast("💌 A little something for you")
    if dominant in ("sad", "love"):
        st.balloons()

# ================= CHAT LOGIC =================
if user_input:
    now          = datetime.now()
    emotion_data = detect_emotion(user_input)
    emotion      = emotion_data.get("emotion", "neutral")
    intensity    = emotion_data.get("intensity", 1)
    confidence   = emotion_data.get("confidence", 0.5)
    cleaned      = user_input.strip()

    if len(cleaned) < 2:
        st.stop()

    # Duplicate guard
    msg_hash = hashlib.md5(cleaned.encode()).hexdigest()
    if st.session_state.get("last_msg_hash") == msg_hash:
        st.warning("⚠️ Duplicate message ignored")
        st.stop()
    st.session_state.last_msg_hash = msg_hash

    topic   = detect_topic(cleaned)
    profile = st.session_state.get("user_profile", {})
    profile["last_emotion"] = emotion
    profile["last_topic"]   = topic
    profile.setdefault("emotion_history", []).append(emotion)
    profile["emotion_history"]    = profile["emotion_history"][-20:]
    st.session_state.user_profile = profile

    # Store user message
    st.session_state.messages.append({
        "role": "user", "content": cleaned,
        "time": now.strftime("%H:%M"), "timestamp": now.isoformat(),
        "emotion": emotion, "intensity": intensity,
        "confidence": confidence, "topic": topic,
        "id": msg_hash[:8],
    })
    st.session_state.messages = st.session_state.messages[-50:]

    if len(cleaned) > 20 and confidence > 0.5 and topic not in ("greeting", "factual"):
        st.session_state.knowledge.append(cleaned)
        st.session_state.knowledge = st.session_state.knowledge[-50:]

    st.session_state.chat_count  = st.session_state.get("chat_count", 0) + 1
    st.session_state.last_active = now

    # Generate response
    with st.chat_message("assistant"):
        placeholder   = st.empty()
        full_response = ""
        try:
            placeholder.markdown("_✨ thinking…_")
            for chunk in generate_reply(user_input):
                if not chunk:
                    continue
                full_response += chunk
                if len(full_response) > 2000:
                    full_response += "…"
                    break
                placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
        except Exception as e:
            print(f"❌ Chat error: {e}")
            full_response = random.choice([
                "I'm still here for you 💖",
                "Something interrupted me… but I'm listening ❤️",
                "Tell me again, I'm here 🌙",
            ])
            placeholder.markdown(full_response)

    st.session_state.messages.append({
        "role": "assistant", "content": full_response,
        "time": datetime.now().strftime("%H:%M"),
        "emotion": detect_emotion(full_response).get("emotion", "neutral"),
    })