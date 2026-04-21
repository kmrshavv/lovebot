import pandas as pd
import json
import pickle
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import LinearRegression

# ==============================
# LOAD CSV FILES
# ==============================
def load_csv(path):
    try:
        df = pd.read_csv(path, on_bad_lines='skip')
        print(f"Loaded {path}:", len(df))
        return df
    except Exception as e:
        print(f"Error loading {path}:", e)
        return pd.DataFrame()

df1 = load_csv("data/chatbot.csv")
df2 = load_csv("data/data.csv")

# ==============================
# LOAD JSON FILE (ALL FORMATS)
# ==============================
json_rows = []

try:
    with open("data/chatbot.json") as f:
        try:
            # Case 1: JSON list
            data = json.load(f)
            for item in data:
                json_rows.append({
                    "question": item.get("question", ""),
                    "answer": item.get("answer", ""),
                    "love_score": item.get("love_score", 90)
                })
        except:
            # Case 2: Line-by-line JSON
            f.seek(0)
            for line in f:
                try:
                    item = json.loads(line)
                    json_rows.append({
                        "question": item.get("question", ""),
                        "answer": item.get("answer", ""),
                        "love_score": item.get("love_score", 90)
                    })
                except:
                    continue

except Exception as e:
    print("Error loading JSON:", e)

df3 = pd.DataFrame(json_rows)
print("Loaded JSON:", len(df3))

# ==============================
# COMBINE ALL DATA
# ==============================
df = pd.concat([df1, df2, df3], ignore_index=True)

# ==============================
# CLEAN DATA
# ==============================
required_cols = ["question", "answer", "love_score"]

for col in required_cols:
    if col not in df.columns:
        df[col] = ""

df = df[required_cols]

# Convert types
df["question"] = df["question"].astype(str).str.strip()
df["answer"] = df["answer"].astype(str).str.strip()
df["love_score"] = pd.to_numeric(df["love_score"], errors="coerce")

# Remove bad rows
df = df.dropna()
df = df[df["question"].str.len() > 2]  # remove empty questions
df = df[df["question"].str.contains("[a-zA-Z]", regex=True)]  # keep real text

print("Total dataset after cleaning:", len(df))

# Debug check
print("\nSample questions:")
print(df["question"].head(5))

# ==============================
# TRAIN MODEL
# ==============================
vectorizer = CountVectorizer(stop_words="english")

X = vectorizer.fit_transform(df["question"])
y = df["love_score"]

# Safety check
if X.shape[1] == 0:
    print("❌ ERROR: No valid text data found. Fix your dataset.")
    exit()

model = LinearRegression()
model.fit(X, y)

# ==============================
# SAVE MODEL
# ==============================
with open("model.pkl", "wb") as f:
    pickle.dump((model, vectorizer, df), f)

print("\n✅ Model trained successfully ❤️")