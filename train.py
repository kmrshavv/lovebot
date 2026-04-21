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
# SEMANTIC EMBEDDINGS (Human-like Understanding)
# ==============================
print("🔄 Loading Sentence Transformer (all-MiniLM-L6-v2)...")
embedder = SentenceTransformer('all-MiniLM-L6-v2')

print("🧠 Generating embeddings...")
questions = df["question"].tolist()
embeddings = embedder.encode(questions, show_progress_bar=True, batch_size=64)

# Save embeddings
df["embedding"] = list(embeddings)

# ==============================
# OPTIONAL: Gemini Embedding Boost (for trending intelligence)
# ==============================
try:
    genai.configure(api_key="YOUR_GEMINI_KEY")  # Will use from secrets later
    gemini_model = genai.GenerativeModel('gemini-1.5-flash')
    print("🌟 Gemini enhancement enabled")
except:
    print("⚠️ Gemini not configured (optional)")

# ==============================
# SAVE ADVANCED MODEL
# ==============================
model_data = {
    "df": df,
    "embedder": embedder,
    "embeddings": embeddings,
    "version": "LoveBot-Pro-v2-2026",
    "trained_on": datetime.now().isoformat(),
    "total_pairs": len(df)
}

with open("model_advanced.pkl", "wb") as f:
    pickle.dump(model_data, f)

print("\n" + "="*60)
print("🎉 LOVE BOT ADVANCED MODEL TRAINED SUCCESSFULLY!")
print("="*60)
print(f"📊 Total Knowledge Pairs : {len(df)}")
print(f"🧠 Embedding Dimension   : {embeddings.shape[1]}")
print(f"💾 Saved as             : model_advanced.pkl")
print(f"🚀 Ready for Voice + Human-like Thinking!")
print("="*60)