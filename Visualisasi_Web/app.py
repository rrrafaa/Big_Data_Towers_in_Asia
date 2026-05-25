import streamlit as st
import plotly.express as px
from utils.hdfs_connection import read_csv_from_hdfs
from utils.ui import apply_dashboard_styles, chart_card, PALETTE

st.set_page_config(page_title="Big Data ASEAN Dashboard", layout="wide")
apply_dashboard_styles()

st.title("Dashboard Infrastruktur Telekomunikasi ASEAN")
st.caption("Analisis Big Data Berbasis Spark untuk Pemetaan dan Prediksi Menara Seluler")

st.markdown(
    """
    <div class="dashboard-hero">
        <h2>Deskripsi Proyek</h2>
        <p>
            Dashboard interaktif ini menyajikan wawasan mendalam hasil pengolahan data masif (Big Data) 
            menara telekomunikasi di kawasan ASEAN. Melalui integrasi penyimpanan <b>HDFS (Hadoop Distributed File System)</b> 
            dan pemrosesan <b>Apache Spark</b>, proyek ini berhasil memetakan karakteristik wilayah, mengukur tingkat 
            keandalan data, serta membangun kecerdasan buatan untuk klasifikasi otomatis menara.
        </p>
        <p><b>Metodologi Pipeline Machine Learning yang Digunakan:</b></p>
        <ul>
            <li><b>K-Means Clustering:</b> Melakukan segmentasi geografis dan zonasi jangkauan wilayah menara.</li>
            <li><b>Gaussian Mixture Model (GMM):</b> Menganalisis keandalan data berdasarkan usia pembaruan dan kualitas sinyal.</li>
            <li><b>Random Forest Classifier:</b> Memprediksi kategori zona menara murni menggunakan spesifikasi teknis (independen dari koordinat spasial).</li>
        </ul>
    </div>
    """,
    unsafe_allow_html=True,
)

# SEKTOR 1: ANALISIS MAKRO REGIONAL ASEAN (ANALISIS DASAR SINKRON DENGAN HDFS)
st.write("---")
st.header("Analisis Deskriptif Dasar (Eksplorasi Pra-Pemodelan)")
st.markdown("Berikut merupakan visualisasi makro struktur menara telekomunikasi di ASEAN dari data bersih HDFS sebelum dieksekusi oleh pipeline *Machine Learning*.")

# --- BARIS 1: TOP 10 OPERATOR & PERSENTASE TEKNOLOGI ---
row1_col1, row1_col2 = st.columns([2, 1])

with row1_col1:
    path_top10 = "/Project_akhir/visualisasi_asean/top10_operator_asean"
    df_top10 = read_csv_from_hdfs(path_top10)
    
    with chart_card("Top 10 Raksasa Provider Telekomunikasi di ASEAN", "Berdasarkan jumlah total menara regional"):
        if not df_top10.empty:
            fig_top10 = px.bar(
                df_top10,
                x="total_menara_asean",
                y="Network",
                color="Negara_Dominan",
                orientation='h',
                color_discrete_sequence=PALETTE,
                labels={"total_menara_asean": "Jumlah Menara", "Network": "Operator Seluler"}
            )
            fig_top10.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=20, r=20, t=20, b=20), height=350)
            st.plotly_chart(fig_top10, use_container_width=True)
        else:
            st.info("Data Top 10 Operator belum tersedia di HDFS.")

with row1_col2:
    path_radio = "/Project_akhir/visualisasi_asean/overall_radio_percentage"
    df_radio = read_csv_from_hdfs(path_radio)
    
    with chart_card("Komposisi Standar Teknologi Radio", "Distribusi pemancar seluler di regional ASEAN"):
        if not df_radio.empty:
            # Menggunakan kolom dari tech_overall_final: 'radio' dan 'percentage' / 'count'
            fig_radio = px.pie(
                df_radio,
                names="generasi",
                values="count",
                hole=0.4,
                color_discrete_sequence=PALETTE
            )
            fig_radio.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=350)
            st.plotly_chart(fig_radio, use_container_width=True)
        else:
            st.info("Data persentase radio belum tersedia di HDFS.")


# SUNBURST OPERATOR & TOP OPERATOR PER NEGARA
row2_col1, row2_col2 = st.columns([1, 1])

