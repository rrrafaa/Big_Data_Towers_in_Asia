import streamlit as st
import plotly.express as px
from utils.hdfs_connection import read_csv_from_hdfs

st.set_page_config(layout="wide", page_title="Quality of Data")

st.title("🛡️ Analisis Keandalan Data per Cluster")
st.markdown("""
Analisis ini menunjukkan tingkat kepercayaan data di setiap wilayah cluster. 
Data ini merupakan hasil profiling dari indikator aktivitas digital yang diproses di Hadoop.
""")

# Path sesuai dengan kode Spark kamu
PATH_KEANDALAN = "/Project_akhir/visualisasi_asean/profiling_cluster/Dominiasi-keandalan"

with st.spinner("Mengambil data keandalan dari HDFS..."):
    df_qa = read_csv_from_hdfs(PATH_KEANDALAN)

if not df_qa.empty:
    # 1. Standarisasi Kolom (Lower Case)
    # Kolom kamu di Spark: prediction, keandalan_data, count
    df_qa.columns = [c.lower() for c in df_qa.columns]
    
    # Pastikan prediction jadi string agar urutan di grafik bagus
    df_qa['prediction'] = "Cluster " + df_qa['prediction'].astype(str)

    # --- LAYOUT DASHBOARD ---
    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("📊 Perbandingan Keandalan antar Cluster")
        # Menggunakan Stacked Bar Chart untuk melihat komposisi
        fig_bar = px.bar(df_qa, 
                         x='prediction', 
                         y='count', 
                         color='keandalan_data', # Nama kolom sesuai Spark (sudah di-lower)
                         title="Distribusi Tingkat Keandalan",
                         barmode='stack',
                         color_discrete_sequence=px.colors.sequential.Greens_r)
        
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        st.subheader("🎯 Total Proporsi Keandalan")
        # Pie chart untuk melihat gambaran umum seluruh ASEAN
        fig_pie = px.pie(df_qa, 
                         values='count', 
                         names='keandalan_data', 
                         hole=0.5,
                         title="Persentase Kualitas Data Keseluruhan",
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        
        st.plotly_chart(fig_pie, use_container_width=True)

    # --- BAGIAN INSIGHT ---
    st.divider()
    st.subheader("💡 Interpretasi Hasil")
    
    # Mencari cluster dengan jumlah 'count' terbanyak
    best_cluster = df_qa.sort_values(by='count', ascending=False).iloc[0]
    
    st.info(f"""
    * **Cluster Dominan**: {best_cluster['prediction']} memiliki frekuensi data terbanyak.
    * **Analisis**: Jika warna hijau tua (High Reliability) mendominasi, berarti infrastruktur di wilayah tersebut terekam dengan akurasi tinggi.
    * **Kegunaan**: Data ini membantu stakeholder menentukan wilayah mana yang butuh pemutakhiran data koordinat menara.
    """)

else:
    st.error("Data 'Dominiasi-keandalan' tidak ditemukan. Pastikan script Spark sudah selesai dijalankan.")