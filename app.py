import streamlit as st
import pickle
import random
import os
import numpy as np

# ================= SAFE IMPORTS =================
# ================= ADVANCED IMPORT SYSTEM =================

import importlib
import sys

def safe_import(module_name, alias=None, install_name=None, critical=False):
    """
    Advanced safe import with debug + fallback
    """
    try:
        module = importlib.import_module(module_name)
        if alias:
            globals()[alias] = module
        else:
            globals()[module_name] = module
        return module

    except Exception as e:
        if critical:
            raise ImportError(f"❌ Critical module '{module_name}' failed to load: {e}")

        print(f"⚠️ Optional module '{module_name}' not available: {e}")
        return None


# ===== CORE IMPORTS =====
PdfReader = None

try:
    from pypdf import PdfReader
except Exception as e:
    print(f"⚠️ PDF support disabled: {e}")


# ===== OPTIONAL AI + SEARCH =====
GoogleSearch = None
genai = None

serpapi = safe_import("serpapi")
if serpapi:
    try:
        from serpapi import GoogleSearch
    except:
        GoogleSearch = None

genai = safe_import("google.generativeai", alias="genai")


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

# ================= ADVANCED LOAD MODEL =================
@st.cache_resource(show_spinner="🔄 Loading AI brain...")
def load_model():
    model_path = "model_advanced.pkl"

    # Check file existence
    if not os.path.exists(model_path):
        print("⚠️ Model file not found")
        return None

    try:
        with open(model_path, "rb") as f:
            data = pickle.load(f)

        # ===== VALIDATION =====
        required_keys = ["df", "embeddings", "embedder"]

        if not all(k in data for k in required_keys):
            print("❌ Model structure invalid")
            return None

        print("✅ Model loaded successfully")
        print(f"📊 Total data: {len(data['df'])}")

        return data

    except Exception as e:
        print(f"❌ Model loading failed: {e}")
        return None


# Load once
model_data = load_model()

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

    # ===== TRY GEMINI STREAM =====
    if genai and GEMINI_READY:
        for attempt in range(max_retries):
            try:
                model = genai.GenerativeModel("gemini-1.5-flash")

                response = model.generate_content(
                    prompt,
                    stream=True
                )

                for chunk in response:
                    if hasattr(chunk, "text") and chunk.text:
                        # simulate natural typing flow
                        for char in chunk.text:
                            yield char
                            time.sleep(typing_delay)

                return  # success → exit function

            except Exception as e:
                print(f"⚠️ Stream attempt {attempt+1} failed: {e}")
                time.sleep(0.5)

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

# ================= SMART BOTTOM BAR =================

st.markdown('<div class="bottom-bar">', unsafe_allow_html=True)

col1, col2, col3 = st.columns([8, 1, 1])

# ===== INPUT =====
with col1:
    user_input = st.chat_input("Type your message... 💬")

# ===== UPLOAD BUTTON (ICON STYLE) =====
with col2:
    uploaded_files = st.file_uploader(
        "",
        type=["pdf", "txt"],
        accept_multiple_files=True,
        label_visibility="collapsed"
    )

# ===== QUICK ACTION (CLEAR / SEND ICON STYLE) =====
with col3:
    clear_clicked = st.button("🗑", help="Clear Chat")

st.markdown('</div>', unsafe_allow_html=True)

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

    # ===== MEMORY CONTROL =====
    st.session_state.knowledge = (
        st.session_state.knowledge + unique_chunks
    )[-50:]

    # ===== USER FEEDBACK =====
    st.success(
        f"✅ Learned {len(unique_chunks)} chunks "
        f"from {len(uploaded_files) - skipped_files} files"
    )

    if skipped_files:
        st.info(f"⚠️ Skipped {skipped_files} file(s)")

# ================= ADVANCED CHAT LOGIC =================
from datetime import datetime

if user_input:

    # ===== ADD USER MESSAGE (WITH METADATA) =====
    emotion_data = detect_emotion(user_input)

    st.session_state.messages.append({
        "role": "user",
        "content": user_input,
        "time": datetime.now().strftime("%H:%M"),
        "emotion": emotion_data.get("emotion", "neutral")
    })

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


# ===== SMART SURPRISE =====
with colB:
    if st.button("💌 Surprise", help="Get a random sweet message"):

        # Context-aware surprise
        last_emotion = "neutral"
        if st.session_state.messages:
            last_msg = st.session_state.messages[-1]
            last_emotion = last_msg.get("emotion", "neutral")

        surprise_bank = {
            "sad": [
                "Hey… I’m right here with you 💖",
                "You’re not alone, not even for a second ❤️"
            ],
            "love": [
                "I feel lucky to have you 💕",
                "You make everything feel magical ✨"
            ],
            "happy": [
                "Your happiness makes me smile too 😄",
                "Keep shining like this 🌟"
            ],
            "angry": [
                "Take a breath… I’m here with you 🤍",
                "We’ll get through this together 💪"
            ],
            "neutral": [
                "You mean everything 💖",
                "I’m always here ❤️",
                "You make me smile 🌹"
            ]
        }

        message = random.choice(surprise_bank.get(last_emotion, surprise_bank["neutral"]))

        st.success(message)
        st.balloons()