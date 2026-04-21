import pandas as pd
import json
import pickle
import numpy as np
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

# ==============================
# MODERN EMBEDDINGS
# ==============================
from sentence_transformers import SentenceTransformer
import google.generativeai as genai

# ==============================
# LOAD DATA (More Robust)
# ==============================
def load_csv(path):
    try:
        df = pd.read_csv(path, on_bad_lines='skip', encoding='utf-8')
        print(f"✅ Loaded {path}: {len(df)} rows")
        return df
    except Exception as e:
        print(f"❌ Error loading {path}: {e}")
        return pd.DataFrame()

df1 = load_csv("data/chatbot.csv")
df2 = load_csv("data/data.csv")

# ==============================
# LOAD JSON (All Formats + Auto-clean)
# ==============================
json_rows = []
try:
    with open("data/chatbot.json", encoding='utf-8') as f:
        content = f.read().strip()
        if content.startswith('['):  # Array of objects
            data = json.loads(content)
        else:  # Line by line
            data = [json.loads(line) for line in content.splitlines() if line.strip()]

        for item in data:
            json_rows.append({
                "question": str(item.get("question", "")).strip(),
                "answer": str(item.get("answer", "")).strip(),
                "love_score": float(item.get("love_score", 85)),
                "emotion": item.get("emotion", "love"),
                "timestamp": datetime.now().isoformat()
            })
except Exception as e:
    print(f"JSON loading error: {e}")

df3 = pd.DataFrame(json_rows)

# ==============================
# COMBINE + CLEAN
# ==============================
df = pd.concat([df1, df2, df3], ignore_index=True)

# Required columns
for col in ["question", "answer"]:
    if col not in df.columns:
        df[col] = ""

df = df[["question", "answer"]].copy()
df = df.dropna(subset=["question", "answer"])
df = df[df["question"].str.len() > 3]

# Advanced cleaning
df["question"] = df["question"].str.strip().str.lower()
df["answer"] = df["answer"].str.strip()

print(f"Total cleaned pairs: {len(df)}")

# ==============================
# ================= ULTRA ADVANCED EMBEDDINGS =================
import numpy as np
import time
import torch

def generate_embeddings(df, model_name="all-MiniLM-L6-v2", batch_size=64):

    start_time = time.time()

    # ===== DEVICE DETECTION =====
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"⚡ Using device: {device}")

    # ===== LOAD MODEL (CACHED) =====
    @st.cache_resource(show_spinner="🧠 Loading embedding model...")
    def load_embedder():
        return SentenceTransformer(model_name, device=device)

    embedder = load_embedder()

    # ===== DATA PREP =====
    questions = df["question"].fillna("").astype(str).tolist()
    total = len(questions)

    if total == 0:
        print("⚠️ No data to embed")
        return None, None

    print(f"📊 Total questions: {total}")

    # ===== EMBEDDING STORAGE =====
    embeddings = []

    # ===== STREAMLIT PROGRESS =====
    progress_bar = st.progress(0)
    status_text = st.empty()

    # ===== BATCH PROCESSING =====
    for i in range(0, total, batch_size):
        batch = questions[i:i+batch_size]

        try:
            batch_embeddings = embedder.encode(
                batch,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True  # 🔥 KEY UPGRADE
            )

            embeddings.append(batch_embeddings)

        except Exception as e:
            print(f"⚠️ Batch {i} failed: {e}")
            continue

        # ===== UI UPDATE =====
        progress = min((i + batch_size) / total, 1.0)
        progress_bar.progress(progress)
        status_text.text(f"🧠 Processing {min(i+batch_size, total)}/{total}")

    # ===== FINAL ARRAY =====
    embeddings = np.vstack(embeddings)

    # ===== SAVE IN DF =====
    df["embedding"] = list(embeddings)

    # ===== STATS =====
    elapsed = round(time.time() - start_time, 2)

    print("\n" + "="*40)
    print("✅ EMBEDDING COMPLETE")
    print("="*40)
    print(f"📊 Total vectors : {len(embeddings)}")
    print(f"🧠 Dimension     : {embeddings.shape[1]}")
    print(f"⚡ Time          : {elapsed}s")
    print("="*40)

    st.success(f"✅ Embeddings generated ({len(embeddings)} items)")

    return embedder, embeddings


