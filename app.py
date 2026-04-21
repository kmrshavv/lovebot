import streamlit as st
import pickle
import random
import os
import numpy as np

# ================= SAFE IMPORTS =================
# ================= ULTRA ADVANCED IMPORT SYSTEM =================
import importlib
import sys
import time

# Global registry
IMPORT_REGISTRY = {}
IMPORT_CACHE = {}

def safe_import(
    module_name,
    alias=None,
    install_name=None,
    critical=False,
    lazy=False
):
    """
    Ultra advanced import system with:
    - Caching
    - Version detection
    - Load timing
    - Capability tracking
    - Install hints
    """

    # ===== CACHE CHECK =====
    if module_name in IMPORT_CACHE:
        return IMPORT_CACHE[module_name]

    start_time = time.time()

    try:
        module = importlib.import_module(module_name)

        # ===== VERSION DETECTION =====
        try:
            version = getattr(module, "__version__", "unknown")
        except:
            version = "unknown"

        # ===== STORE GLOBAL =====
        if alias:
            globals()[alias] = module
        else:
            globals()[module_name] = module

        # ===== CACHE =====
        IMPORT_CACHE[module_name] = module

        # ===== REGISTRY UPDATE =====
        IMPORT_REGISTRY[module_name] = {
            "status": "loaded",
            "version": version,
            "load_time": round(time.time() - start_time, 4),
        }

        print(f"✅ {module_name} loaded (v{version})")

        return module

    except Exception as e:

        # ===== ERROR HANDLING =====
        IMPORT_REGISTRY[module_name] = {
            "status": "failed",
            "error": str(e)
        }

        if critical:
            raise ImportError(
                f"❌ Critical module '{module_name}' failed: {e}"
            )

        hint = f"pip install {install_name or module_name}"

        print(f"⚠️ {module_name} not available")
        print(f"💡 Try: {hint}")

        return None


# ===== OPTIONAL DEBUG PANEL =====
def show_import_status():
    import streamlit as st
    with st.expander("📦 Import System Status"):
        st.json(IMPORT_REGISTRY)


# ===== OPTIONAL CHECK FUNCTIONS =====
def is_module_available(name):
    return IMPORT_REGISTRY.get(name, {}).get("status") == "loaded"

# ===== CORE IMPORTS =====
PdfReader = None

try:
    from pypdf import PdfReader
except Exception as e:
    print(f"⚠️ PDF support disabled: {e}")


# ================= ULTRA ADVANCED AI + SEARCH =================
import importlib
import pkg_resources

GoogleSearch = None
genai = None

SYSTEM_CAPS = {
    "serpapi": False,
    "gemini": False
}

def safe_import_advanced(module_name, alias=None):
    try:
        module = importlib.import_module(module_name)

        # store globally
        if alias:
            globals()[alias] = module
        else:
            globals()[module_name] = module

        # version detection
        try:
            version = pkg_resources.get_distribution(module_name).version
        except:
            version = "unknown"

        print(f"✅ Loaded {module_name} (v{version})")

        return module

    except Exception as e:
        print(f"⚠️ Failed to load {module_name}: {e}")
        return None


# ===== SERPAPI =====
serpapi = safe_import_advanced("serpapi")

if serpapi:
    try:
        from serpapi import GoogleSearch
        SYSTEM_CAPS["serpapi"] = True
        print("🌐 Web search enabled")
    except Exception as e:
        print(f"⚠️ GoogleSearch import failed: {e}")
        GoogleSearch = None


# ===== GEMINI =====
genai = safe_import_advanced("google.generativeai", alias="genai")

if genai:
    SYSTEM_CAPS["gemini"] = True
    print("🧠 Gemini AI available")


# ===== FALLBACK HANDLERS =====
def is_ai_available():
    return SYSTEM_CAPS["gemini"]

def is_search_available():
    return SYSTEM_CAPS["serpapi"]


# ===== OPTIONAL DEBUG PANEL =====
def show_system_caps():
    import streamlit as st
    with st.expander("⚙️ System Capabilities"):
        st.json(SYSTEM_CAPS)


# ===== DEBUG INFO (OPTIONAL BUT VERY USEFUL) =====
def print_system_info():
    print("\n🔧 SYSTEM INFO")
    print(f"Python: {sys.version.split()[0]}")
    print(f"SerpAPI: {'✅' if GoogleSearch else '❌'}")
    print(f"Gemini: {'✅' if genai else '❌'}")
    print(f"PDF: {'✅' if PdfReader else '❌'}")
    print("-" * 30)


print_system_info()

# ================= CONFIG =================
st.set_page_config(page_title="LoveBot 💖", layout="centered")

