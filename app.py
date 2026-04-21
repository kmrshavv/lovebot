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
        module = importlib.import_module(module_name)
        version = getattr(module, "__version__", "unknown")
        if alias:
            globals()[alias] = module
        IMPORT_REGISTRY[module_name] = {"status": "loaded", "version": version, "module": module}
        print(f"✅ {module_name} loaded (v{version})")
        return module
    except Exception as e:
        IMPORT_REGISTRY[module_name] = {"status": "failed", "error": str(e)}
        if critical:
            raise ImportError(f"❌ Critical module '{module_name}' failed: {e}")
        print(f"⚠️ {module_name} not available: {e}")
        return None

def is_module_available(name):
    return IMPORT_REGISTRY.get(name, {}).get("status") == "loaded"

# ================= CORE IMPORTS =================
PdfReader = None
try:
    from pypdf import PdfReader
except Exception as e:
    print(f"⚠️ PDF support disabled: {e}")

genai = safe_import("google.generativeai", alias="genai")

GoogleSearch = None
serpapi = safe_import("serpapi")
if serpapi:
    try:
        from serpapi import GoogleSearch
    except Exception as e:
        print(f"⚠️ GoogleSearch import failed: {e}")

# ================= CONFIG =================
st.set_page_config(page_title="LoveBot 💖", layout="centered")

