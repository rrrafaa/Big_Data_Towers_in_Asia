import streamlit as st
from utils.ui import apply_dashboard_styles

st.set_page_config(layout="wide", page_title="Hierarki Cluster")
apply_dashboard_styles()

st.title("🎯 Hierarki Cluster")
st.info(
    "Visualisasi sunburst hierarki sekarang digabungkan ke halaman **K-Means** untuk menghindari duplikasi chart."
)
st.page_link("pages/k-means.py", label="Buka halaman K-Means", icon="📊")