with row2_col1:
    path_sunburst = "/Project_akhir/visualisasi_asean/sunburst_asean_operator"
    df_sunburst = read_csv_from_hdfs(path_sunburst)
    
    with chart_card("Struktur Hierarki Pasar Seluler ASEAN", "Hubungan Negara - Operator Dominan - Jenis Pemancar"):
        if not df_sunburst.empty:
            fig_sun = px.sunburst(
                df_sunburst,
                path=["region", "Country", "Network"],
                values="tower_count",
                color_discrete_sequence=PALETTE
            )
            fig_sun.update_layout(margin=dict(l=10, r=10, t=10, b=10), height=400)
            st.plotly_chart(fig_sun, use_container_width=True)
        else:
            st.info("Data sunburst operator belum tersedia di HDFS.")

with row2_col2:
    path_top3 = "/Project_akhir/visualisasi_asean/top3_operator_per_negara"
    df_top3 = read_csv_from_hdfs(path_top3)
    
    with chart_card("Top 3 Operator Penguasa Menara Per Negara", "Perbandingan dominasi market share infrastruktur lokal"):
        if not df_top3.empty:
            fig_top3 = px.bar(
                df_top3,
                x="Country",
                y="tower_count",
                color="Network",
                barmode="group",
                color_discrete_sequence=PALETTE,
                labels={"tower_count": "Jumlah Menara", "Country": "Negara"}
            )
            fig_top3.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=400)
            st.plotly_chart(fig_top3, use_container_width=True)
        else:
            st.info("Data Top 3 Operator per negara belum tersedia di HDFS.")


# TREN PERTUMBUHAN TAHUNAN & RASIO MODERNISASI
row3_col1, row3_col2 = st.columns([1, 1])

with row3_col1:
    path_growth = "/Project_akhir/visualisasi_asean/pertumbuhan_tahunan"
    df_growth = read_csv_from_hdfs(path_growth)
    
    with chart_card("Tren Pertumbuhan dan Registrasi Menara Tahunan", "Kurva riwayat penambahan infrastruktur baru"):
        if not df_growth.empty:
            # Urutkan berdasarkan tahun agar garis tidak berantakan
            df_growth = df_growth.sort_values(by="created_year")
            fig_growth = px.line(
                df_growth,
                x="created_year",
                y="count",
                markers=True,
                color_discrete_sequence=[PALETTE[0]],
                labels={"created_year": "Tahun Pembuatan", "tower_added": "Jumlah Menara Baru"}
            )
            fig_growth.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=380)
            st.plotly_chart(fig_growth, use_container_width=True)
        else:
            st.info("Data pertumbuhan tahunan belum tersedia di HDFS.")

with row3_col2:
    path_modern = "/Project_akhir/visualisasi_asean/rasio_modernisasi_usia"
    df_modern = read_csv_from_hdfs(path_modern)
    
    with chart_card("Rasio Usia Data Menara vs Modernisasi Jaringan", "Rata-rata usia pembaharuan data (hari) berdasarkan tipe generasi"):
        if not df_modern.empty:
            fig_modern = px.bar(
                df_modern,
                x="Country",
                y="avg_data_age_days",
                color="Country",
                color_discrete_sequence=PALETTE,
                text="modernization_percentage",
                labels={"generasi": "Generasi Jaringan", "avg_data_age_days": "Rata-rata Usia Data (Hari)"}
            )
            fig_modern.update_traces(texttemplate='%{text:.2f}%', textposition='outside')
            fig_modern.update_layout(margin=dict(l=20, r=20, t=20, b=20), height=380, showlegend=False)
            st.plotly_chart(fig_modern, use_container_width=True)
        else:
            st.info("Data rasio modernisasi jaringan belum tersedia di HDFS.")

st.write("---")
with st.expander("Struktur Data Analisis Dasar Langsung dari HDFS"):
    st.markdown("Berikut adalah sampel data riil berbentuk tabular yang ditarik langsung dari klaster HDFS lokal tanpa diunduh manual:")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Top Regional & Radio", "Top Per Negara", "Pertumbuhan", "Modernisasi Usia"])
    with tab1:
        st.subheader("Top 10 Operator & Komposisi Radio")
        st.dataframe(df_top10.head(10) if not df_top10.empty else "Data kosong")
        st.dataframe(df_radio if not df_radio.empty else "Data kosong")
    with tab2:
        st.subheader("Top 3 Operator Setiap Negara")
        st.dataframe(df_top3.head(15) if not df_top3.empty else "Data kosong")
    with tab3:
        st.subheader("Data Deret Waktu Pertumbuhan")
        st.dataframe(df_growth if not df_growth.empty else "Data kosong")
    with tab4:
        st.subheader("Metrik Usia Pembaharuan Sinyal")
        st.dataframe(df_modern if not df_modern.empty else "Data kosong")