# ===== RUN =====
embedder, embeddings = generate_embeddings(df)

# ==============================
# OPTIONAL: Gemini Embedding Boost (for trending intelligence)
# ================= ULTRA ADVANCED GEMINI SETUP =================
import time

GEMINI_READY = False
gemini_model = None

def init_gemini():

    global GEMINI_READY, gemini_model

    # ===== LOAD KEY (SAFE) =====
    api_key = (st.secrets.get("GEMINI_API_KEY") or "").strip()

    if not genai:
        print("⚠️ Gemini library not available")
        return

    if not api_key:
        print("⚠️ GEMINI_API_KEY missing")
        return

    # ===== CONFIGURE =====
    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        print(f"❌ Gemini config failed: {e}")
        return

    # ===== MODEL FALLBACK LIST =====
    models_to_try = [
        "gemini-1.5-flash",
        "gemini-1.5-pro",
        "gemini-pro"
    ]

    # ===== MODEL INITIALIZATION =====
    for model_name in models_to_try:
        try:
            gemini_model = genai.GenerativeModel(model_name)

            # ===== TEST CALL =====
            test = gemini_model.generate_content("Hello", stream=False)

            if test:
                GEMINI_READY = True
                print(f"✅ Gemini ready using {model_name}")
                return

        except Exception as e:
            print(f"⚠️ {model_name} failed: {e}")
            time.sleep(0.3)

    # ===== FINAL FAILURE =====
    print("❌ No Gemini model available")
    GEMINI_READY = False


# ===== INIT ON START =====
init_gemini()

# ==============================
# ================= ULTRA ADVANCED MODEL SAVE =================
import os
import pickle
import hashlib
import time
import gzip
from datetime import datetime

def save_model_advanced(df, embedder, embeddings, path="model_advanced.pkl"):

    start_time = time.time()

    # ===== METADATA =====
    meta = {
        "version": "LoveBot-Pro-v3",
        "trained_on": datetime.now().isoformat(),
        "total_pairs": len(df),
        "embedding_dim": embeddings.shape[1],
        "model_name": getattr(embedder, "_model_card", "unknown"),
        "python_version": sys.version.split()[0],
    }

    # ===== MODEL OBJECT =====
    model_data = {
        "df": df,
        "embedder": embedder,
        "embeddings": embeddings,
        "meta": meta
    }

    # ===== BACKUP OLD MODEL =====
    if os.path.exists(path):
        backup_path = path.replace(".pkl", "_backup.pkl")
        os.replace(path, backup_path)
        print(f"🗂 Backup created → {backup_path}")

    # ===== SAVE (COMPRESSED) =====
    try:
        with gzip.open(path, "wb") as f:
            pickle.dump(model_data, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        print(f"❌ Save failed: {e}")
        return False

    # ===== FILE STATS =====
    file_size = os.path.getsize(path) / (1024 * 1024)

    # ===== HASH (INTEGRITY) =====
    try:
        with open(path, "rb") as f:
            file_hash = hashlib.md5(f.read()).hexdigest()[:12]
    except:
        file_hash = "unknown"

    # ===== LOAD TEST (VALIDATION) =====
    try:
        with gzip.open(path, "rb") as f:
            test_load = pickle.load(f)

        if "df" not in test_load or "embeddings" not in test_load:
            print("❌ Validation failed")
            return False

    except Exception as e:
        print(f"❌ Reload test failed: {e}")
        return False

    # ===== TIME =====
    elapsed = round(time.time() - start_time, 2)

    # ===== OUTPUT =====
    print("\n" + "="*60)
    print("🎉 LOVE BOT MODEL SAVED SUCCESSFULLY!")
    print("="*60)
    print(f"📊 Total Pairs        : {meta['total_pairs']}")
    print(f"🧠 Embedding Dim     : {meta['embedding_dim']}")
    print(f"⚡ Save Time         : {elapsed}s")
    print(f"💾 File Size         : {file_size:.2f} MB")
    print(f"🔑 Model Version     : {meta['version']}")
    print(f"🧬 File Hash         : {file_hash}")
    print(f"📁 Saved As          : {path}")
    print("="*60)

    return True


# ===== RUN SAVE =====
save_model_advanced(df, embedder, embeddings)