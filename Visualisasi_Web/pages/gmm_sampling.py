import streamlit as st
import plotly.express as px
import pandas as pd
# Import fungsi bawaan projekmu untuk baca HDFS
from utils.hdfs_connection import read_csv_from_hdfs 
from utils.ui import PALETTE, style_figure

# 1. Tambahkan path scatter sample HDFS ke kamus PATHS kamu
PATHS = {
    "operator": "/Project_akhir/visualisasi_asean/gmm_operator_reliability",
    "cluster": "/Project_akhir/visualisasi_asean/gmm_cluster_profile",
    "scatter_sample": "/Project_akhir/visualisasi_asean/gmm_scatter_sample" # <-- PATH BARU HDFS
}

# --- TARUH KODE SCATTER PLOT INI DI BAGIAN BAWAH DASHBOARD STREAMLIT KAMU ---
st.write("---")
st.subheader("🎯 Visualisasi Batasan (Boundary) Cluster GMM")
st.caption("Scatter plot interaktif ditarik langsung dari HDFS menggunakan sampel data untuk melihat batas operasional tiap cluster.")

with st.spinner("Mengambil data sampel scatter dari HDFS..."):
    # Gunakan fungsi hdfs_connection bawaan projekmu
    df_scatter_raw = read_csv_from_hdfs(PATHS["scatter_sample"])

if df_scatter_raw is not None and not df_scatter_raw.empty:
    # Standarkan nama kolom menjadi huruf kecil seperti fungsi bawaanmu
    df_scatter = df_scatter_raw.copy()
    df_scatter.columns = [c.lower() for c in df_scatter.columns]
    
    # Pastikan tipe data cluster dibaca sebagai string untuk pewarnaan kategori
    df_scatter["gmm_cluster"] = df_scatter["gmm_cluster"].astype(str)
    df_scatter = df_scatter.sort_values("gmm_cluster")

    # Mapping warna agar konsisten dengan warna PALETTE ui.py milikmu
    # Mengingat cluster bertipe string '0', '1', dst.
    PALETTE_MAP = {
        "0":  "#1f77b4",
        "1":  "#ff7f0e",
        "2":  "#2ca02c",
        "3":  "#d62728",
        "4":  "#9467bd"
    }

    # 2. Buat scatter plot interaktif menggunakan Plotly Express
    fig_scatter = px.scatter(
        df_scatter,
        x="data_age_days",
        y="sam",
        color="gmm_cluster",
        color_discrete_map=PALETTE_MAP,
        log_y=True,  # Skala logaritmik wajib agar visualisasi SAM tidak jomplang
        labels={
            "data_age_days": "Usia Data Pemeliharaan (Hari)",
            "sam": "Jumlah Sampel Sinyal (SAM) - Skala Log",
            "gmm_cluster": "GMM Cluster"
        },
        title="Sebaran Titik Batasan Cluster GMM (Data Terpusat di HDFS)",
        opacity=0.6
    )

    # 3. Tampilkan chart di Streamlit dengan style bawaan UI-mu
    st.plotly_chart(style_figure(fig_scatter), use_container_width=True)

else:
    st.warning("Data sampel scatter plot gagal diambil atau direktori di HDFS masih kosong.")