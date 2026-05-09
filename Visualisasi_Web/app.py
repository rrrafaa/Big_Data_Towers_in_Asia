import streamlit as st

st.set_page_config(page_title="Big Data ASEAN Dashboard", layout="wide", page_icon="📡")

st.title("Dashboard Infrastruktur Telekomunikasi ASEAN")
st.markdown("""
### Deskripsi Proyek
Dashboard ini menampilkan analisis hasil pengolahan Big Data menggunakan **Apache Spark** dan **Hadoop**.
Data diakses secara *real-time* langsung dari **HDFS (Hadoop Distributed File System)**.

**Metodologi yang digunakan:**
* **K-Means Clustering**: Untuk memetakan kesenjangan digital.
* **Gaussian Mixture Model (GMM)**: Untuk analisis keandalan data.
* **Random Forest**: Untuk distribusi penggunaan radio.
""")

st.info("Pilih menu di samping kiri untuk melihat analisis spesifik.")