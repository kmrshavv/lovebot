import os
import sys
import json
import gzip
import time
import pickle
import hashlib
import warnings
import numpy as np
import pandas as pd
from datetime import datetime

warnings.filterwarnings("ignore")

# ================= IMPORTS =================
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("⚠️ PyTorch not found — defaulting to CPU")

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    raise ImportError("❌ sentence-transformers required: pip install sentence-transformers")

try:
    import google.generativeai as genai
except ImportError:
    genai = None
    print("⚠️ google-generativeai not found — Gemini disabled")

# ================= LOAD CSV =================
def load_csv(path):
    try:
        df = pd.read_csv(path, on_bad_lines="skip", encoding="utf-8")
        print(f"✅ Loaded {path}: {len(df)} rows")
        return df
    except Exception as e:
        print(f"⚠️ Could not load {path}: {e}")
        return pd.DataFrame()

df1 = load_csv("data/chatbot.csv")
df2 = load_csv("data/data.csv")

# ================= LOAD JSON =================
json_rows = []
try:
    with open("data/chatbot.json", encoding="utf-8") as f:
        content = f.read().strip()

    if content.startswith("["):
        data = json.loads(content)
    else:
        data = [json.loads(line) for line in content.splitlines() if line.strip()]

    for item in data:
        json_rows.append({
            "question":   str(item.get("question", "")).strip(),
            "answer":     str(item.get("answer",   "")).strip(),
            "love_score": float(item.get("love_score", 85)),
            "emotion":    item.get("emotion", "love"),
            "timestamp":  datetime.now().isoformat(),
        })
    print(f"✅ Loaded chatbot.json: {len(json_rows)} rows")

except FileNotFoundError:
    print("⚠️ chatbot.json not found — skipping")
except Exception as e:
    print(f"⚠️ JSON loading error: {e}")

df3 = pd.DataFrame(json_rows) if json_rows else pd.DataFrame()

# ================= COMBINE + CLEAN =================
df = pd.concat([df1, df2, df3], ignore_index=True)

for col in ["question", "answer"]:
    if col not in df.columns:
        df[col] = ""

df = df[["question", "answer"]].copy()
df = df.dropna(subset=["question", "answer"])
df = df[df["question"].str.strip().str.len() > 3]
df = df[df["answer"].str.strip().str.len() > 0]

df["question"] = df["question"].str.strip().str.lower()
df["answer"]   = df["answer"].str.strip()

# Remove duplicates
df = df.drop_duplicates(subset=["question"]).reset_index(drop=True)

print(f"\n📊 Total cleaned pairs: {len(df)}")

if len(df) == 0:
    raise ValueError("❌ No data after cleaning — check your CSV/JSON files.")

# ================= EMBEDDINGS =================
def generate_embeddings(df, model_name="all-MiniLM-L6-v2", batch_size=64):
    start_time = time.time()

    device = "cuda" if (TORCH_AVAILABLE and torch.cuda.is_available()) else "cpu"
    print(f"⚡ Using device: {device}")

    print(f"🔄 Loading embedding model: {model_name}")
    embedder = SentenceTransformer(model_name, device=device)

    questions = df["question"].fillna("").astype(str).tolist()
    total     = len(questions)
    print(f"📊 Embedding {total} questions...")

    embeddings = []

    for i in range(0, total, batch_size):
        batch = questions[i : i + batch_size]
        try:
            batch_emb = embedder.encode(
                batch,
                show_progress_bar=False,
                convert_to_numpy=True,
                normalize_embeddings=True,
            )
            embeddings.append(batch_emb)
        except Exception as e:
            print(f"⚠️ Batch {i} failed: {e}")
            continue

        done = min(i + batch_size, total)
        print(f"  ↳ {done}/{total} ({100*done//total}%)", end="\r")

    print()  # newline after progress

    if not embeddings:
        raise RuntimeError("❌ All embedding batches failed.")

    embeddings = np.vstack(embeddings)

    elapsed = round(time.time() - start_time, 2)
    print(f"\n✅ Embeddings complete — {len(embeddings)} vectors, dim {embeddings.shape[1]}, {elapsed}s")

    return embedder, embeddings


