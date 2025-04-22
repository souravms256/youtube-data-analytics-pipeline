import os
import pandas as pd
import chardet
import firebase_admin
from firebase_admin import credentials, firestore
import re

# ---------- 🔧 Encoding Detection ----------
def detect_encoding(file_path):
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read(100000))
    encoding = result['encoding']
    confidence = result['confidence']

    print(f"📄 {os.path.basename(file_path)} → {encoding} (confidence: {confidence})")

    if encoding is None or confidence < 0.5:
        print("⚠️  Low confidence. Falling back to 'latin1'")
        encoding = 'latin1'
    return encoding

# ---------- 📂 Load Function for Cleaned CSV ----------
def load_cleaned_csv(csv_path):
    print(f"\n📥 Loading cleaned CSV: {csv_path}")
    encoding = detect_encoding(csv_path)
    df = pd.read_csv(csv_path, encoding=encoding)
    print("📌 Columns in cleaned CSV:", df.columns.tolist())
    return df

# ---------- 🔥 Firestore Upload ----------
def upload_to_firestore(collection_name, df):
    for _, row in df.iterrows():
        doc = row.dropna().to_dict()
        db.collection(collection_name).add(doc)
    print(f"✅ Uploaded {len(df)} documents to '{collection_name}'")

# ---------- 🗂 Paths ----------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLEANED_DIR = os.path.join(BASE_DIR, "cleaned")
FIREBASE_KEY = os.path.join(BASE_DIR, "config", "key.json")

# Limit to only 3 countries excluding US
selected_countries = ['CA', 'DE', 'IN']

# Regex to match titles starting with A–Z (case-insensitive)
alphabet_pattern = re.compile(r'^[A-Za-z]')

# ---------- 🔐 Firebase Initialization ----------
cred = credentials.Certificate(FIREBASE_KEY)
firebase_admin.initialize_app(cred)
db = firestore.client()

# ---------- 🔄 Upload Each Filtered File ----------
for code in selected_countries:
    try:
        csv_path = os.path.join(CLEANED_DIR, f"{code}videos_cleaned.csv")
        df = load_cleaned_csv(csv_path)

        # Filter: Titles that start with an alphabet
        df = df[df['title'].apply(lambda x: bool(alphabet_pattern.match(str(x))))]

        # Limit to 1000 records
        df = df.head(1000)

        upload_to_firestore(f"{code}videos", df)
    except Exception as e:
        print(f"❌ Failed to upload {code}: {e}")

print("\n🚀 Done! Filtered datasets uploaded to Firestore.")
