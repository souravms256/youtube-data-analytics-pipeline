import pandas as pd
import json
import firebase_admin
from firebase_admin import credentials, firestore

# Paths
JP_CSV = '../data/JPvideos.csv'
KR_CSV = '../data/KRvideos.csv'
JP_JSON = '../data/JP_category_id.json'
KR_JSON = '../data/KR_category_id.json'

def load_category(json_path):
    with open(json_path) as f:
        data = json.load(f)
    return pd.DataFrame([
        {"id": int(item["id"]), "title": item["snippet"]["title"]}
        for item in data["items"] if item["snippet"]["assignable"]
    ])

def load_and_merge(csv_path, category_df):
    df = pd.read_csv(csv_path)
    df['categoryId'] = df['categoryId'].astype(int)
    return df.merge(category_df, left_on='categoryId', right_on='id', how='left')

def upload_to_firestore(collection_name, df):
    for _, row in df.iterrows():
        doc = row.dropna().to_dict()
        db.collection(collection_name).add(doc)

# Initialize Firebase
cred = credentials.Certificate("../firebase-key.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Load and upload JP data
jp_categories = load_category(JP_JSON)
jp_df = load_and_merge(JP_CSV, jp_categories)
upload_to_firestore("JPvideos", jp_df)

# Load and upload KR data
kr_categories = load_category(KR_JSON)
kr_df = load_and_merge(KR_CSV, kr_categories)
upload_to_firestore("KRvideos", kr_df)

print("✅ Data uploaded to Firebase Firestore.")
