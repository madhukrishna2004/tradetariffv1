import pandas as pd
import openai
import faiss
import numpy as np
from tqdm import tqdm

# ==== CONFIG ====
EXCEL_FILE = "global-uk-tariff.xlsx"
PICKLE_OUTPUT = "hs_code_data.pkl"
FAISS_OUTPUT = "hs_code_index.faiss"
EMBEDDING_MODEL = "text-embedding-3-small"
API_KEY = "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"
BATCH_SIZE = 100  # Safe range for OpenAI
# =================

openai.api_key = API_KEY

# Step 1: Load Excel
print("📥 Loading Excel file...")
try:
    df = pd.read_excel(EXCEL_FILE)
    print(f"✅ Loaded {len(df)} rows from Excel.")
except Exception as e:
    print(f"❌ Failed to load Excel file: {e}")
    exit()

# Step 2: Prepare text
if "description" not in df.columns:
    print("❌ 'description' column not found in Excel.")
    exit()

descriptions = df["description"].fillna("").astype(str).tolist()

# Step 3: Batch Embeddings
print("🔁 Creating embeddings in batches...")
embeddings = []

for i in tqdm(range(0, len(descriptions), BATCH_SIZE), desc="🔄 Embedding progress (batched)", unit="batch"):
    batch_texts = descriptions[i:i+BATCH_SIZE]
    try:
        response = openai.Embedding.create(
            input=batch_texts,
            model=EMBEDDING_MODEL
        )
        batch_embeddings = [item['embedding'] for item in response['data']]
        embeddings.extend(batch_embeddings)
    except Exception as e:
        print(f"⚠️ Batch {i}-{i+BATCH_SIZE} failed: {e}")
        for _ in batch_texts:
            embeddings.append([0]*1536)

# Step 4: Save Pickle
try:
    df.to_pickle(PICKLE_OUTPUT)
    print(f"✅ Pickle saved: {PICKLE_OUTPUT}")
except Exception as e:
    print(f"❌ Error saving Pickle: {e}")

# Step 5: Build FAISS Index
try:
    embedding_matrix = np.array(embeddings).astype("float32")
    dimension = len(embedding_matrix[0])

    index = faiss.IndexFlatL2(dimension)
    index.add(embedding_matrix)
    faiss.write_index(index, FAISS_OUTPUT)
    print(f"✅ FAISS index saved: {FAISS_OUTPUT}")
except Exception as e:
    print(f"❌ FAISS build failed: {e}")

print("🚀 All done in ultra speed.")
