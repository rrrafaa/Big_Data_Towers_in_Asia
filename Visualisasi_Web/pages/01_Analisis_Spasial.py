import streamlit as st
import plotly.express as px
from utils.hdfs_connection import read_csv_from_hdfs

st.set_page_config(layout="wide")
st.title("Peta Sebaran Infrastruktur Menara (K-Means)")

# ROUTING KE HDFS
PATH_HDFS = "/Project_akhir/visualisasi_asean/profiling_cluster/stats_utama"
df = read_csv_from_hdfs(PATH_HDFS)

if not df.empty:
    # Menggunakan Scatter Mapbox dengan skala warna yang kontras
    fig = px.scatter_mapbox(df, 
                        lat='avg_lat', 
                        lon='avg_lon', 
                        size='total_tower', 
                        color='avg_range_radius',
                        color_continuous_scale="YlOrRd", # Kuning-Oranye-Merah (mirap contoh)
                        hover_name='prediction',
                        zoom=3,
                        mapbox_style="carto-positron")

    # PERBAIKAN: Cara mengatur opacity dan tampilan titik yang benar untuk Mapbox
    fig.update_traces(
        marker=dict(
            opacity=0.8, # Buat sedikit transparan agar area padat terlihat bertumpuk
        )
    )

    # Mengatur layout agar peta penuh dan rapi
    fig.update_layout(
        margin={"r":0,"t":40,"l":0,"b":0},
        coloraxis_colorbar=dict(title="Avg Radius")
    )

    st.plotly_chart(fig, use_container_width=True)
    
    # Menampilkan tabel data di bawahnya untuk detail
    with st.expander("Lihat Detail Data Cluster"):
        st.write(df)
else:
    st.error("Gagal memuat data dari HDFS.")

st.set_page_config(layout="wide", page_title="Detail Cluster Karakteristik")

st.title("📊 Detail Karakteristik 5 Cluster Asia")
st.markdown("""
Halaman ini membedah **isi** dari 5 cluster yang ditemukan. Kita akan melihat teknologi apa yang mendominasi 
di setiap wilayah dan negara mana saja yang masuk ke dalam cluster tersebut.
""")

# --- LOAD DATA DARI HDFS ---
# Kita ambil dua file profiling sekaligus
PATH_TECH = "/Project_akhir/visualisasi_asean/profiling_cluster/Dominasi-teknologi"
PATH_COUNTRY = "/Project_akhir/visualisasi_asean/profiling_cluster/Dominasi-negara"

with st.spinner("Sedang mengambil data detail dari Hadoop..."):
    df_tech = read_csv_from_hdfs(PATH_TECH)
    df_country = read_csv_from_hdfs(PATH_COUNTRY)

if not df_tech.empty and not df_country.empty:
    
    # --- BAGIAN 1: DISTRIBUSI TEKNOLOGI (Stacked Bar Chart) ---
    st.subheader("1. Dominasi Teknologi per Cluster")
    st.info("Visualisasi ini menjawab: Teknologi apa (GSM/LTE/5G) yang paling banyak digunakan di Cluster X?")
    
    # Mengurutkan agar cluster tampil berurutan 0-4
    df_tech = df_tech.sort_values(by='prediction')
    df_tech['prediction'] = df_tech['prediction'].astype(str) # Ubah ke string agar axis tidak desimal
    
    fig_tech = px.bar(df_tech, 
                     x='prediction', 
                     y='count', 
                     color='generasi',
                     title="Perbandingan Radio (GSM vs UMTS vs LTE vs 5G) per Cluster",
                     labels={'prediction': 'ID Cluster', 'count': 'Jumlah Menara', 'radio': 'Teknologi'},
                     barmode='stack', # Stacked bar untuk melihat proporsi
                     color_discrete_sequence=px.colors.qualitative.Pastel)
    
    st.plotly_chart(fig_tech, use_container_width=True)

    st.divider()

    # --- BAGIAN 2: DOMINASI NEGARA (Treemap) ---
    st.subheader("2. Komposisi Negara dalam Cluster")
    st.info("Visualisasi ini menjawab: Negara mana yang paling mendominasi di Cluster X?")
    
    # Menggunakan Treemap agar terlihat modern dan proporsional
    df_country['prediction'] = df_country['prediction'].astype(str)
    
    fig_country = px.treemap(df_country, 
                            path=['prediction', 'Country'], # Hirarki: Cluster -> Negara
                            values='count',
                            color='count',
                            title="Distribusi Negara di Tiap Cluster",
                            color_continuous_scale='Viridis')
    
    st.plotly_chart(fig_country, use_container_width=True)

    # --- BAGIAN 3: INSIGHT ANALISIS ---
    with st.expander("💡 Cara Membaca Analisis Ini untuk Sidang"):
        st.write("""
        1. **Kesenjangan Teknologi**: Jika Cluster 0 (pusat kota) didominasi LTE/5G, sedangkan Cluster 4 (pinggiran) 
           masih didominasi GSM, maka ini adalah bukti kuat adanya kesenjangan digital.
        2. **Dominasi Wilayah**: Melalui Treemap, Anda bisa melihat apakah Cluster tertentu 'eksklusif' milik satu negara 
           (misal: Cluster 2 ternyata 100% Indonesia) atau cluster tersebut 'campuran' beberapa negara.
        3. **Skalabilitas**: Meskipun kita hanya punya 5 titik di peta, grafik ini membuktikan bahwa di balik 
           titik tersebut terdapat jutaan data yang terbagi secara proporsional.
        """)

else:
    st.error("Data profiling cluster tidak ditemukan di HDFS. Pastikan proses analisis di Spark sudah selesai.")

