import streamlit as st
import plotly.express as px
from utils.hdfs_connection import read_csv_from_hdfs

# 1. Konfigurasi Halaman
st.set_page_config(layout="wide", page_title="Overall Radio Distribution")

st.title("🌐 Distribusi Teknologi Total (Asia)")
st.markdown("""
Halaman ini menyajikan gambaran besar (Big Picture) mengenai komposisi teknologi jaringan 
di seluruh area penelitian tanpa sekat negara.
""")

# 2. Definisi Path HDFS
PATH_OVERALL = "/Project_akhir/visualisasi_asean/overall_radio_distribution"

# 3. Load Data
with st.spinner("Menghitung total distribusi..."):
    df_overall = read_csv_from_hdfs(PATH_OVERALL)

if not df_overall.empty:
    # Standarisasi kolom
    df_overall.columns = [c.lower() for c in df_overall.columns]
    
    # Kolom dari Spark kamu: radio, count, percentage

    # --- LAYOUT KOLOM ---
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("🥧 Proporsi Teknologi")
        fig_pie = px.pie(df_overall, 
                         values='count', 
                         names='radio', 
                         hole=0.4,
                         title="Persentase Pangsa Pasar Teknologi",
                         color_discrete_sequence=px.colors.qualitative.Pastel)
        
        fig_pie.update_traces(textposition='inside', textinfo='percent+label')
        st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        st.subheader("📊 Hierarki Dominasi")
        # Funnel Chart menunjukkan penurunan dari teknologi paling umum ke paling jarang
        fig_funnel = px.funnel(df_overall, 
                               y='radio', 
                               x='count',
                               title="Urutan Jumlah Menara Berdasarkan Teknologi",
                               color='radio',
                               color_discrete_sequence=px.colors.qualitative.Safe)
        
        st.plotly_chart(fig_funnel, use_container_width=True)

    # --- RINGKASAN DATA ---
    st.divider()
    st.subheader("📑 Rekapitulasi Angka")
    
    # Menampilkan ringkasan dalam barisan metrik
    metrics = st.columns(len(df_overall))
    for i, row in df_overall.iterrows():
        with metrics[i]:
            st.metric(label=f"Total {row['radio']}", 
                      value=f"{int(row['count']):,}", 
                      delta=f"{row['percentage']:.2f}% dari Total")

else:
    st.error("Data distribusi keseluruhan tidak ditemukan di HDFS.")