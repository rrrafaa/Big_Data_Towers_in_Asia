import streamlit as st
import plotly.express as px
from utils.hdfs_connection import read_csv_from_hdfs
from utils.ui import apply_dashboard_styles, chart_card, PALETTE

st.set_page_config(page_title="Zonasi Geografis (K-Means)", layout="wide")
apply_dashboard_styles()

st.title("🗺️ Analisis Geografis & Profiling Cluster K-Means")
st.caption("Eksplorasi Menyeluruh Karakteristik Spasial, Hierarki Operator, Jangkauan Wilayah, dan Teknologi Menara ASEAN")

# Definisikan nama klaster agar lebih informatif secara bisnis
CLUSTER_LABELS = {
    0: "Cluster 0 (Filipina / Urban Padat)",
    1: "Cluster 1 (Indonesia / Heterogen)",
    2: "Cluster 2 (Malaysia-Singapura / Modern)",
    3: "Cluster 3 (Mainland ASEAN / Rural-Suburban)",
    4: "Cluster 4 (Kawasan Perbatasan / Khusus)"
}

# Path HDFS 100% Sinkron dengan pipeline yang kamu cantumkan
PATHS_KMEANS = {
    "stats": "/Project_akhir/visualisasi_asean/profiling_cluster/stats_utama",
    "hierarchy": "/Project_akhir/visualisasi_asean/profiling_cluster/Hierarki-Cluster-Lengkap",
    "tech": "/Project_akhir/visualisasi_asean/profiling_cluster/Dominasi-teknologi",
    "area": "/Project_akhir/visualisasi_asean/profiling_cluster/Dominasi-Wilayah"
}

# 1. Ambil semua data dari HDFS
df_stats = read_csv_from_hdfs(PATHS_KMEANS["stats"])
df_hier = read_csv_from_hdfs(PATHS_KMEANS["hierarchy"])
df_tech = read_csv_from_hdfs(PATHS_KMEANS["tech"])
df_area = read_csv_from_hdfs(PATHS_KMEANS["area"])

# ==============================================================================
# BAGIAN 1: PROFILING STATISTIK UTAMA (Centroid Map & KPI Metrics)
# ==============================================================================
st.subheader("📍 1. Titik Tengah Spasial & Estimasi Makro Cluster")

if not df_stats.empty:
    # Buat mapping label pada dataframe stat agar seragam
    df_stats["Cluster_Name"] = df_stats["prediction"].map(CLUSTER_LABELS)
    
    # Tampilkan Ringkasan berupa Metric Box secara dinamis berdasarkan data HDFS
    col_metrics = st.columns(len(df_stats))
    for idx, row in df_stats.iterrows():
        with col_metrics[idx]:
            st.metric(
                label=f"C{int(row['prediction'])}: Total Menara",
                value=f"{int(row['total_tower']):,}",
                delta=f"Radius: {float(row['avg_range_radius']):.1f}m"
            )
            st.caption(f"Avg Sampel Sinyal: **{float(row['avg_sample_count']):.1f}**")
            
    # Visualisasi Peta Titik Tengah (Centroid) tiap klaster
    with chart_card("Peta Lokasi Pusat Koordinat (Centroid) Tiap Cluster", 
                     "Ukuran lingkaran mewakili volume total menara, posisi berdasarkan rata-rata LAT & LON klaster"):
        fig_map = px.scatter_mapbox(
            df_stats,
            lat="avg_lat",
            lon="avg_lon",
            size="total_tower",
            color="Cluster_Name",
            color_discrete_sequence=PALETTE,
            zoom=3,
            center=dict(lat=4.5, lon=108.0),
            mapbox_style="open-street-map",
            hover_data=["avg_range_radius", "avg_sample_count"]
        )
        fig_map.update_layout(margin=dict(l=0, r=0, t=30, b=0), height=450)
        st.plotly_chart(fig_map, use_container_width=True)
else:
    st.warning("Data 'stats_utama' tidak ditemukan di HDFS.")

