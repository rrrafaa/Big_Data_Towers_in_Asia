import streamlit as st
import plotly.express as px
from utils.hdfs_connection import read_csv_from_hdfs

# 1. Konfigurasi Halaman
st.set_page_config(layout="wide", page_title="Hierarki Cluster")

st.title("🎯 Hierarki Cluster: Wilayah, Negara, & Operator")
st.markdown("""
Halaman ini menggabungkan hasil **Machine Learning (Clustering)** dengan data **Geografis** dan **Provider**. 
Klik pada bagian lingkaran untuk melakukan *drill-down* (melihat detail) di tiap level.
""")

# 2. Definisi Path HDFS sesuai logika Spark Anda
PATH_HIERARCHY = "/Project_akhir/visualisasi_asean/profiling_cluster/Hierarki-Cluster-Lengkap"

# 3. Load Data
with st.spinner("Membangun struktur hirarki dari HDFS..."):
    df_hier = read_csv_from_hdfs(PATH_HIERARCHY)

if not df_hier.empty:
    # Standarisasi kolom menjadi huruf kecil (lowercase)
    # Kolom di Spark: prediction, Country, Network, count
    df_hier.columns = [c.lower() for c in df_hier.columns]
    
    # Mempercantik tampilan ID Cluster
    df_hier['prediction'] = "Cluster " + df_hier['prediction'].astype(str)

    # --- VISUALISASI UTAMA: SUNBURST ---
    # Hirarki: Cluster -> Negara -> Operator/Network
    fig_sun = px.sunburst(
        df_hier, 
        path=['prediction', 'country', 'network'], 
        values='count',
        color='prediction', # Warna dikelompokkan berdasarkan Cluster
        title="Eksplorasi Hirarki: Cluster > Negara > Operator",
        color_discrete_sequence=px.colors.qualitative.Pastel,
        height=750
    )

    # Menampilkan label dan persentase di dalam lingkaran
    fig_sun.update_traces(
        textinfo="label+percent entry",
        hovertemplate='<b>%{label}</b><br>Jumlah Menara: %{value}<br>Persentase: %{percentEntry:.2f}%'
    )

    # Pengaturan Layout
    fig_sun.update_layout(
        margin=dict(t=50, l=0, r=0, b=0),
        hoverlabel=dict(bgcolor="white", font_size=13)
    )

    # Tampilkan Chart
    st.plotly_chart(fig_sun, use_container_width=True)

    # --- BAGIAN INSIGHT ---
    st.divider()
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("💡 Cara Membaca Sunburst")
        st.write("""
        - **Lingkaran Dalam**: Mewakili ID Cluster hasil K-Means.
        - **Lingkaran Tengah**: Menunjukkan negara-negara yang masuk dalam cluster tersebut.
        - **Lingkaran Luar**: Menunjukkan operator (Network) yang memiliki menara di negara tersebut.
        - **Interaksi**: Klik pada salah satu cluster atau negara untuk melihat detail provider di dalamnya secara eksklusif.
        """)

    with col2:
        st.subheader("📋 Top 5 Data Kontributor")
        # Menampilkan tabel data teratas
        st.dataframe(
            df_hier.sort_values(by='count', ascending=False).head(5), 
            use_container_width=True
        )

else:
    st.error("Data Hierarki Cluster tidak ditemukan di HDFS. Pastikan proses Spark sudah selesai.")