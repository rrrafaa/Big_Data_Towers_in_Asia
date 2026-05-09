import streamlit as st
import plotly.express as px
from utils.hdfs_connection import read_csv_from_hdfs

# 1. Konfigurasi Halaman
st.set_page_config(layout="wide", page_title="Detail Cluster Karakteristik")

st.title("Detail Karakteristik Cluster Asia")
st.markdown("""
Halaman ini membedah isi dari cluster yang ditemukan. Kita akan melihat teknologi apa yang mendominasi 
dan bagaimana distribusi negara di setiap cluster.
""")

# 2. Definisi Path HDFS
PATH_TECH = "/Project_akhir/visualisasi_asean/profiling_cluster/Dominasi-teknologi"
PATH_COUNTRY = "/Project_akhir/visualisasi_asean/profiling_cluster/Dominasi-negara"

# 3. Load Data
with st.spinner("Mengambil data dari HDFS..."):
    df_tech = read_csv_from_hdfs(PATH_TECH)
    df_country = read_csv_from_hdfs(PATH_COUNTRY)

if not df_tech.empty and not df_country.empty:
    
    # Standarisasi Nama Kolom (Mencegah Error Case Sensitive)
    df_tech.columns = [c.lower() for c in df_tech.columns]
    df_country.columns = [c.lower() for c in df_country.columns]
    
    # Pastikan tipe data prediction adalah string untuk sumbu X yang rapi
    df_tech['prediction'] = df_tech['prediction'].astype(str)
    df_country['prediction'] = df_country['prediction'].astype(str)

    # --- LAYOUT KOLOM ---
    col1, col2 = st.columns([1, 1])

    with col1:
        # --- BAGIAN 1: STACKED BAR CHART (TEKNOLOGI) ---
        st.subheader("1. Dominasi Teknologi per Cluster")
        
        # Mapping nama kolom hasil standarisasi .lower()
        # Jika di CSV-mu 'generasi', maka ganti 'radio' jadi 'generasi' di bawah ini
        fig_tech = px.bar(df_tech, 
                         x='prediction', 
                         y='count', 
                         color='generasi', # Sesuai temuan error sebelumnya
                         title="Komposisi Teknologi (GSM/LTE/5G)",
                         labels={'prediction': 'ID Cluster', 'count': 'Jumlah Menara', 'generasi': 'Teknologi'},
                         barmode='stack',
                         color_discrete_sequence=px.colors.qualitative.Set3)
        
        st.plotly_chart(fig_tech, use_container_width=True)

    with col2:
        # --- BAGIAN 2: PIE CHART (NEGARA) ---
        st.subheader("2. Persentase Negara per Cluster")
        
        # Dropdown interaktif
        cluster_list = sorted(df_country['prediction'].unique())
        selected_cluster = st.selectbox("Pilih Cluster untuk Detail Negara:", cluster_list)

        # Filter data
        df_filtered = df_country[df_country['prediction'] == selected_cluster]

        # Buat Donut Chart
        fig_pie = px.pie(df_filtered, 
                         values='count', 
                         names='country', # Sudah dipaksa kecil oleh .lower()
                         title=f"Distribusi Negara di Cluster {selected_cluster}",
                         hole=0.4,
                         color_discrete_sequence=px.colors.sequential.RdBu)

        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- BAGIAN 3: TABEL DATA DETAIL ---
    with st.expander("Klik untuk melihat tabel data mentah HDFS"):
        tab1, tab2 = st.tabs(["Data Teknologi", "Data Negara"])
        with tab1:
            st.dataframe(df_tech, use_container_width=True)
        with tab2:
            st.dataframe(df_country, use_container_width=True)

else:
    st.error("Data tidak ditemukan di HDFS. Periksa kembali path folder Anda.")