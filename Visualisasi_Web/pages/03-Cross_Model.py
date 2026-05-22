import streamlit as st
import plotly.express as px
import pandas as pd
from utils.hdfs_connection import read_csv_from_hdfs
from utils.ui import apply_dashboard_styles, chart_card, PALETTE

st.set_page_config(page_title="Cross Model (Random Forest)", layout="wide")
apply_dashboard_styles()

st.title("🤖 Evaluasi Model AI - Random Forest Classifier")
st.caption("Menguji Kemampuan AI Memprediksi Zona Menara Berdasarkan Sifat Teknis Tanpa Fitur GPS")

# Path HDFS sesuai dengan output akhir skrip 05_RF.py
path_rf_output = "/Project_akhir/visualisasi_asean/rf_prediction_output"
df_rf = read_csv_from_hdfs(path_rf_output)

if not df_rf.empty:
    # Menghitung Akurasi Sederhana secara langsung dari data HDFS untuk sinkronisasi otomatis
    correct_predictions = (df_rf["kmeans_target_cluster"] == df_rf["rf_predicted_cluster"]).sum()
    total_data = len(df_rf)
    accuracy = (correct_predictions / total_data) * 100 if total_data > 0 else 0
    
    col_m1, col_m2, col_m3 = st.columns(3)
    with col_m1:
        st.metric(label="Total Data Sampel Diuji", value=f"{total_data:,}")
    with col_m2:
        st.metric(label="Prediksi AI yang Tepat", value=f"{correct_predictions:,}")
    with col_m3:
        st.metric(label="Akurasi Model di Dashboard", value=f"{accuracy:.2f} %")

    st.write("---")
    
    c1, c2 = st.columns(2)
    with c1:
        with chart_card("Distribusi Zona Asli Hasil K-Means", "Target klasifikasi awal"):
            fig_target = px.histogram(df_rf, x="kmeans_target_cluster", color="kmeans_target_cluster", color_discrete_sequence=PALETTE)
            st.plotly_chart(fig_target, use_container_width=True)
            
    with c2:
        with chart_card("Distribusi Zona Hasil Tebakan Random Forest AI", "Hasil prediksi model klasifikasi"):
            fig_pred = px.histogram(df_rf, x="rf_predicted_cluster", color="rf_predicted_cluster", color_discrete_sequence=PALETTE)
            st.plotly_chart(fig_pred, use_container_width=True)

    with st.expander("🔍 Intip Data Prediksi Komplit (Sampel dari HDFS)"):
        st.dataframe(df_rf.head(100), use_container_width=True)

else:
    st.error("Gagal memuat output model Random Forest dari HDFS. Pastikan skrip '05_RF.py' sudah selesai dijalankan.")