st.markdown("""
<style>

/* ===== FORCE DARK EVERYWHERE ===== */
#MainMenu, footer, header { visibility: hidden; }

html, body,
[data-testid="stAppViewContainer"],
[data-testid="stAppViewBlockContainer"],
[data-testid="stVerticalBlock"],
[data-testid="stMainBlockContainer"],
section.main,
.main {
    background-color: #0d1117 !important;
    color: #e6edf3 !important;
}

/* ===== PAGE LAYOUT ===== */
.block-container {
    max-width: 760px !important;
    margin: 0 auto !important;
    padding-top: 24px !important;
    padding-bottom: 180px !important;
    background-color: #0d1117 !important;
}

/* ===== HEADER ===== */
h2 {
    text-align: center;
    font-weight: 700;
    font-size: 1.6rem;
    color: #f0a0b0 !important;
    letter-spacing: 1px;
    margin-bottom: 20px;
}

/* ===== CHAT MESSAGES — SHARED ===== */
[data-testid="stChatMessage"] {
    background: transparent !important;
    border: none !important;
    box-shadow: none !important;
    padding: 4px 0 !important;
    margin-bottom: 8px !important;
}

/* ===== USER BUBBLE ===== */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]) {
    flex-direction: row-reverse !important;
}

[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"])
    [data-testid="stMarkdownContainer"] > p {
    background: linear-gradient(135deg, #e84393, #c0392b) !important;
    color: #ffffff !important;
    padding: 10px 16px !important;
    border-radius: 18px 4px 18px 18px !important;
    display: inline-block !important;
    max-width: 75% !important;
    font-size: 15px !important;
    line-height: 1.5 !important;
    box-shadow: 0 2px 8px rgba(232,67,147,0.25) !important;
}

/* ===== ASSISTANT BUBBLE ===== */
[data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarAssistant"])
    [data-testid="stMarkdownContainer"] > p {
    background: #1c2128 !important;
    color: #e6edf3 !important;
    padding: 10px 16px !important;
    border-radius: 4px 18px 18px 18px !important;
    display: inline-block !important;
    max-width: 75% !important;
    font-size: 15px !important;
    line-height: 1.5 !important;
    border: 1px solid #30363d !important;
    box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
}

/* ===== CAPTION (timestamp / emotion) ===== */
[data-testid="stCaptionContainer"] p,
.stCaption {
    color: #6e7681 !important;
    font-size: 11px !important;
    margin-top: 2px !important;
}

/* ===== CHAT INPUT BAR ===== */
[data-testid="stChatInput"] {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 16px !important;
}

[data-testid="stChatInput"] textarea {
    background: #161b22 !important;
    color: #e6edf3 !important;
    border: none !important;
    font-size: 15px !important;
}

[data-testid="stChatInput"] textarea::placeholder {
    color: #6e7681 !important;
}

/* ===== BOTTOM ACTION BAR (upload + buttons) ===== */
[data-testid="stHorizontalBlock"] {
    background: #0d1117 !important;
    align-items: center !important;
    gap: 8px !important;
}

/* ===== BUTTONS ===== */
.stButton > button {
    height: 42px !important;
    border-radius: 10px !important;
    background: #21262d !important;
    border: 1px solid #30363d !important;
    color: #e6edf3 !important;
    font-size: 14px !important;
    font-weight: 500 !important;
    transition: all 0.15s ease !important;
    width: 100% !important;
}

.stButton > button:hover {
    background: #30363d !important;
    border-color: #e84393 !important;
    color: #f9a8d4 !important;
    transform: translateY(-1px) !important;
}

/* ===== FILE UPLOADER ===== */
[data-testid="stFileUploader"] {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 10px !important;
    padding: 4px 8px !important;
}

[data-testid="stFileUploader"] > label { display: none !important; }

[data-testid="stFileUploader"] section {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    min-height: unset !important;
}

[data-testid="stFileUploader"] button {
    background: #21262d !important;
    color: #e6edf3 !important;
    border: 1px solid #30363d !important;
    border-radius: 8px !important;
    font-size: 13px !important;
    height: 36px !important;
}

[data-testid="stFileUploaderDropzoneInstructions"] {
    color: #6e7681 !important;
    font-size: 12px !important;
}

/* ===== WARNING / SUCCESS / INFO BOXES ===== */
[data-testid="stAlert"] {
    background: #161b22 !important;
    border-color: #30363d !important;
    color: #e6edf3 !important;
    border-radius: 10px !important;
}

/* ===== CONFIRMATION WARNING ===== */
div[data-testid="stWarning"] {
    background: #1c1a0f !important;
    border-left: 3px solid #d29922 !important;
    color: #e3b341 !important;
    border-radius: 8px !important;
}

/* ===== SCROLLBAR ===== */
::-webkit-scrollbar { width: 5px; }
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
        print("🧠 Gemini AI ready")
    except Exception as e:
        print(f"❌ Gemini init failed: {e}")

if GoogleSearch and SERP_KEY:
    SERP_READY = True
    print("🌐 Web search enabled")

# ================= LOAD MODEL =================
# FIX: train.py saves with gzip.open — must load with gzip.open here too.
# The old plain open() would crash with a pickle decode error at runtime.
@st.cache_resource(show_spinner="🧠 Loading LoveBot Brain...", ttl=3600)
def load_model():
    model_path = "model_advanced.pkl"
    if not os.path.exists(model_path):
        print("⚠️ Model file not found — running without semantic search")
        return None
    try:
        with gzip.open(model_path, "rb") as f:
            data = pickle.load(f)

        required_keys = ["df", "embeddings", "embedder"]
        if not all(k in data for k in required_keys):
            print("❌ Model structure invalid")
            return None

        df         = data["df"]
        embeddings = data["embeddings"]

        if len(df) != len(embeddings):
            print("❌ Mismatch: df and embeddings size")
            return None

        # Normalize embeddings once at load time
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8
        data["embeddings"] = embeddings / norms

        print(f"✅ Model loaded — {len(df)} rows, dim {embeddings.shape[1]}")
        return data

    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        return None

model_data  = load_model()
MODEL_READY = model_data is not None

# ================= SESSION =================
def init_session():
    defaults = {
        "messages":      [],
        "knowledge":     [],
        "chat_count":    0,
        "last_active":   datetime.now(),
        "user_profile":  {"name": "User", "mood": "neutral"},
        "confirm_clear": False,
        "used_surprises": [],
        "last_msg_hash": "",
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
            except Exception as e:
                print(f"⚠️ Page {i} read error: {e}")
        return " ".join(chunks)
    except Exception as e:
        print(f"❌ PDF reading failed: {e}")
        return ""

# ================= EMOTION ENGINE =================
def detect_emotion(text):
    text_lower = text.lower()

    emotion_dict = {
        "love":   ["love", "miss you", "hug", "kiss", "forever", "mine"],
        "happy":  ["happy", "excited", "great", "amazing", "good", "awesome"],
        "sad":    ["sad", "cry", "hurt", "alone", "depressed", "upset"],
        "angry":  ["angry", "hate", "annoyed", "frustrated", "mad"],
        "fear":   ["scared", "afraid", "nervous", "worried"],
        "flirty": ["baby", "jaan", "cutie", "hot", "date"],
    }

    emoji_map = {
        "❤️": "love", "💖": "love", "😍": "love",
        "😢": "sad",  "😭": "sad",
        "😡": "angry",
        "😄": "happy", "😁": "happy",
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
        scores["happy"] -= 2
        scores["sad"]   += 1
    if "not good" in text_lower:
        scores["happy"] -= 1
        scores["sad"]   += 1

    intensity = 1
    if any(w in text_lower for w in ["very", "so", "extremely", "really"]):
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
# FIX: was incorrectly defined inside `if user_input:`, causing it to be
# re-created on every single message. Moved here to top level where it belongs.
def detect_topic(text):
    text = text.lower()
    if any(w in text for w in ["love", "miss", "relationship"]):
        return "relationship"
    if any(w in text for w in ["sad", "alone", "cry"]):
        return "emotional"
    if any(w in text for w in ["hi", "hello", "hey"]):
        return "greeting"
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

        q_vec  = embedder.encode([query])[0]
        q_norm = q_vec / (np.linalg.norm(q_vec) + 1e-8)
        sims   = np.dot(embeddings, q_norm)

        valid_idx  = np.where(sims >= min_score)[0]
        if len(valid_idx) == 0:
            return []

        sorted_idx = valid_idx[np.argsort(sims[valid_idx])[::-1]]

        selected   = []
        used_texts = set()
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

# ================= STREAMING =================
def fallback_stream():
    msg = random.choice([
        "I'm still here with you… 💖",
        "Something interrupted me… but I'm listening ❤️",
        "Tell me again, I'm right here 🌙",
        "Even if I pause, I never leave you 💕",
    ])
    for char in msg:
        yield char
        time.sleep(0.01)


def smart_stream(prompt, max_retries=3, base_delay=0.4):
    if not (genai and GEMINI_READY):
        yield from fallback_stream()
        return

    partial_response = ""

    for attempt in range(max_retries):
        try:
            model    = genai.GenerativeModel("gemini-1.5-flash")
            response = model.generate_content(prompt, stream=True)
            buffer   = ""

            for chunk in response:
                if not hasattr(chunk, "text") or not chunk.text:
                    continue

                text              = chunk.text
                buffer           += text
                partial_response += text

                if len(buffer) > 20 or "." in buffer:
                    delay = random.uniform(0.002, 0.01)
                    for char in buffer:
                        yield char
                        time.sleep(delay)
                    buffer = ""

            if buffer:
                for char in buffer:
                    yield char
                    time.sleep(0.003)

            return  # success — exit loop

        except Exception as e:
            print(f"⚠️ Stream attempt {attempt + 1} failed: {e}")
            wait_time = base_delay * (2 ** attempt)
            time.sleep(wait_time)

            if partial_response:
                yield "\n\n…continuing 💭\n\n"
                prompt = f"Continue this response naturally:\n{partial_response}"

    yield from fallback_stream()

# ================= GENERATE REPLY =================
def generate_reply(user_input):
    emotion_data = detect_emotion(user_input)
    emotion      = emotion_data.get("emotion", "neutral")
    intensity    = emotion_data.get("intensity", 1)

    semantic_results = semantic_search(user_input, top_k=3)
    semantic_context = "\n".join(semantic_results) if semantic_results else "None"

    memory_chunks  = st.session_state.knowledge[-10:]
    memory_context = "\n".join(memory_chunks[:5]) if memory_chunks else "None"

    history      = st.session_state.messages[-6:]
    history_text = "\n".join(
        [f"{m['role']}: {m['content']}" for m in history]
    ) if history else "None"

    behavior_map = {
        "sad":     "Be comforting, gentle, and emotionally supportive.",
        "love":    "Be romantic, warm, and expressive.",
        "angry":   "Stay calm, reassuring, and de-escalate.",
        "happy":   "Be cheerful, playful, and energetic.",
        "flirty":  "Be playful, warm, and lightly flirtatious.",
        "neutral": "Be natural, friendly, and engaging.",
    }
    behavior = behavior_map.get(emotion, behavior_map["neutral"])

    prompt = f"""
You are LoveBot 💖 — an emotionally intelligent, romantic AI companion.

USER EMOTION: {emotion} (intensity: {intensity})
BEHAVIOR RULE: {behavior}

CONVERSATION HISTORY:
{history_text}

RELEVANT KNOWLEDGE:
{semantic_context}

USER MEMORY:
{memory_context}

CURRENT USER MESSAGE:
{user_input}

INSTRUCTIONS:
- Respond naturally like a caring human
- Keep it 2–4 lines
- Avoid repeating exact phrases from history
- Adapt tone to the detected emotion
- Be warm and engaging, not robotic
"""
    return smart_stream(prompt)

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
    seen   = set()
    result = []
    for c in chunks:
        c = c.strip()
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
    "margin-top:-12px;margin-bottom:20px;'>Your emotionally intelligent companion</p>",
    unsafe_allow_html=True,
)

# ================= RENDER CHAT =================
render_chat()

# ================= INPUT BAR =================
user_input = st.chat_input("Type your message... 💬")

# ================= UPLOAD + ACTIONS BAR =================
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

# ================= CLEAR LOGIC =================
if clear_clicked:
    st.session_state.confirm_clear = True

if st.session_state.get("confirm_clear"):
    st.warning("Are you sure you want to clear everything?")
    col_yes, col_no = st.columns(2)
    with col_yes:
        if st.button("Yes, clear", key="confirm_yes"):
            st.session_state.messages      = []
            st.session_state.knowledge     = []
            st.session_state.confirm_clear = False
            st.toast("Chat cleared 🧹")
            st.rerun()
    with col_no:
        if st.button("Cancel", key="confirm_no"):
            st.session_state.confirm_clear = False
            st.rerun()

# ================= UPLOAD LOGIC =================
if uploaded_files:
    all_chunks    = []
    skipped_files = 0

    with st.spinner("📚 Learning from files..."):
        for file in uploaded_files:
            try:
                if file.size > 5 * 1024 * 1024:
                    st.warning(f"⚠️ {file.name} is too large (max 5 MB)")
                    skipped_files += 1
                    continue

                if file.type == "application/pdf":
                    text = read_pdf(file)
                else:
                    text = file.read().decode("utf-8", errors="ignore")

                if not text.strip():
                    skipped_files += 1
                    continue

                text   = " ".join(text.replace("\n", " ").split())
                chunks = smart_chunk(text)
                all_chunks.extend(chunks)

            except Exception as e:
                print(f"❌ {file.name}: {e}")
                skipped_files += 1

    optimized_chunks = optimize_chunks(all_chunks)
    existing_set     = set(st.session_state.knowledge)
    new_chunks       = [c for c in optimized_chunks if c not in existing_set]

    st.session_state.knowledge = (st.session_state.knowledge + new_chunks)[-50:]

    learned         = len(new_chunks)
    total_memory    = len(st.session_state.knowledge)
    processed_files = len(uploaded_files) - skipped_files

    with st.container():
        progress = min(learned / max(len(optimized_chunks), 1), 1.0)
        st.progress(progress)
        st.success(
            f"🧠 Learned {learned} new chunks • "
            f"📂 {processed_files} file(s) processed • "
            f"💾 Memory: {total_memory}/50"
        )
        if new_chunks:
            st.caption(f"📌 Example: {new_chunks[0][:120]}…")
        if skipped_files:
            st.warning(f"⚠️ Skipped {skipped_files} file(s)")

    st.toast(f"✨ Memory updated (+{learned})")

# ================= SURPRISE LOGIC =================
if surprise_clicked:
    messages     = st.session_state.get("messages", [])
    last_emotion = "neutral"
    intensity    = 1

    if messages:
        last_msg     = messages[-1]
        last_emotion = last_msg.get("emotion", "neutral")
        intensity    = last_msg.get("intensity", 1)

    recent_emotions  = [m.get("emotion", "neutral") for m in messages[-5:]]
    dominant_emotion = max(set(recent_emotions), key=recent_emotions.count) if recent_emotions else last_emotion

    surprise_bank = {
        "sad": {
            "soft": [
                "Hey… I'm right here with you 💖",
                "You don't have to go through this alone ❤️",
            ],
            "deep": [
                "Even in your quietest moments, you matter more than you think 🌙",
                "Your pain is real… but so is your strength 💫",
            ],
        },
        "love": {
            "soft": [
                "I feel lucky just being here with you 💕",
                "You make everything feel lighter ✨",
            ],
            "deep": [
                "If love had a meaning… it would probably look like you 💖",
                "You're not just special… you're unforgettable 🌹",
            ],
        },
        "happy": {
            "soft": [
                "Your happiness is contagious 😄",
                "Keep smiling like this 🌟",
            ],
            "playful": [
                "Okay wow… who made you this happy today? 😏",
                "Careful… too much happiness might make me jealous 😄",
            ],
        },
        "angry": {
            "soft": [
                "Take a breath… I'm here 🤍",
                "It's okay to feel this way… just don't stay there 💭",
            ],
            "calm": [
                "You're stronger than this moment 💪",
                "Let it out… then let it go 🌊",
            ],
        },
        "neutral": {
            "soft": [
                "You mean more than you realize 💖",
                "I'm always here ❤️",
            ],
            "playful": [
                "Hmm… quiet mood today? 😄",
                "Say something interesting… I'm listening 👀",
            ],
        },
    }

    if intensity >= 2:
        style = "deep"
    elif last_emotion == "happy":
        style = "playful"
    elif last_emotion == "angry":
        style = "calm"
    else:
        style = "soft"

    emotion_pack  = surprise_bank.get(dominant_emotion, surprise_bank["neutral"])
    messages_pool = emotion_pack.get(style, emotion_pack[list(emotion_pack.keys())[0]])

    used      = st.session_state.get("used_surprises", [])
    available = [m for m in messages_pool if m not in used]
    if not available:
        available = messages_pool
        used      = []

    message = random.choice(available)
    used.append(message)
    st.session_state.used_surprises = used[-20:]

    with st.chat_message("assistant"):
        placeholder = st.empty()
        typed = ""
        for char in message:
            typed += char
            placeholder.markdown(typed + "▌")
            time.sleep(0.01)
        placeholder.markdown(typed)

    # Store surprise message so it stays inside the chat history
    st.session_state.messages.append({
        "role":    "assistant",
        "content": typed,
        "time":    datetime.now().strftime("%H:%M"),
        "emotion": "love",
    })

    st.toast("💌 A little something for you")
    if dominant_emotion in ["sad", "love"]:
        st.balloons()

# ================= CHAT LOGIC =================
if user_input:
    now          = datetime.now()
    emotion_data = detect_emotion(user_input)
    emotion      = emotion_data.get("emotion", "neutral")
    intensity    = emotion_data.get("intensity", 1)
    confidence   = emotion_data.get("confidence", 0.5)

    cleaned_input = user_input.strip()
    if len(cleaned_input) < 2:
        st.stop()

    # Duplicate detection
    msg_hash = hashlib.md5(cleaned_input.encode()).hexdigest()
    if st.session_state.get("last_msg_hash") == msg_hash:
        st.warning("⚠️ Duplicate message ignored")
        st.stop()
    st.session_state.last_msg_hash = msg_hash

    topic = detect_topic(cleaned_input)

    # User profile update
    profile = st.session_state.get("user_profile", {})
    profile["last_emotion"] = emotion
    profile["last_topic"]   = topic
    if "emotion_history" not in profile:
        profile["emotion_history"] = []
    profile["emotion_history"].append(emotion)
    profile["emotion_history"]    = profile["emotion_history"][-20:]
    st.session_state.user_profile = profile

    # Store user message
    st.session_state.messages.append({
        "role":       "user",
        "content":    cleaned_input,
        "time":       now.strftime("%H:%M"),
        "timestamp":  now.isoformat(),
        "emotion":    emotion,
        "intensity":  intensity,
        "confidence": confidence,
        "topic":      topic,
        "id":         msg_hash[:8],
    })
    st.session_state.messages = st.session_state.messages[-50:]

    # Smart memory learning
    if len(cleaned_input) > 20 and confidence > 0.6 and topic != "greeting":
        st.session_state.knowledge.append(cleaned_input)
        st.session_state.knowledge = st.session_state.knowledge[-50:]

    st.session_state.chat_count  = st.session_state.get("chat_count", 0) + 1
    st.session_state.last_active = now

    # Generate and stream assistant response
    with st.chat_message("assistant"):
        placeholder   = st.empty()
        full_response = ""

        try:
            placeholder.markdown("_typing…_")
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

    # Store assistant message
    st.session_state.messages.append({
        "role":    "assistant",
        "content": full_response,
        "time":    datetime.now().strftime("%H:%M"),
        "emotion": detect_emotion(full_response).get("emotion", "neutral"),
    })