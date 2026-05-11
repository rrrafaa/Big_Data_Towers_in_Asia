import streamlit as st
import plotly.express as px
from utils.hdfs_connection import read_csv_from_hdfs

# 1. Konfigurasi Halaman
st.set_page_config(layout="wide", page_title="Tipe Jangkauan Cluster")

st.title("🏘️ Profiling Tipe Jangkauan per Cluster")
st.markdown("""
Halaman ini menganalisis karakteristik wilayah pada setiap cluster berdasarkan jangkauan sinyal 
(**Urban, Suburban, Rural**). Ini membantu mengidentifikasi apakah sebuah cluster 
mewakili area metropolitan atau area terpencil.
""")

# 2. Definisi Path HDFS sesuai file 03_Analisis_Profiling.py
PATH_AREA = "/Project_akhir/visualisasi_asean/profiling_cluster/Dominiasi-tipe-jangkauan"

# 3. Load Data
with st.spinner("Mengambil data jangkauan wilayah..."):
    df_area = read_csv_from_hdfs(PATH_AREA)

if not df_area.empty:
    # Standarisasi kolom menjadi lowercase
    # Berdasarkan file Spark: prediction, jangkauan, count
    df_area.columns = [c.lower() for c in df_area.columns]
    
    # Mempercantik tampilan ID Cluster
    df_area['prediction'] = "Cluster " + df_area['prediction'].astype(str)

    # --- VISUALISASI UTAMA: GROUPED BAR CHART ---
    st.subheader("1. Distribusi Tipe Wilayah per Cluster")
    
    fig_bar = px.bar(df_area, 
                     x='prediction', 
                     y='count', 
                     color='jangkauan',
                     title="Jumlah Menara berdasarkan Tipe Jangkauan (Urban/Suburban/Rural)",
                     labels={'prediction': 'ID Cluster', 'count': 'Jumlah Menara', 'jangkauan': 'Tipe Wilayah'},
                     barmode='group', # Mengelompokkan bar berdampingan
                     color_discrete_sequence=px.colors.qualitative.Pastel)
    
    fig_bar.update_layout(xaxis_title="Cluster", yaxis_title="Total Menara")
    st.plotly_chart(fig_bar, use_container_width=True)

    # --- VISUALISASI KEDUA: SUNBURST (Untuk melihat porsi) ---
    st.divider()
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("2. Proporsi Jangkauan")
        fig_pie = px.sunburst(df_area, 
                             path=['prediction', 'jangkauan'], 
                             values='count',
                             color='prediction',
                             title="Hirarki Cluster dan Jangkauan",
                             color_discrete_sequence=px.colors.qualitative.Set3)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.subheader("📝 Insight Analisis")
        # Mencari jangkauan yang paling dominan secara keseluruhan
        top_area = df_area.groupby('jangkauan')['count'].sum().idxmax()
        st.info(f"""
        - **Dominasi Wilayah**: Secara keseluruhan, kategori **{top_area}** memiliki jumlah infrastruktur terbanyak.
        - **Karakteristik Cluster**: 
            - Jika **Urban** tinggi: Cluster tersebut kemungkinan besar adalah pusat kota besar.
            - Jika **Rural** tinggi: Cluster tersebut adalah wilayah pinggiran atau pedesaan dengan jangkauan luas namun kepadatan menara rendah.
        """)
        
        # Tampilkan tabel data
        st.dataframe(df_area, use_container_width=True)

else:
    st.error("Data 'Dominiasi-tipe-jangkauan' tidak ditemukan di HDFS.")