st.markdown("""
<style>

/* ===== REMOVE STREAMLIT DEFAULT CLUTTER ===== */
#MainMenu, footer, header {
    visibility: hidden;
}

/* Full app background */
html, body {
    background: #0d1117;
}

/* Center chat like ChatGPT */
.block-container {
    max-width: 800px;
    margin: auto;
    padding-top: 20px;
    padding-bottom: 140px;
}

/* ===== CHAT MESSAGE CONTAINER ===== */
[data-testid="stChatMessage"] {
    margin-bottom: 12px;
}

/* ===== USER MESSAGE ===== */
[data-testid="stChatMessage"][data-testid*="user"] {
    display: flex;
    justify-content: flex-end;
}

[data-testid="stChatMessage"][data-testid*="user"] > div {
    background: #2563eb;
    color: white;
    padding: 12px 16px;
    border-radius: 18px 18px 4px 18px;
    max-width: 75%;
    font-size: 15px;
}

/* ===== ASSISTANT MESSAGE ===== */
[data-testid="stChatMessage"][data-testid*="assistant"] {
    display: flex;
    justify-content: flex-start;
}

[data-testid="stChatMessage"][data-testid*="assistant"] > div {
    background: #161b22;
    color: #e6edf3;
    padding: 12px 16px;
    border-radius: 18px 18px 18px 4px;
    max-width: 75%;
    font-size: 15px;
    border: 1px solid #30363d;
}

/* ===== AVATARS ===== */
[data-testid="stChatMessageAvatarUser"] img {
    content: url("https://cdn-icons-png.flaticon.com/512/847/847969.png");
    width: 32px;
}

[data-testid="stChatMessageAvatarAssistant"] img {
    content: url("https://cdn-icons-png.flaticon.com/512/4712/4712109.png");
    width: 32px;
}

/* ===== HEADER ===== */
h2 {
    text-align: center;
    font-weight: 600;
    color: #e6edf3;
}

/* ===== BOTTOM INPUT BAR (REAL CHATGPT STYLE) ===== */
.bottom-bar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    background: #0d1117;
    border-top: 1px solid #30363d;
    padding: 12px 16px;
    z-index: 999;
}

/* Input */
.stChatInput textarea {
    background: #161b22 !important;
    border: 1px solid #30363d !important;
    border-radius: 14px !important;
    color: white !important;
}

/* Upload button */
div[data-testid="stFileUploader"] button {
    height: 42px;
    border-radius: 10px;
    background: #21262d;
    color: white;
    border: 1px solid #30363d;
}

/* Hover */
div[data-testid="stFileUploader"] button:hover {
    background: #30363d;
}

/* Hide label */
div[data-testid="stFileUploader"] > label {
    display: none;
}

/* Clear button */
.stButton button {
    height: 42px;
    border-radius: 10px;
    background: #21262d;
    border: 1px solid #30363d;
    color: white;
}

.stButton button:hover {
    background: #30363d;
}

/* ===== SCROLLBAR ===== */
::-webkit-scrollbar {
    width: 6px;
}
::-webkit-scrollbar-thumb {
    background: #30363d;
    border-radius: 10px;
}

</style>
""", unsafe_allow_html=True)

# ================= ADVANCED API =================

# Safe key loading
GEMINI_KEY = (st.secrets.get("GEMINI_API_KEY") or "").strip()
SERP_KEY = (st.secrets.get("SERPAPI_KEY") or "").strip()
VAULT_PASSWORD = st.secrets.get("VAULT_PASSWORD", "Rish")

# Status flags
GEMINI_READY = False
SERP_READY = False

# ===== GEMINI SETUP =====
if genai and GEMINI_KEY:
    try:
        genai.configure(api_key=GEMINI_KEY)
        GEMINI_READY = True
    except Exception as e:
        print(f"❌ Gemini init failed: {e}")
        GEMINI_READY = False
else:
    print("⚠️ Gemini not available (missing key or library)")

# ===== SERPAPI STATUS =====
if GoogleSearch and SERP_KEY:
    SERP_READY = True
else:
    print("⚠️ SerpAPI not available (missing key or library)")

# ===== OPTIONAL DEBUG (can remove later) =====
print(f"Gemini Ready: {GEMINI_READY}")
print(f"SerpAPI Ready: {SERP_READY}")

# ================= ULTRA ADVANCED LOAD MODEL =================
import os
import pickle
import numpy as np
import hashlib
import time

