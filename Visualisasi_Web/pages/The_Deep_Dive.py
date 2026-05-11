import streamlit as st
import plotly.express as px
import pandas as pd

# Import utilitas sesuai struktur yang Anda berikan
from utils.hdfs_connection import read_csv_from_hdfs
from utils.ui import apply_dashboard_styles, chart_card, PALETTE, PALETTE_SCALE, style_figure

# 1. KONFIGURASI PATH HDFS (Halaman 3: Cross Analysis)
# Path disesuaikan dengan output dari script 03_Cross_Profiling.py
CROSS_PATHS = {
    "cross_matrix": "/Project_akhir/visualisasi_asean/cross_analysis/cross_matrix_utama",
    "digital_gap": "/Project_akhir/visualisasi_asean/cross_analysis/digital_gap_score_per_negara",
    "zona_kritis": "/Project_akhir/visualisasi_asean/cross_analysis/zona_kritis_c4_gmm",
    "gmm_dist": "/Project_akhir/visualisasi_asean/cross_analysis/gmm_distribusi_per_negara",
    "tech_v_gmm": "/Project_akhir/visualisasi_asean/cross_analysis/teknologi_vs_gmm_cluster"
}

def show_cross_analysis_page():
    apply_dashboard_styles()
    
    st.title("Analisis Lintas Model & Digital Gap")
    st.markdown("""
        Halaman ini menggabungkan hasil **K-Means (Geografis)** dan **GMM (Reliabilitas)** untuk mengidentifikasi area kritis dan skor kesenjangan digital di ASEAN.
    """)

    # --- 2. LOAD DATA DARI HDFS ---
    with st.spinner("Mengambil data Cross-Analysis dari HDFS..."):
        df_cross = read_csv_from_hdfs(CROSS_PATHS["cross_matrix"])
        df_gap = read_csv_from_hdfs(CROSS_PATHS["digital_gap"])
        df_kritis = read_csv_from_hdfs(CROSS_PATHS["zona_kritis"])
        df_tech_gmm = read_csv_from_hdfs(CROSS_PATHS["tech_v_gmm"])

    # Cek jika data berhasil dimuat
    if df_cross is None or df_gap is None:
        st.error("Gagal mengambil data dari HDFS. Pastikan script 03_Cross_Profiling.py sudah dijalankan.")
        return

    # --- 3. BARIS 1: DIGITAL GAP INDEX (Komponen Utama) ---
    st.subheader("1. ASEAN Digital Gap Index")
    with chart_card(title="ASEAN Digital Gap Index"):
        st.markdown("Ranking kesenjangan digital berdasarkan bobot teknologi, kualitas data, dan lokasi.")
        # Urutkan berdasarkan skor tertinggi (terburuk)
        df_gap_sorted = df_gap.sort_values("digital_gap_score", ascending=True)
        
        fig_gap = px.bar(
            df_gap_sorted,
            y="Country",
            x="digital_gap_score",
            orientation='h',
            color="digital_gap_score",
            color_continuous_scale=PALETTE_SCALE,
            labels={"digital_gap_score": "Skor Kesenjangan", "Country": "Negara"}
        )
        style_figure(fig_gap)
        st.plotly_chart(fig_gap, use_container_width=True)

        st.caption("Myanmar berada di posisi paling kritis dalam indeks ini. Hal ini disebabkan oleh kombinasi persentase GMM Abandoned (95.9%) yang sangat tinggi dan rendahnya penetrasi teknologi modern. Skor ini menunjukkan bahwa di Myanmar, infrastruktur tidak hanya terbatas secara jangkauan, tetapi data yang tersedia sudah sangat usang dan tidak andal.")

    # --- 4. BARIS 2: HEATMAP KORELASI & TEKNOLOGI ---
    col1, col2 = st.columns(2)

    with col1:
        with chart_card(title="Matriks Wilayah vs Kualitas"):
            st.subheader("Matriks Wilayah vs Kualitas")
            # Pivot untuk Heatmap: K-Means (prediction) vs GMM (gmm_cluster)
            z_data = df_cross.pivot(index='prediction', columns='gmm_cluster', values='tower_count').fillna(0)
            
            fig_heatmap = px.imshow(
                z_data,
                labels=dict(x="GMM Cluster (Kualitas)", y="K-Means Cluster (Wilayah)", color="Tower"),
                text_auto=True,
                color_continuous_scale=PALETTE_SCALE
            )
            style_figure(fig_heatmap)
            st.plotly_chart(fig_heatmap, use_container_width=True)
            st.caption("Meskipun sebagian besar menara di ASEAN berada di cluster wilayah yang stabil (Cluster 1), terdapat **kantong-kantong bahaya** di Cluster 4. Menara di wilayah terpencil ini seringkali memiliki data yang tidak diperbarui selama bertahun-tahun (usia data rata-rata mencapai 15 tahun/5.510 hari), yang berarti koordinat atau status operasional menara tersebut kemungkinan besar sudah tidak akurat lagi di lapangan")

    with col2:
        with chart_card(title="Korelasi Teknologi vs Keandalan"):
            st.subheader("Teknologi vs Keandalan")
            fig_tech = px.bar(
                df_tech_gmm,
                x="generasi",
                y="tower_count",
                color="gmm_cluster",
                barmode="group",
                color_discrete_sequence=PALETTE,
                title="Distribusi Kualitas Data per Generasi"
            )
            style_figure(fig_tech)
            st.plotly_chart(fig_tech, use_container_width=True)
            st.caption("Visualisasi ini membuktikan hipotesis bahwa teknologi tua berbanding lurus dengan data yang terbengkalai. Operator cenderung memprioritaskan pemeliharaan data pada aset 4G dan 5G. Sebaliknya, menara 2G dibiarkan tanpa pembaruan data (terjebak di GMM cluster 4), yang memperparah kesenjangan digital bagi pengguna di daerah pelosok yang masih bergantung pada sinyal 2G.")

    # --- 5. BARIS 3: TABEL ZONA KRITIS ---
    st.subheader("2. 🚨 Daftar Merah: Zona Kritis (C4 + GMM Terbengkalai)")
    st.markdown("""
        Daftar operator yang berada di wilayah klaster terpencil (C4) dengan profil data 
        paling tidak andal (SAM rendah & Usia data tua).
    """)
    with chart_card(title="Daftar Operator di Zona Kritis"):
        # Menampilkan tabel hasil filter zona kritis dari profiling
        st.dataframe(df_kritis, use_container_width=True)

    st.caption("Tabel ini adalah daftar prioritas untuk audit lapangan. Operator seperti Maxis di Malaysia memiliki volume menara **zombie** yang sangat besar di wilayah pelosok (C4). Angka Avg SAM yang rendah (1.08 - 2.92) menunjukkan bahwa selain datanya tua, menara-menara ini memiliki kekuatan sinyal yang lemah berdasarkan laporan sampel data terakhir, sehingga wilayah ini bisa dikategorikan sebagai true blank spot.")

    # --- 6. BARIS 4: DISTRIBUSI GMM PER NEGARA (TAMBAHAN) ---
    st.subheader("3. Distribusi Kualitas Data (GMM) per Negara")
    with chart_card(title="Proporsi Klaster Keandalan per Negara"):
        st.markdown("""
            Visualisasi ini menunjukkan 'kesehatan' data aset menara di tiap negara. 
            Negara dengan tumpukan warna **GMM Cluster 4** yang besar menunjukkan risiko data usang yang tinggi.
        """)
        
        # Load data distribusi GMM per negara
        df_gmm_dist = read_csv_from_hdfs(CROSS_PATHS["gmm_dist"])
        
        if df_gmm_dist is not None:
            # Membuat Stacked Bar Chart
            fig_gmm_dist = px.bar(
                df_gmm_dist,
                x="Country",
                y="tower_count",
                color="gmm_cluster",
                title="Distribusi Klaster GMM berdasarkan Negara",
                labels={"tower_count": "Jumlah Menara", "gmm_cluster": "Klaster GMM"},
                color_discrete_sequence=PALETTE,
                barmode="relative" # Membuat tumpukan (stacked)
            )
            
            style_figure(fig_gmm_dist)
            st.plotly_chart(fig_gmm_dist, use_container_width=True)
            st.caption("Indonesia secara kuantitas memiliki infrastruktur yang sangat besar dengan tingkat reliabilitas yang cukup terjaga di Cluster 0 dan 1. Namun, Vietnam menunjukkan efisiensi yang lebih tinggi di mana hampir seluruh menaranya terpusat pada satu standar kualitas data (Cluster 1), menunjukkan manajemen data aset yang lebih seragam secara nasional.")

# Eksekusi fungsi halaman
if __name__ == "__main__":
    show_cross_analysis_page()