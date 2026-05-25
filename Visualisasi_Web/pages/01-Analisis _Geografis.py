import streamlit as st
import plotly.express as px
from utils.hdfs_connection import read_csv_from_hdfs
from utils.ui import apply_dashboard_styles, chart_card, PALETTE

st.set_page_config(page_title="Zonasi Geografis (K-Means)", layout="wide")
apply_dashboard_styles()

st.title("Analisis Geografis & Profiling Cluster K-Means")
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
    "area": "/Project_akhir/visualisasi_asean/profiling_cluster/Dominasi-Wilayah",
    "sample" : "/Project_akhir/visualisasi_asean/profiling_cluster/sample_map_tower"
}

# 1. Ambil semua data dari HDFS
df_stats = read_csv_from_hdfs(PATHS_KMEANS["stats"])
df_hier = read_csv_from_hdfs(PATHS_KMEANS["hierarchy"])
df_tech = read_csv_from_hdfs(PATHS_KMEANS["tech"])
df_area = read_csv_from_hdfs(PATHS_KMEANS["area"])
df_sample = read_csv_from_hdfs(PATHS_KMEANS["sample"])

# BAGIAN 1: PROFILING STATISTIK UTAMA (KPI Metrics & Unified Map Tabs)
st.subheader("Eksplorasi Spasial & Estimasi Makro Cluster")

if not df_stats.empty:
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
            
    st.write("#") 

    with chart_card("Peta Eksplorasi Spasial Telekomunikasi ASEAN", 
                    "Pilih tab di bawah untuk melihat pola makro (Centroid) atau sebaran langsung di lapangan (Riil/Detail)"):
        
        tab_peta_centroid, tab_peta_riil = st.tabs([
            "Peta Titik Pusat Koordinat (Centroid Makro)",
            "Peta Sebaran Riil Menara (Detail Sampel Terdistribusi)"
        ])
        
        # TAB 1: PETA CENTROID (Titik Pusat Koordinat Rata-rata per Cluster)
        with tab_peta_centroid:
            fig_map = px.scatter_mapbox(
                df_stats,
                lat="avg_lat",
                lon="avg_lon",
                size="total_tower",
                color="Cluster_Name",
                color_discrete_sequence=PALETTE,
                zoom=3.5,
                center=dict(lat=4.5, lon=108.0),
                mapbox_style="carto-positron",
                hover_data=["avg_range_radius", "avg_sample_count"]
            )
            fig_map.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=500)
            st.plotly_chart(fig_map, use_container_width=True)

        # TAB 2: PETA SEBARAN RIIL menggunakan sample
        with tab_peta_riil:
            if not df_sample.empty:
                df_sample["Cluster_Name"] = df_sample["prediction"].map(CLUSTER_LABELS)
                
                fig_real_map = px.scatter_mapbox(
                    df_sample,
                    lat="LAT",
                    lon="LON",
                    color="Cluster_Name",
                    color_discrete_sequence=PALETTE,
                    zoom=3.5,
                    center=dict(lat=4.5, lon=108.0),
                    mapbox_style="carto-positron",
                    hover_data=["Country", "Network"]
                )
                fig_real_map.update_traces(marker=dict(size=4, opacity=0.6))
                fig_real_map.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=500)
                st.plotly_chart(fig_real_map, use_container_width=True)
            else:
                st.warning("Data sampel peta sebaran riil belum tersedia di HDFS.")

else:
    st.warning("Data 'stats_utama' tidak ditemukan di HDFS.")

st.write("---")

main_col1, main_col2 = st.columns([1.3, 1.0]) 

# KOLOM KIRI: STRUKTUR HIERARKI KLASTER 
with main_col1:
    st.subheader("Struktur Hierarki Klaster")
    with chart_card("Visualisasi Interaktif Hierarki Menara Telekomunikasi ASEAN", 
                    "Klik pada lingkaran terdalam (Cluster) untuk membedah sebaran Negara, lalu klik Negara untuk melihat dominasi Operator Penanggung Jawab"):
        if not df_hier.empty:
            df_hier["Cluster_Name"] = df_hier["prediction"].map(CLUSTER_LABELS)
            
            fig_sunburst = px.sunburst(
                df_hier,
                path=["Cluster_Name", "Country", "Network"],
                values="count",
                color="Cluster_Name",
                color_discrete_sequence=PALETTE,
                branchvalues="total"
            )
            fig_sunburst.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=660) 
            st.plotly_chart(fig_sunburst, use_container_width=True)
        else:
            st.warning("Data 'Hierarki-Cluster-Lengkap' tidak ditemukan di HDFS.")

# KOLOM KANAN: PROFIL KOMPOSISI FITUR TEKNIS 
with main_col2:
    st.subheader("Profil Komposisi Fitur Teknis Klaster")
    
    # Chart Atas: Dominasi Teknologi Jaringan (Stacked Bar)
    with chart_card("Dominasi Teknologi Jaringan (Generasi Radio) per Cluster", 
                    "Komposisi kontribusi generasi teknologi (2G, 3G, 4G, 5G) di dalam masing-masing klaster"):
        if not df_tech.empty:
            df_tech["prediction"] = df_tech["prediction"].astype(str)
            fig_tech = px.bar(
                df_tech, 
                x="prediction", 
                y="count", \
                color="generasi", 
                barmode="stack", 
                color_discrete_sequence=PALETTE,
                labels={"prediction": "ID Cluster", "count": "Jumlah Menara", "generasi": "Teknologi"}
            )
            fig_tech.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=265)
            st.plotly_chart(fig_tech, use_container_width=True)
        else:
            st.warning("Data 'Dominasi-teknologi' tidak ditemukan di HDFS.")

    # Chart Bawah: Tipe Jangkauan Wilayah (Grouped Bar)
    with chart_card("Tipe Jangkauan Wilayah per Cluster", 
                    "Karakteristik jangkauan operasional menara berdasarkan wilayah Urban, Suburban, dan Rural"):
        if not df_area.empty:
            df_area["prediction"] = df_area["prediction"].astype(str)
            fig_area = px.bar(
                df_area, 
                x="prediction", 
                y="count", 
                color="jangkauan", \
                barmode="group", 
                color_discrete_sequence=PALETTE,
                labels={"prediction": "ID Cluster", "count": "Jumlah Menara", "jangkauan": "Tipe Wilayah"}
            )
            fig_area.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=265)
            st.plotly_chart(fig_area, use_container_width=True)
        else:
            st.warning("Data 'Dominasi-Wilayah' tidak ditemukan di HDFS.")

st.write("---")

# Tab Data Mentah HDFS
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