st.write("---")

# ==============================================================================
# BAGIAN 2: PROFILING HIERARKI (Sunburst Chart: Cluster -> Country -> Network)
# ==============================================================================
st.subheader("🌳 2. Struktur Hierarki Klaster")

with chart_card("Visualisasi Interaktif Hierarki Menara Telekomunikasi ASEAN", 
                 "Klik pada lingkaran terdalam (Cluster) untuk membedah sebaran Negara, lalu klik Negara untuk melihat dominasi Operator Penanggung Jawab"):
    if not df_hier.empty:
        # Melakukan mapping label agar tampilan chart interaktif bersih
        df_hier["Cluster_Name"] = df_hier["prediction"].map(CLUSTER_LABELS)
        
        # Grafik Sunburst sangat efisien untuk menampilkan data agregat hierarkis berkategori besar
        fig_sunburst = px.sunburst(
            df_hier,
            path=["Cluster_Name", "Country", "Network"],
            values="count",
            color="Cluster_Name",
            color_discrete_sequence=PALETTE,
            branchvalues="total"
        )
        fig_sunburst.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=550)
        st.plotly_chart(fig_sunburst, use_container_width=True)
    else:
        st.warning("Data 'Hierarki-Cluster-Lengkap' tidak ditemukan di HDFS.")

st.write("---")

# ==============================================================================
# BAGIAN 3 & 4: PROFILING DOMINASI TEKNOLOGI & TIPE JANGKAUAN WILAYAH
# ==============================================================================
st.subheader("📊 3. Profil Komposisi Fitur Teknis Klaster")

c1, c2 = st.columns(2)

with c1:
    with chart_card("Dominasi Teknologi Jaringan (Generasi Radio) per Cluster", 
                     "Komposisi kontribusi generasi teknologi (2G, 3G, 4G) di dalam masing-masing klaster"):
        if not df_tech.empty:
            df_tech["prediction"] = df_tech["prediction"].astype(str)
            fig_tech = px.bar(
                df_tech, 
                x="prediction", 
                y="count", 
                color="generasi", 
                barmode="stack", 
                color_discrete_sequence=PALETTE,
                labels={"prediction": "ID Cluster", "count": "Jumlah Menara", "generasi": "Teknologi"}
            )
            st.plotly_chart(fig_tech, use_container_width=True)
        else:
            st.warning("Data 'Dominasi-teknologi' tidak ditemukan di HDFS.")

with c2:
    with chart_card("Tipe Jangkauan Wilayah per Cluster", 
                     "Karakteristik jangkauan operasional menara berdasarkan wilayah Urban, Suburban, dan Rural"):
        if not df_area.empty:
            df_area["prediction"] = df_area["prediction"].astype(str)
            fig_area = px.bar(
                df_area, 
                x="prediction", 
                y="count", 
                color="jangkauan", 
                barmode="group", 
                color_discrete_sequence=PALETTE,
                labels={"prediction": "ID Cluster", "count": "Jumlah Menara", "jangkauan": "Tipe Wilayah"}
            )
            st.plotly_chart(fig_area, use_container_width=True)
        else:
            st.warning("Data 'Dominasi-Wilayah' tidak ditemukan di HDFS.")

st.write("---")

# Tab Data Mentah HDFS (Diletakkan di paling bawah untuk kebutuhan audit/pengecekan data)
with st.expander("🔍 Lihat Struktur Data Mentah Langsung dari HDFS"):
    tab_stats, tab_hier, tab_tech, tab_area = st.tabs(["Stats Utama", "Hierarki Lengkap", "Teknologi", "Wilayah"])
    with tab_stats:
        st.dataframe(df_stats, use_container_width=True)
    with tab_hier:
        st.dataframe(df_hier, use_container_width=True)
    with tab_tech:
        st.dataframe(df_tech, use_container_width=True)
    with tab_area:
        st.dataframe(df_area, use_container_width=True)