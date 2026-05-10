import streamlit as st
from utils.ui import apply_dashboard_styles

st.set_page_config(page_title="Big Data ASEAN Dashboard", layout="wide")
apply_dashboard_styles()

st.title("Dashboard Infrastruktur Telekomunikasi ASEAN")
st.caption(
    "Analisis Big Data untuk Memetakan Sebaran Infrastruktur Telekomunikasi di Kawasan ASEAN"
)

st.markdown(
    """
    <div class="dashboard-hero">
        <h2>Deskripsi Project</h2>
        <p>
            Halaman ini memang dikhususkan untuk menjelaskan konteks proyek.
            Dashboard menampilkan hasil pengolahan Big Data terkait menara telekomunikasi
            di kawasan ASEAN, mulai dari lokasi tower, teknologi yang digunakan, negara,
            operator, hingga kualitas dan keandalan data.
        </p>
        <p>
            Tujuannya adalah memberi gambaran yang lebih jelas tentang persebaran
            infrastruktur telekomunikasi di ASEAN, sekaligus menyoroti pola dominasi
            teknologi, operator, dan karakteristik cluster yang terbentuk dari hasil analisis.
        </p>
        <p><strong>Sumber Data</strong><br>
            Data berasal dari Kaggle:
            https://www.kaggle.com/datasets/zakariaeyoussefi/cell-towers-worldwide-location-data-by-continent.
            Data yang digunakan difokuskan pada wilayah Asia dan disaring kembali ke kawasan ASEAN.
        </p>
        <p><strong>Metodologi yang digunakan:</strong></p>
        <ul>
            <li><strong>K-Means Clustering</strong> untuk memetakan kesenjangan digital.</li>
            <li><strong>Gaussian Mixture Model (GMM)</strong> untuk analisis keandalan data.</li>
            <li><strong>Random Forest</strong> untuk distribusi penggunaan radio.</li>
        </ul>
    </div>
    """,
    unsafe_allow_html=True,
)
