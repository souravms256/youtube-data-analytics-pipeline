import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
import pandas as pd
import plotly.express as px
import os
import json
from datetime import datetime

# Set wide layout
st.set_page_config(page_title="YouTube Firestore Analytics", layout="wide")

# ---------- Firebase Firestore Setup ----------
with st.spinner("📡 Collecting data..."):
    if "firebase" in st.secrets:
        firebase_creds = st.secrets["firebase"]
        credentials = service_account.Credentials.from_service_account_info(firebase_creds)
        project_id = firebase_creds["project_id"]
    else:
        key_path = os.path.join("config", "key.json")
        if not os.path.exists(key_path):
            st.error(f"Key file not found at {key_path}. Please check your path or configure Streamlit secrets.")
            st.stop()

        with open(key_path) as f:
            firebase_creds = json.load(f)

        credentials = service_account.Credentials.from_service_account_info(firebase_creds)
        project_id = firebase_creds["project_id"]

    db = firestore.Client(credentials=credentials, project=project_id)

    country_collections = ['USvideos', 'CAvideos', 'INvideos', 'DEvideos']

    @st.cache_data(show_spinner=False)
    def fetch_all_data():
        all_data = []
        for country in country_collections:
            docs = db.collection(country).stream()
            for doc in docs:
                record = doc.to_dict()
                record["region"] = country[:2].lower()
                all_data.append(record)
        if all_data:
            return pd.DataFrame(all_data)
        else:
            return pd.DataFrame()

    df = fetch_all_data()

if df.empty:
    st.warning("No data fetched from Firestore. Please check your database.")
    st.stop()

# ---------- Sidebar Filter Section ----------
st.sidebar.title("🔎 Filter Options")

categories = df["category_name"].dropna().unique() if "category_name" in df.columns else []
selected_category = st.sidebar.selectbox("Select Category", ["All"] + sorted(list(categories)))

# Robust timestamp parsing
if "publish_time" in df.columns:
    df["publish_time"] = pd.to_datetime(df["publish_time"], errors="coerce")

valid_dates = df["publish_time"].dropna()

selected_date = None
if not valid_dates.empty:
    selected_date = st.sidebar.date_input(
        "Select Publish Date",
        min_value=valid_dates.min().date(),
        max_value=valid_dates.max().date(),
        value=None
    )

# Button to override filters
use_complete_data = st.sidebar.checkbox("📋 Consider Complete Data (Ignore Filters)")

# ---------- Data Filtering ----------
filtered_df = df.copy()

# Apply filtering only if checkbox is NOT selected
if not use_complete_data:
    if selected_category != "All":
        filtered_df = filtered_df[filtered_df["category_name"] == selected_category]
    if selected_date:
        filtered_df = filtered_df[filtered_df["publish_time"].dt.date == selected_date]

# ---------- Main Dashboard Section ----------
st.title("🎬 YouTube Firestore Analytics Dashboard")
st.markdown("Get insights from YouTube trending data across **US**, **Canada**, **India**, and **Denmark**")

# Ensure numeric fields
for field in ['likes', 'dislikes', 'views']:
    if field not in filtered_df.columns:
        filtered_df[field] = 0
    else:
        filtered_df[field] = pd.to_numeric(filtered_df[field], errors='coerce').fillna(0)

# ---------- Graphs ----------

# Top 10 liked videos
likes_df = filtered_df.groupby("title", as_index=False)["likes"].sum().nlargest(10, "likes")
fig1 = px.bar(likes_df, x="likes", y="title", orientation="h", title="🔥 Top 10 Liked Videos", height=500)

# Top 10 viewed videos
views_title_df = filtered_df.groupby("title", as_index=False)["views"].sum().nlargest(10, "views")
fig2 = px.pie(views_title_df, values="views", names="title", hole=0.4, title="👀 Top Viewed Videos", height=500)

# Other graphs only for full data (or no filter)
full_analytics = (use_complete_data or (selected_category == "All" and not selected_date))

if full_analytics:
    views_region_df = filtered_df.groupby("region", as_index=False)["views"].sum()
    fig3 = px.pie(views_region_df, values="views", names="region", hole=0.3, title="🌍 Views by Region", height=500)

    views_category_df = filtered_df.groupby("category_name", as_index=False)["views"].sum()
    fig4 = px.pie(views_category_df, values="views", names="category_name", hole=0.3, title="📊 Views by Category", height=500)

    ratings_df = filtered_df.copy()
    ratings_df["rating"] = ratings_df["likes"] - ratings_df["dislikes"]
    ratings_category_df = ratings_df.groupby("category_name", as_index=False)["rating"].sum()
    fig5 = px.pie(ratings_category_df, values="rating", names="category_name", hole=0.3, title="⭐ Ratings by Category", height=500)

# ---------- Layout Rendering ----------
st.markdown("### 🔹 Overview Insights")

col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.plotly_chart(fig2, use_container_width=True)

# Show extra graphs only when complete data or no filters
if full_analytics:
    st.markdown("---")
    col3, col4 = st.columns(2)

    with col3:
        st.plotly_chart(fig3, use_container_width=True)
    with col4:
        st.plotly_chart(fig4, use_container_width=True)

    st.markdown("---")
    col5, col6 = st.columns(2)

    with col5:
        st.plotly_chart(fig5, use_container_width=True)

# ---------- Filter Info ----------
if not use_complete_data and (selected_category != "All" or selected_date):
    st.info("✅ Filters applied. Only relevant data shown based on your selection.")