embedder, embeddings = generate_embeddings(df)

# ================= GEMINI INIT (OPTIONAL) =================
GEMINI_READY = False
gemini_model = None

def init_gemini():
    global GEMINI_READY, gemini_model

    if genai is None:
        print("⚠️ Gemini library not available — skipping")
        return

    api_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("⚠️ GEMINI_API_KEY not set in environment — skipping Gemini")
        return

    try:
        genai.configure(api_key=api_key)
    except Exception as e:
        print(f"❌ Gemini config failed: {e}")
        return

    for model_name in ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-pro"]:
        try:
            model = genai.GenerativeModel(model_name)
            test  = model.generate_content("Hello", stream=False)
            if test:
                gemini_model = model
                GEMINI_READY = True
                print(f"✅ Gemini ready: {model_name}")
                return
        except Exception as e:
            print(f"⚠️ {model_name} failed: {e}")
            time.sleep(0.3)

    print("❌ No Gemini model available")

init_gemini()

# ================= SAVE MODEL =================
def save_model(df, embedder, embeddings, path="model_advanced.pkl"):
    start_time = time.time()

    meta = {
        "version":        "LoveBot-Pro-v3",
        "trained_on":     datetime.now().isoformat(),
        "total_pairs":    len(df),
        "embedding_dim":  int(embeddings.shape[1]),
        "python_version": sys.version.split()[0],
    }

    model_data = {
        "df":         df,
        "embedder":   embedder,
        "embeddings": embeddings,
        "meta":       meta,
    }

    # Backup existing model
    if os.path.exists(path):
        backup = path.replace(".pkl", "_backup.pkl")
        os.replace(path, backup)
        print(f"🗂 Backup saved → {backup}")

    # Save compressed with gzip (matches load_model in app.py)
    try:
        with gzip.open(path, "wb") as f:
            pickle.dump(model_data, f, protocol=pickle.HIGHEST_PROTOCOL)
    except Exception as e:
        print(f"❌ Save failed: {e}")
        return False

    # Validate by reloading
    try:
        with gzip.open(path, "rb") as f:
            test_load = pickle.load(f)
        if not all(k in test_load for k in ["df", "embeddings", "embedder"]):
            print("❌ Validation failed — missing keys")
            return False
    except Exception as e:
        print(f"❌ Reload validation failed: {e}")
        return False

    # Stats
    file_size = os.path.getsize(path) / (1024 * 1024)
    elapsed   = round(time.time() - start_time, 2)
    try:
        with open(path, "rb") as f:
            file_hash = hashlib.md5(f.read()).hexdigest()[:12]
    except Exception:
        file_hash = "unknown"

    print("\n" + "=" * 60)
    print("🎉 MODEL SAVED SUCCESSFULLY!")
    print("=" * 60)
    print(f"📊 Total Pairs    : {meta['total_pairs']}")
    print(f"🧠 Embedding Dim  : {meta['embedding_dim']}")
    print(f"⚡ Save Time      : {elapsed}s")
    print(f"💾 File Size      : {file_size:.2f} MB")
    print(f"🔑 Version        : {meta['version']}")
    print(f"🧬 File Hash      : {file_hash}")
    print(f"📁 Saved To       : {path}")
    print("=" * 60)

    return True


# ================= LOAD MODEL (used by app.py) =================
def load_model(path="model_advanced.pkl"):
    """Load the saved model. Called by app.py at runtime."""
    if not os.path.exists(path):
        print(f"⚠️ Model not found at {path}")
        return None
    try:
        with gzip.open(path, "rb") as f:
            data = pickle.load(f)

        # Normalize embeddings if not already done
        emb   = data["embeddings"]
        norms = np.linalg.norm(emb, axis=1, keepdims=True) + 1e-8
        data["embeddings"] = emb / norms

        print(f"✅ Model loaded — {len(data['df'])} rows")
        return data
    except Exception as e:
        print(f"❌ Load failed: {e}")
        return None


# ================= RUN =================
save_model(df, embedder, embeddings)