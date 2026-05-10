import streamlit as st
import plotly.express as px
from utils.hdfs_connection import read_csv_from_hdfs

# 1. Konfigurasi Halaman
st.set_page_config(layout="wide", page_title="Perbandingan Teknologi Negara")

st.title("📱 Perbandingan Teknologi per Negara")
st.markdown("""
Visualisasi ini menunjukkan persentase distribusi teknologi jaringan (GSM, UMTS, LTE, 5G) di setiap negara. 
Ini membantu mengidentifikasi negara mana yang sudah mengadopsi teknologi terbaru secara luas.
""")

# 2. Definisi Path HDFS
PATH_TECH_COMP = "/Project_akhir/visualisasi_asean/perbandingan_teknologi_negara"

# 3. Load Data
with st.spinner("Mengolah data teknologi negara..."):
    df_tech = read_csv_from_hdfs(PATH_TECH_COMP)

if not df_tech.empty:
    # Standarisasi kolom (lower case) sesuai kebiasaan Spark/HDFS kita
    df_tech.columns = [c.lower() for c in df_tech.columns]
    
    # Berdasarkan logika Spark kamu, kolomnya adalah: 
    # country, radio, count_tower, total_towers_country, percentage

    # --- VISUALISASI: 100% STACKED BAR CHART ---
    fig_tech = px.bar(df_tech, 
                      x='country', 
                      y='percentage', 
                      color='radio', # Kolom teknologi
                      title="Persentase Sebaran Teknologi per Negara (%)",
                      labels={
                          'country': 'Negara', 
                          'percentage': 'Persentase (%)', 
                          'radio': 'Tipe Jaringan'
                      },
                      text=df_tech['percentage'].apply(lambda x: f'{x:.1f}%'), # Tampilkan % di dalam bar
                      color_discrete_sequence=px.colors.qualitative.Vivid)

    # Mengatur agar bar bertumpuk (stacked)
    fig_tech.update_layout(
        yaxis_ticksuffix="%",
        xaxis={'categoryorder':'total descending'}, # Urutkan negara dari yang paling banyak datanya
        legend_title_text='Teknologi',
        uniformtext_minsize=8, 
        uniformtext_mode='hide'
    )

    fig_tech.update_traces(textposition='inside')

    st.plotly_chart(fig_tech, use_container_width=True)

    # --- TABEL DETAIL ---
    with st.expander("Lihat Tabel Data Persentase"):
        st.dataframe(df_tech.sort_values(['country', 'percentage'], ascending=[True, False]), use_container_width=True)

    # --- INSIGHT ---
    st.info("""
    **Cara Membaca Grafik:**
    * Setiap batang mewakili satu negara dengan total tinggi 100%.
    * Warna yang mendominasi menunjukkan teknologi utama di negara tersebut.
    * Jika bagian warna **LTE** atau **5G** lebih besar, berarti negara tersebut memiliki infrastruktur digital yang lebih modern.
    """)

else:
    st.error("Data perbandingan teknologi negara tidak ditemukan di HDFS.")