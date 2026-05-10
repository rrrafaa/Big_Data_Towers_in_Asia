import streamlit as st
import plotly.express as px
from utils.hdfs_connection import read_csv_from_hdfs

st.set_page_config(page_title="Big Data ASEAN Dashboard", layout="wide")

st.title("Dashboard Infrastruktur Telekomunikasi ASEAN")
st.caption(
    "Analisis Big Data untuk Memetakan Sebaran Infrastruktur Telekomunikasi di Kawasan ASEAN"
)

st.markdown("""
    ### Deskripsi Project
    Dashboard ini menampilkan analisis hasil pengolahan Big Data yang mengolah data terkait dengan data tower telekomunikasi di kawasan ASEAN. Data ini mencakup informasi tentang lokasi menara, teknologi yang digunakan, negara, operator, dan keandalan data. Tujuannya adalah untuk memberikan wawasan tentang sebaran infrastruktur telekomunikasi di ASEAN serta dominasi teknologi, negara, dan operator.
            
    #### Sumber Data
    Data diambil dari kaggle : https://www.kaggle.com/datasets/zakariaeyoussefi/cell-towers-worldwide-location-data-by-continent data yang diolah hanya mencakup data asia dengan mengambil data yang berada di kawasan Asean.

    **Metodologi yang digunakan:**
    * **K-Means Clustering**: Untuk memetakan kesenjangan digital.
    * **Gaussian Mixture Model (GMM)**: Untuk analisis keandalan data.
    * **Random Forest**: Untuk distribusi penggunaan radio.
""")