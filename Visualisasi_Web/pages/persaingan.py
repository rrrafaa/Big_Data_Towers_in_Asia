import streamlit as st
import plotly.express as px
from utils.hdfs_connection import read_csv_from_hdfs

# 1. Konfigurasi Halaman
st.set_page_config(layout="wide", page_title="Sunburst Persaingan Operator")

st.title("🎯 Peta Persaingan Operator (Market Share)")
st.markdown("""
Visualisasi ini menunjukkan hirarki market share infrastruktur menara. 
Mulai dari tingkat **Regional**, lalu ke tingkat **Negara**, hingga ke masing-masing **Operator/Network**.
""")

# 2. Definisi Path HDFS
PATH_SUNBURST = "/Project_akhir/visualisasi_asean/sunburst_asean_operator"

# 3. Load Data
with st.spinner("Membangun hirarki Sunburst..."):
    df_sun = read_csv_from_hdfs(PATH_SUNBURST)

if not df_sun.empty:
    # Standarisasi kolom (lower case)
    df_sun.columns = [c.lower() for c in df_sun.columns]
    
    # Kolom dari Spark kamu: region, country, network, tower_count, percentage_share

    # --- VISUALISASI: SUNBURST CHART ---
    # Kita menggunakan path sesuai hirarki yang kamu buat di Spark
    fig_sun = px.sunburst(df_sun, 
                          path=['region', 'country', 'network'], 
                          values='tower_count',
                          color='country', # Warna berbeda tiap negara agar mudah dibedakan
                          title="Market Share Infrastruktur: ASEAN > Negara > Operator",
                          hover_data=['percentage_share'],
                          color_discrete_sequence=px.colors.qualitative.Pastel)

    # Mempercantik tampilan: Menampilkan persentase saat kursor diarahkan (hover)
    fig_sun.update_traces(
        textinfo="label+percent entry",
        hovertemplate='<b>%{label}</b><br>Jumlah Menara: %{value}<br>Share: %{customdata[0]:.2f}%'
    )

    fig_sun.update_layout(
        margin=dict(t=40, l=0, r=0, b=0),
        height=700 # Dibuat lebih besar agar jelas
    )

    st.plotly_chart(fig_sun, use_container_width=True)

    # --- BAGIAN ANALISIS ---
    st.divider()
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📝 Insight Market Share")
        st.write("""
        1. **Dominasi Negara**: Luas area di lingkaran 'Country' menunjukkan siapa pemegang jumlah menara terbanyak di ASEAN.
        2. **Fragmentasi Operator**: Jika di satu negara terlihat banyak potongan kecil 'Network', berarti persaingan operator di negara tersebut sangat ketat (banyak pemain).
        3. **Monopoli/Duopoli**: Jika di satu negara hanya ada 1-2 potongan besar, berarti pasar dikuasai oleh pemain besar.
        """)

    with col2:
        st.subheader("🔍 Detail Data")
        # Menampilkan top 5 baris data untuk referensi cepat
        st.dataframe(df_sun.sort_values(by='tower_count', ascending=False).head(10), use_container_width=True)

else:
    st.error("Data Sunburst tidak ditemukan di HDFS.")