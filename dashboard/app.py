import streamlit as st
from google.cloud import firestore
from google.oauth2 import service_account
import pandas as pd
import plotly.express as px

# Set wide layout
st.set_page_config(page_title="YouTube Firestore Analytics", layout="wide")

# Display progress message
with st.spinner("📡 Collecting data..."):
    # Load credentials from Streamlit secrets
    firebase_creds = st.secrets["firebase"]
    credentials = service_account.Credentials.from_service_account_info(firebase_creds)

    # Initialize Firestore DB
    db = firestore.Client(credentials=credentials, project=firebase_creds["project_id"])

    # Country-wise collections
    country_collections = ['USvideos', 'CAvideos', 'INvideos', 'DEvideos']

    @st.cache_data
    def fetch_all_data():
        all_data = []
        for country in country_collections:
            docs = db.collection(country).stream()
            for doc in docs:
                record = doc.to_dict()
                record["region"] = country[:2].lower()
                all_data.append(record)
        return pd.DataFrame(all_data)

    df = fetch_all_data()

# Title and header
st.title("🎬 YouTube Firestore Analytics Dashboard")
st.markdown("Get insights from YouTube trending data across **US**, **Canada**, **India**, and **Denmark**")

# ------------- Graphs Preparation ----------------
likes_df = df.groupby("title")["likes"].sum().nlargest(10).reset_index()
fig1 = px.bar(likes_df, x="likes", y="title", orientation="h", title="🔥 Top 10 Liked Videos", height=500)

dislikes_df = df.groupby("category_id")["dislikes"].sum().reset_index()
fig2 = px.pie(dislikes_df, values="dislikes", names="category_id", hole=0.4, title="👎 Dislikes by Category", height=500)

ratings_disabled_df = df[df["ratings_disabled"] == True].groupby("title").size().nlargest(10).reset_index(name="count")
fig3 = px.bar(ratings_disabled_df, x="count", y="title", orientation="h", title="❌ Ratings Disabled (Top Videos)", height=500)

views_title_df = df.groupby("title")["views"].sum().nlargest(10).reset_index()
fig4 = px.pie(views_title_df, values="views", names="title", hole=0.4, title="👀 Top Viewed Videos", height=500)

views_region_df = df.groupby("region")["views"].sum().reset_index()
fig5 = px.pie(views_region_df, values="views", names="region", title="🌍 Views by Region", height=500)

# ----------- Layout Rendering -------------
st.markdown("### 🔹 Overview Insights")

col1, col2, col3 = st.columns([1, 1, 1])

with col1:
    st.plotly_chart(fig1, use_container_width=True)

with col2:
    st.plotly_chart(fig2, use_container_width=True)

with col3:
    st.plotly_chart(fig3, use_container_width=True)

st.markdown("---")

col4, col5 = st.columns([1, 1])

with col4:
    st.plotly_chart(fig4, use_container_width=True)

with col5:
    st.plotly_chart(fig5, use_container_width=True)
