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
            <li><b>Random Forest Classifier:</b> Memprediksi kategori zona menara murni menggunakan spesifikasi teknis (independen dari koordinat peta).</li>
        </ul>
    </div>
    """,
    unsafe_allow_html=True,
)

st.subheader("Analisis Makro Regional ASEAN")

# Membaca data analisis dasar dari HDFS
path_top10 = "/Project_akhir/visualisasi_asean/top10_operator_asean"
df_top10 = read_csv_from_hdfs(path_top10)

col1, col2 = st.columns([2, 1])

with col1:
    with chart_card("Top 10 Raksasa Provider Telekomunikasi di ASEAN", "Berdasarkan jumlah total menara yang terdata di HDFS"):
        if not df_top10.empty:
            fig = px.bar(
                df_top10,
                x="total_menara_asean",
                y="Network",
                color="Negara_Dominan",
                orientation='h',
                color_discrete_sequence=PALETTE,
                labels={"total_menara_asean": "Jumlah Menara", "Network": "Operator"}
            )
            fig.update_layout(yaxis={'categoryorder':'total ascending'}, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Data Top 10 Operator belum tersedia di HDFS.")

with col2:
    st.markdown("### Ringkasan Analisis")
    if not df_top10.empty:
        total_tower_top10 = df_top10["total_menara_asean"].sum()
        st.metric(label="Total Menara (Top 10 Operator)", value=f"{total_tower_top10:,}")
        st.write(
            f"Provider **{df_top10.iloc[0]['Network']}** mendominasi pasar menara seluler regional "
            f"yang berpusat di negara **{df_top10.iloc[0]['Negara_Dominan']}**."
        )