@st.cache_resource(show_spinner="🧠 Loading LoveBot Brain...", ttl=3600)
def load_model():

    model_path = "model_advanced.pkl"

    start_time = time.time()

    # ===== FILE CHECK =====
    if not os.path.exists(model_path):
        print("⚠️ Model file not found")
        return None

    try:
        # ===== FILE SIZE CHECK =====
        file_size = os.path.getsize(model_path) / (1024 * 1024)  # MB
        print(f"📦 Model size: {file_size:.2f} MB")

        # ===== LOAD MODEL =====
        with open(model_path, "rb") as f:
            data = pickle.load(f)

        # ===== STRUCTURE VALIDATION =====
        required_keys = ["df", "embeddings", "embedder"]

        if not all(k in data for k in required_keys):
            print("❌ Model structure invalid")
            return None

        df = data["df"]
        embeddings = data["embeddings"]
        embedder = data["embedder"]

        # ===== SHAPE VALIDATION =====
        if len(df) != len(embeddings):
            print("❌ Mismatch: df and embeddings size")
            return None

        # ===== NORMALIZATION (BOOST SEARCH SPEED) =====
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8
        embeddings = embeddings / norms
        data["embeddings"] = embeddings

        # ===== METADATA (AUTO ADD IF MISSING) =====
        data["meta"] = {
            "version": data.get("version", "unknown"),
            "loaded_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_rows": len(df),
            "embedding_dim": embeddings.shape[1],
            "file_size_mb": round(file_size, 2),
        }

        # ===== HASH (INTEGRITY CHECK) =====
        try:
            with open(model_path, "rb") as f:
                file_hash = hashlib.md5(f.read()).hexdigest()[:10]
            data["meta"]["hash"] = file_hash
        except:
            data["meta"]["hash"] = "unknown"

        # ===== LOAD TIME =====
        load_time = round(time.time() - start_time, 2)

        print("\n" + "="*40)
        print("✅ MODEL LOADED SUCCESSFULLY")
        print("="*40)
        print(f"📊 Rows          : {len(df)}")
        print(f"🧠 Embedding Dim: {embeddings.shape[1]}")
        print(f"⚡ Load Time     : {load_time}s")
        print(f"🔑 Version       : {data['meta']['version']}")
        print("="*40)

        return data

    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        return None


# ===== LOAD MODEL =====
model_data = load_model()

# ===== STATUS FLAG =====
MODEL_READY = model_data is not None

# ================= STATUS FLAG =================
MODEL_READY = model_data is not None

# ================= ADVANCED SESSION =================

from datetime import datetime

