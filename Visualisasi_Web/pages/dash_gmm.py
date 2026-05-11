import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Set Page Config
st.set_page_config(page_title="GMM Reliability Dashboard", layout="wide")

st.title("📊 Analisis Keandalan Data Menara (GMM)")
st.markdown("---")

# 1. LOAD DATA
# Gantilah path ini dengan lokasi file CSV hasil profiling Anda
try:
    df_cluster = pd.read_csv('gmm_cluster_profile.csv')
    df_operator = pd.read_csv('gmm_operator_reliability.csv')
except:
    st.error("File CSV tidak ditemukan. Pastikan sudah mengunduh hasil profiling dari HDFS.")
    st.stop()

# --- BAGIAN 1: PROFIL KARAKTERISTIK CLUSTER ---
st.header("1) Karakteristik Cluster (Akurasi vs Kebaruan)")
col1, col2 = st.columns([1, 2])

with col1:
    st.write("Tabel Rata-rata per Cluster")
    st.dataframe(df_cluster.style.highlight_max(axis=0, subset=['avg_sam']))

with col2:
    # Visualisasi Bar Chart Ganda
    fig_cluster = px.bar(
        df_cluster, 
        x="gmm_cluster", 
        y=["avg_sam", "avg_days_old"],
        barmode="group",
        title="Perbandingan Sampel (SAM) vs Usia Data (Hari)",
        labels={"value": "Skala Nilai", "variable": "Metrik"},
        color_discrete_sequence=["#00CC96", "#EF553B"]
    )
    st.plotly_chart(fig_cluster, use_container_width=True)

st.info("""
**Cara Membaca:** - Cluster dengan **avg_sam Tinggi** dan **avg_days_old Rendah** = Data Sangat Andal (Gold).
- Cluster dengan **avg_sam Rendah** dan **avg_days_old Tinggi** = Data Usang (Legacy).
""")

# --- BAGIAN 2: PERINGKAT OPERATOR & NEGARA ---
st.header("2) Distribusi Keandalan per Operator")

# Filter Negara
countries = df_operator['Country'].unique().tolist()
selected_country = st.multiselect("Pilih Negara:", countries, default=countries[:2])

# Filter Data berdasarkan Negara
df_filtered = df_operator[df_operator['Country'].isin(selected_country)]

# Visualisasi Stacked Bar Chart
fig_op = px.bar(
    df_filtered,
    x="Network",
    y="tower_count",
    color="gmm_cluster",
    title=f"Proporsi Cluster per Operator di {', '.join(selected_country)}",
    labels={"tower_count": "Jumlah Menara", "gmm_cluster": "ID Cluster"},
    barmode="relative", # Bisa diganti "group" atau "stack"
    color_continuous_scale=px.colors.sequential.Viridis
)

st.plotly_chart(fig_op, use_container_width=True)

# --- BAGIAN 3: TREEMAP (HIERARKI) ---
st.header("3) Hierarki Keandalan: Negara > Operator > Cluster")
fig_tree = px.treemap(
    df_filtered, 
    path=['Country', 'Network', 'gmm_cluster'], 
    values='tower_count',
    color='gmm_cluster',
    color_continuous_scale='RdYlGn_r' # Merah ke Hijau (Terbalik)
)
st.plotly_chart(fig_tree, use_container_width=True)