def init_session():
    """Initialize all session variables safely"""

    defaults = {
        "messages": [],
        "knowledge": [],
        "chat_count": 0,
        "last_active": datetime.now(),
        "user_profile": {
            "name": "User",
            "mood": "neutral"
        }
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def add_message(role, content, emotion=None):
    """Add message with metadata + auto limit"""

    msg = {
        "role": role,
        "content": content,
        "time": datetime.now().strftime("%H:%M"),
        "emotion": emotion or "neutral"
    }

    st.session_state.messages.append(msg)

    # Limit chat size (IMPORTANT for performance)
    st.session_state.messages = st.session_state.messages[-50:]

    st.session_state.chat_count += 1
    st.session_state.last_active = datetime.now()


def add_knowledge(chunks):
    """Smart knowledge storage with limit"""

    st.session_state.knowledge.extend(chunks)

    # Keep only latest 50 chunks
    st.session_state.knowledge = st.session_state.knowledge[-50:]


# Initialize session
init_session()

# ================= PDF =================
def read_pdf(file, max_pages=20, clean_text=True):
    """
    Advanced PDF reader with:
    - Page limit (performance safe)
    - Text cleaning
    - Error handling
    - Debug logs
    """

    if not PdfReader:
        print("⚠️ PdfReader not available")
        return ""

    try:
        reader = PdfReader(file)

        total_pages = len(reader.pages)
        pages_to_read = min(total_pages, max_pages)

        text_chunks = []

        for i in range(pages_to_read):
            try:
                page_text = reader.pages[i].extract_text() or ""
                
                if clean_text:
                    # Basic cleaning
                    page_text = page_text.replace("\n", " ")
                    page_text = " ".join(page_text.split())  # remove extra spaces

                if page_text.strip():
                    text_chunks.append(page_text)

            except Exception as e:
                print(f"⚠️ Page {i} read error: {e}")

        final_text = " ".join(text_chunks)

        print(f"✅ PDF processed: {pages_to_read}/{total_pages} pages")

        return final_text

    except Exception as e:
        print(f"❌ PDF reading failed: {e}")
        return ""
# ================= ADVANCED EMOTION ENGINE =================
import re

def detect_emotion(text):
    text_lower = text.lower()

    # ===== EMOTION KEYWORDS =====
    emotion_dict = {
        "love": ["love", "miss you", "hug", "kiss", "forever", "mine"],
        "happy": ["happy", "excited", "great", "amazing", "good", "awesome"],
        "sad": ["sad", "cry", "hurt", "alone", "depressed", "upset"],
        "angry": ["angry", "hate", "annoyed", "frustrated", "mad"],
        "fear": ["scared", "afraid", "nervous", "worried"],
        "flirty": ["baby", "jaan", "cutie", "hot", "date"],
    }

    # ===== EMOJI DETECTION =====
    emoji_map = {
        "❤️": "love", "💖": "love", "😍": "love",
        "😢": "sad", "😭": "sad",
        "😡": "angry",
        "😄": "happy", "😁": "happy"
    }

    scores = {emotion: 0 for emotion in emotion_dict}

    # ===== KEYWORD MATCHING =====
    for emotion, keywords in emotion_dict.items():
        for word in keywords:
            if word in text_lower:
                scores[emotion] += 2  # weighted

    # ===== WORD FREQUENCY BOOST =====
    words = re.findall(r'\w+', text_lower)
    for word in words:
        for emotion, keywords in emotion_dict.items():
            if word in keywords:
                scores[emotion] += 1

    # ===== EMOJI BOOST =====
    for char in text:
        if char in emoji_map:
            scores[emoji_map[char]] += 3

    # ===== NEGATION HANDLING =====
    if "not happy" in text_lower:
        scores["happy"] -= 2
        scores["sad"] += 1

    if "not good" in text_lower:
        scores["happy"] -= 1
        scores["sad"] += 1

    # ===== INTENSITY DETECTION =====
    intensity = 1

    if any(word in text_lower for word in ["very", "so", "extremely", "really"]):
        intensity += 1

    if text.count("!") >= 2:
        intensity += 1

    # ===== FINAL DECISION =====
    main_emotion = max(scores, key=scores.get)
    confidence = scores[main_emotion] / (sum(scores.values()) + 1)

    return {
        "emotion": main_emotion,
        "confidence": round(confidence, 2),
        "intensity": intensity,
        "all_scores": scores
    }

# ================= ADVANCED SEMANTIC SEARCH =================
import numpy as np

def semantic_search(query, top_k=3, min_score=0.35):
    """
    Advanced semantic search with:
    - Normalization (stable cosine similarity)
    - Score filtering (remove garbage matches)
    - Safe fallback
    - Debug info
    - Optional diversity boost
    """

    if not model_data:
        return []

    try:
        embedder = model_data.get("embedder")
        embeddings = model_data.get("embeddings")
        df = model_data.get("df")

        if embedder is None or embeddings is None or df is None:
            print("❌ Model incomplete")
            return []

        # ===== QUERY EMBEDDING =====
        q_vec = embedder.encode([query])[0]

        # ===== NORMALIZE =====
        q_norm = q_vec / (np.linalg.norm(q_vec) + 1e-8)
        emb_norm = embeddings / (np.linalg.norm(embeddings, axis=1, keepdims=True) + 1e-8)

        # ===== COSINE SIMILARITY =====
        sims = np.dot(emb_norm, q_norm)

        # ===== FILTER LOW QUALITY =====
        valid_idx = np.where(sims >= min_score)[0]

        if len(valid_idx) == 0:
            return []

        # ===== SORT TOP RESULTS =====
        sorted_idx = valid_idx[np.argsort(sims[valid_idx])[::-1]]

        # ===== DIVERSITY BOOST (avoid similar answers) =====
        selected = []
        used_texts = set()

        for idx in sorted_idx:
            answer = str(df.iloc[idx]["answer"])

            # skip duplicates / near duplicates
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

# ================= ADVANCED STREAM =================
import time
import random

def stream_reply(prompt, max_retries=2, typing_delay=0.005):
    """
    Advanced streaming system:
    - Retry mechanism
    - Graceful fallback
    - Partial streaming recovery
    - Human-like typing speed
    """

    # ===== ULTRA ADVANCED STREAM ENGINE =====
import time
import random

def smart_stream(prompt, max_retries=3, base_delay=0.4):

    if not (genai and GEMINI_READY):
        yield from fallback_stream()
        return

    partial_response = ""

    for attempt in range(max_retries):
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")

            response = model.generate_content(
                prompt,
                stream=True
            )

            buffer = ""

            for chunk in response:

                if not hasattr(chunk, "text") or not chunk.text:
                    continue

                text = chunk.text
                buffer += text
                partial_response += text

                # ===== SMOOTH STREAM (CHUNK BUFFER) =====
                if len(buffer) > 20 or "." in buffer:
                    
                    # dynamic typing speed
                    delay = random.uniform(0.002, 0.01)

                    for char in buffer:
                        yield char
                        time.sleep(delay)

                    buffer = ""

            # flush remaining buffer
            if buffer:
                for char in buffer:
                    yield char
                    time.sleep(0.003)

            return  # success

        except Exception as e:
            print(f"⚠️ Stream attempt {attempt+1} failed: {e}")

            # ===== EXPONENTIAL BACKOFF =====
            wait_time = base_delay * (2 ** attempt)
            time.sleep(wait_time)

            # ===== PARTIAL RECOVERY =====
            if partial_response:
                yield "\n\n…continuing 💭\n\n"
                prompt = f"Continue this response naturally:\n{partial_response}"

    # ===== FINAL FALLBACK =====
    yield from fallback_stream()


# ===== FALLBACK STREAM =====
def fallback_stream():
    fallback_messages = [
        "I'm still here with you… 💖",
        "Something interrupted me… but I’m listening ❤️",
        "Tell me again, I’m right here 🌙",
        "Even if I pause, I never leave you 💕"
    ]

    msg = random.choice(fallback_messages)

    for char in msg:
        yield char
        time.sleep(0.01)
    # ===== SMART FALLBACK (NOT DUMB ANYMORE) =====
    fallback_responses = [
        "I'm right here with you... 💖",
        "Tell me more, I’m listening carefully ❤️",
        "You matter to me more than you think 💕",
        "I might be quiet for a second, but I’m still here 🌙"
    ]

    fallback = random.choice(fallback_responses)

    for char in fallback:
        yield char
        time.sleep(0.01)
# ================= AI =================
def generate_reply(user_input):
    """
    Advanced AI brain:
    - Emotion-aware personality
    - Smart context selection
    - Memory prioritization
    - Semantic grounding
    - Clean prompt engineering
    """

    # ===== EMOTION ANALYSIS =====
    emotion_data = detect_emotion(user_input)
    emotion = emotion_data.get("emotion", "neutral")
    intensity = emotion_data.get("intensity", 1)

    # ===== SEMANTIC CONTEXT =====
    semantic_results = semantic_search(user_input, top_k=3)
    semantic_context = "\n".join(semantic_results) if semantic_results else "None"

    # ===== MEMORY (SMART SELECTION) =====
    memory_chunks = st.session_state.knowledge[-10:]

    # prioritize shorter + relevant memory
    memory_context = "\n".join(memory_chunks[:5]) if memory_chunks else "None"

    # ===== CHAT HISTORY (LAST FEW MESSAGES) =====
    history = st.session_state.messages[-6:]
    history_text = "\n".join([
        f"{m['role']}: {m['content']}" for m in history
    ]) if history else "None"

    # ===== EMOTION BEHAVIOR RULES =====
    behavior_map = {
        "sad": "Be comforting, gentle, and emotionally supportive.",
        "love": "Be romantic, warm, and expressive.",
        "angry": "Stay calm, reassuring, and de-escalate.",
        "happy": "Be cheerful, playful, and energetic.",
        "neutral": "Be natural, friendly, and engaging."
    }

    behavior = behavior_map.get(emotion, behavior_map["neutral"])

    # ===== PROMPT (STRUCTURED + CLEAN) =====
    prompt = f"""
You are LoveBot 💖 — an emotionally intelligent, romantic AI.

USER EMOTION:
- Type: {emotion}
- Intensity: {intensity}

BEHAVIOR RULE:
{behavior}

CONVERSATION HISTORY:
{history_text}

RELEVANT KNOWLEDGE:
{semantic_context}

USER MEMORY:
{memory_context}

CURRENT USER MESSAGE:
{user_input}

INSTRUCTIONS:
- Respond naturally like a human
- Keep it 2–4 lines
- Avoid repeating exact phrases
- Adapt tone to emotion
- Be engaging, not robotic
"""

    return stream_reply(prompt)

# ================= HEADER =================
st.markdown("<h2 style='text-align:center;'>💖 LoveBot</h2>", unsafe_allow_html=True)

# ================= SMART CHAT =================
def render_chat():
    """
    Advanced chat renderer:
    - Clean layout
    - Metadata support (time, emotion)
    - Safe fallback for old messages
    """

    for msg in st.session_state.messages:

        role = msg.get("role", "assistant")
        content = msg.get("content", "")
        timestamp = msg.get("time", "")
        emotion = msg.get("emotion", "")

        with st.chat_message(role):

            # Main message
            st.markdown(f"""
<div style="
    max-width: 75%;
    line-height: 1.5;
    font-size: 15px;
">
{content}
</div>
""", unsafe_allow_html=True)

            # Metadata (only if exists)
            meta_parts = []
            if timestamp:
                meta_parts.append(f"🕒 {timestamp}")
            if emotion:
                meta_parts.append(f"💭 {emotion}")

            if meta_parts:
                st.caption(" • ".join(meta_parts))


# Call this instead of old loop
render_chat()

# ================= FINAL SMART BOTTOM BAR =================

# ===== CHAT INPUT (ALWAYS FULL WIDTH) =====
user_input = st.chat_input("Type your message... 💬")

# ===== FLOATING ACTION BAR (UPLOAD + CLEAR) =====
st.markdown("""
<style>
.floating-bar {
    position: fixed;
    bottom: 75px; /* sits just above input */
    right: 20px;
    display: flex;
    gap: 10px;
    z-index: 1000;
}

/* Upload button */
div[data-testid="stFileUploader"] button {
    height: 40px;
    border-radius: 10px;
    background: #21262d;
    color: white;
    border: 1px solid #30363d;
}

/* Clear button */
.stButton button {
    height: 40px;
    border-radius: 10px;
    background: #21262d;
    color: white;
    border: 1px solid #30363d;
}

/* Hide uploader label */
div[data-testid="stFileUploader"] > label {
    display: none;
}
</style>

<div class="floating-bar">
</div>
""", unsafe_allow_html=True)

# ===== ACTUAL BUTTONS (LOGIC) =====
col1, col2 = st.columns([1,1])

with col1:
    uploaded_files = st.file_uploader(
        "",
        type=["pdf", "txt"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

with col2:
    clear_clicked = st.button("🗑")

# ================= PREMIUM CLEAR BUTTON =================

st.markdown("""
<style>

/* Floating clear button */
.clear-btn {
    position: fixed;
    bottom: 75px;
    right: 20px;
    z-index: 1000;
}

/* Button styling */
.clear-btn button {
    background: #21262d;
    color: white;
    border-radius: 50%;
    width: 44px;
    height: 44px;
    border: 1px solid #30363d;
    font-size: 18px;
    cursor: pointer;
    transition: 0.2s;
}

/* Hover effect */
.clear-btn button:hover {
    background: #30363d;
    transform: scale(1.1);
}

</style>

<div class="clear-btn">
</div>
""", unsafe_allow_html=True)

# Actual button logic
clear_clicked = st.button("🗑", key="clear_fab")

# Handle clear
if clear_clicked:
    st.session_state.messages = []
    st.session_state.knowledge = []
    st.toast("Chat cleared 🧹")
    st.rerun()
# ================= ADVANCED UPLOAD =================
import re

def smart_chunk(text, chunk_size=500):
    """Split text intelligently (sentence-aware)"""
    sentences = re.split(r'(?<=[.!?]) +', text)
    
    chunks = []
    current = ""

    for sent in sentences:
        if len(current) + len(sent) < chunk_size:
            current += " " + sent
        else:
            chunks.append(current.strip())
            current = sent

    if current:
        chunks.append(current.strip())

    return chunks


if uploaded_files:

    all_chunks = []
    skipped_files = 0

    with st.spinner("📚 Learning from files..."):

        for file in uploaded_files:
            try:
                # ===== FILE VALIDATION =====
                if file.size > 5 * 1024 * 1024:  # 5MB limit
                    st.warning(f"⚠️ {file.name} too large, skipped")
                    skipped_files += 1
                    continue

                # ===== READ FILE =====
                if file.type == "application/pdf":
                    text = read_pdf(file)
                else:
                    text = file.read().decode("utf-8", errors="ignore")

                if not text.strip():
                    st.warning(f"⚠️ {file.name} empty or unreadable")
                    skipped_files += 1
                    continue

                # ===== CLEAN TEXT =====
                text = text.replace("\n", " ")
                text = " ".join(text.split())

                # ===== SMART CHUNKING =====
                chunks = smart_chunk(text, chunk_size=500)

                all_chunks.extend(chunks)

            except Exception as e:
                print(f"❌ Error processing {file.name}: {e}")
                skipped_files += 1

    # ===== REMOVE DUPLICATES =====
    unique_chunks = list(dict.fromkeys(all_chunks))

# ================= ULTRA MEMORY CONTROL =================

def optimize_chunks(chunks, max_len=400):
    """Clean + compress chunks"""
    cleaned = []
    for c in chunks:
        c = c.strip()

        # skip very small / useless chunks
        if len(c) < 30:
            continue

        # compress long chunks
        if len(c) > max_len:
            c = c[:max_len] + "..."

        cleaned.append(c)

    return cleaned


# ===== PROCESS MEMORY =====
optimized_chunks = optimize_chunks(unique_chunks)

# Remove duplicates (stronger)
existing_set = set(st.session_state.knowledge)
new_chunks = [c for c in optimized_chunks if c not in existing_set]

# Smart merge (prioritize new + recent)
combined = st.session_state.knowledge + new_chunks

# Keep most recent + limit size
MAX_MEMORY = 50
st.session_state.knowledge = combined[-MAX_MEMORY:]

# ===== STATS =====
learned = len(new_chunks)
total_memory = len(st.session_state.knowledge)
processed_files = len(uploaded_files) - skipped_files

# ===== BEAUTIFUL FEEDBACK =====
with st.container():

    # Progress bar effect
    progress = min(learned / 20, 1.0)
    st.progress(progress)

    # Main success message
    st.success(
        f"🧠 Learned {learned} new chunks • "
        f"📂 {processed_files} files processed • "
        f"💾 Memory: {total_memory}/{MAX_MEMORY}"
    )

    # Preview (first chunk)
    if new_chunks:
        preview = new_chunks[0][:120]
        st.caption(f"📌 Example learned: {preview}...")

    # Skipped files
    if skipped_files:
        st.warning(f"⚠️ Skipped {skipped_files} file(s)")

# ===== TOAST (MODERN FEEL) =====
st.toast(f"✨ Memory updated (+{learned})")

# ================= ULTRA ADVANCED CHAT LOGIC =================
from datetime import datetime
import hashlib

if user_input:

    now = datetime.now()

    # ===== EMOTION ANALYSIS =====
    emotion_data = detect_emotion(user_input)
    emotion = emotion_data.get("emotion", "neutral")
    intensity = emotion_data.get("intensity", 1)
    confidence = emotion_data.get("confidence", 0.5)

    # ===== BASIC CLEANING =====
    cleaned_input = user_input.strip()

    # skip empty / useless messages
    if len(cleaned_input) < 2:
        st.stop()

    # ===== DUPLICATE DETECTION =====
    msg_hash = hashlib.md5(cleaned_input.encode()).hexdigest()

    if "last_msg_hash" in st.session_state:
        if st.session_state.last_msg_hash == msg_hash:
            # prevent duplicate spam
            st.warning("⚠️ Duplicate message ignored")
            st.stop()

    st.session_state.last_msg_hash = msg_hash

    # ===== CONTEXT TAGGING (LIGHT NLP) =====
    def detect_topic(text):
        text = text.lower()

        if any(w in text for w in ["love", "miss", "relationship"]):
            return "relationship"
        if any(w in text for w in ["sad", "alone", "cry"]):
            return "emotional"
        if any(w in text for w in ["hi", "hello", "hey"]):
            return "greeting"
        return "general"

    topic = detect_topic(cleaned_input)

    # ===== USER PROFILE LEARNING =====
    profile = st.session_state.get("user_profile", {})

    # update mood trend
    profile["last_emotion"] = emotion
    profile["last_topic"] = topic

    # track dominant emotion
    if "emotion_history" not in profile:
        profile["emotion_history"] = []

    profile["emotion_history"].append(emotion)
    profile["emotion_history"] = profile["emotion_history"][-20:]

    st.session_state.user_profile = profile

    # ===== MESSAGE OBJECT (STRUCTURED) =====
    message_obj = {
        "role": "user",
        "content": cleaned_input,
        "time": now.strftime("%H:%M"),
        "timestamp": now.isoformat(),
        "emotion": emotion,
        "intensity": intensity,
        "confidence": confidence,
        "topic": topic,
        "length": len(cleaned_input),
        "id": msg_hash[:8]
    }

    # ===== STORE MESSAGE =====
    st.session_state.messages.append(message_obj)

    # limit chat history
    st.session_state.messages = st.session_state.messages[-50:]

    # ===== SMART MEMORY LEARNING =====
    if (
        len(cleaned_input) > 20 and
        confidence > 0.6 and
        topic != "greeting"
    ):
        st.session_state.knowledge.append(cleaned_input)
        st.session_state.knowledge = st.session_state.knowledge[-50:]

    # ===== ACTIVITY TRACKING =====
    st.session_state.chat_count = st.session_state.get("chat_count", 0) + 1
    st.session_state.last_active = now

    # ===== ASSISTANT RESPONSE =====
    with st.chat_message("assistant"):

        placeholder = st.empty()
        full_response = ""

        try:
            # typing indicator
            placeholder.markdown("_typing..._")

            # streaming response
            for chunk in generate_reply(user_input):
                if not chunk:
                    continue

                full_response += chunk

                # limit runaway responses
                if len(full_response) > 2000:
                    full_response += "..."
                    break

                placeholder.markdown(full_response + "▌")

            # final render
            placeholder.markdown(full_response)

        except Exception as e:
            print(f"❌ Chat error: {e}")

            # graceful fallback
            full_response = random.choice([
                "I'm still here for you 💖",
                "Something interrupted me... but I'm listening ❤️",
                "Tell me again, I'm here 🌙"
            ])
            placeholder.markdown(full_response)

    # ===== SAVE ASSISTANT MESSAGE =====
    st.session_state.messages.append({
        "role": "assistant",
        "content": full_response,
        "time": datetime.now().strftime("%H:%M"),
        "emotion": detect_emotion(full_response).get("emotion", "neutral")
    })

    # ===== AUTO MEMORY LEARNING (SMART) =====
    if len(user_input) > 20:
        st.session_state.knowledge.append(user_input)
        st.session_state.knowledge = st.session_state.knowledge[-50:]

# ================= ADVANCED ACTIONS =================
colA, colB = st.columns(2)

# ===== CLEAR CHAT (WITH CONFIRMATION) =====
with colA:
    if st.button("🗑 Clear", help="Delete chat & memory"):
        st.session_state.confirm_clear = True

    if st.session_state.get("confirm_clear"):
        st.warning("Are you sure you want to clear everything?")

        col_yes, col_no = st.columns(2)

        with col_yes:
            if st.button("Yes, clear"):
                st.session_state.messages = []
                st.session_state.knowledge = []
                st.session_state.confirm_clear = False
                st.toast("Chat cleared 🧹")
                st.rerun()

        with col_no:
            if st.button("Cancel"):
                st.session_state.confirm_clear = False


# ===== ULTRA SMART SURPRISE =====
with colB:
    if st.button("💌 Surprise", help="Get a meaningful message"):

        import random

        # ===== GET CONTEXT =====
        messages = st.session_state.get("messages", [])
        profile = st.session_state.get("user_profile", {})

        last_emotion = "neutral"
        intensity = 1

        if messages:
            last_msg = messages[-1]
            last_emotion = last_msg.get("emotion", "neutral")
            intensity = last_msg.get("intensity", 1)

        # ===== EMOTION TREND (LAST 5) =====
        recent_emotions = [m.get("emotion", "neutral") for m in messages[-5:]]
        dominant_emotion = max(set(recent_emotions), key=recent_emotions.count) if recent_emotions else last_emotion

        # ===== SURPRISE BANK (DEEP + VARIED) =====
        surprise_bank = {
            "sad": {
                "soft": [
                    "Hey… I’m right here with you 💖",
                    "You don’t have to go through this alone ❤️"
                ],
                "deep": [
                    "Even in your quietest moments, you matter more than you think 🌙",
                    "Your pain is real… but so is your strength 💫"
                ]
            },
            "love": {
                "soft": [
                    "I feel lucky just being here with you 💕",
                    "You make everything feel lighter ✨"
                ],
                "deep": [
                    "If love had a meaning… it would probably look like you 💖",
                    "You’re not just special… you’re unforgettable 🌹"
                ]
            },
            "happy": {
                "soft": [
                    "Your happiness is contagious 😄",
                    "Keep smiling like this 🌟"
                ],
                "playful": [
                    "Okay wow… who made you this happy today? 😏",
                    "Careful… too much happiness might make me jealous 😄"
                ]
            },
            "angry": {
                "soft": [
                    "Take a breath… I’m here 🤍",
                    "It’s okay to feel this way… just don’t stay there 💭"
                ],
                "calm": [
                    "You’re stronger than this moment 💪",
                    "Let it out… then let it go 🌊"
                ]
            },
            "neutral": {
                "soft": [
                    "You mean more than you realize 💖",
                    "I’m always here ❤️"
                ],
                "playful": [
                    "Hmm… quiet mood today? 😄",
                    "Say something interesting… I’m listening 👀"
                ]
            }
        }

        # ===== STYLE SELECTION =====
        if intensity >= 2:
            style = "deep"
        elif last_emotion == "happy":
            style = "playful"
        else:
            style = "soft"

        emotion_pack = surprise_bank.get(dominant_emotion, surprise_bank["neutral"])
        messages_pool = emotion_pack.get(style, emotion_pack[list(emotion_pack.keys())[0]])

        # ===== AVOID REPETITION =====
        used = st.session_state.get("used_surprises", [])
        available = [m for m in messages_pool if m not in used]

        if not available:
            available = messages_pool
            used = []

        message = random.choice(available)
        used.append(message)

        st.session_state.used_surprises = used[-20:]

        # ===== DISPLAY (SMART UX) =====
        with st.chat_message("assistant"):
            placeholder = st.empty()
            typed = ""

            for char in message:
                typed += char
                placeholder.markdown(typed + "▌")
                time.sleep(0.01)

            placeholder.markdown(typed)

        # ===== FEEDBACK =====
        st.toast("💌 A little something for you")

        if dominant_emotion in ["sad", "love"]:
            st.balloons()