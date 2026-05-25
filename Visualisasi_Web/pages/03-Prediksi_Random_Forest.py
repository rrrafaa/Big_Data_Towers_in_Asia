import streamlit as st
import plotly.express as px
import pandas as pd
from sklearn.metrics import classification_report
from utils.hdfs_connection import read_csv_from_hdfs
from utils.ui import apply_dashboard_styles, chart_card, PALETTE

st.set_page_config(page_title="Cross Model (Random Forest)", layout="wide")
apply_dashboard_styles()

st.title("Evaluasi Model AI - Random Forest Classifier")
st.caption("Menguji Kemampuan AI Memprediksi Zona Menara Berdasarkan Sifat Teknis Tanpa Fitur GPS")

# Path distribusi data dari komputasi Apache Spark (HDFS)
PATH_RF_OUTPUT = "/Project_akhir/visualisasi_asean/rf_prediction_output"
PATH_CROSS_PROFILE = "/Project_akhir/visualisasi_asean/cross_profiling_output"

df_rf = read_csv_from_hdfs(PATH_RF_OUTPUT)
df_cross = read_csv_from_hdfs(PATH_CROSS_PROFILE)

if not df_rf.empty:
    y_true = df_rf["kmeans_target_cluster"]
    y_pred = df_rf["rf_predicted_cluster"]
    
    total_data = len(df_rf)
    
    # Mengambil nilai precision, recall, f1-score global (weighted)
    report = classification_report(y_true, y_pred, output_dict=True)
    accuracy = report['accuracy'] * 100
    precision = report['weighted avg']['precision'] * 100
    recall = report['weighted avg']['recall'] * 100
    f1_score = report['weighted avg']['f1-score'] * 100

    # 1. RINGKASAN METRIK UTAMA (4 KOLOM METRIC)
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.metric(label="Total Data Sampel (Test)", value=f"{total_data:,}")
    with col_m2:
        st.metric(label="Akurasi Model", value=f"{accuracy:.2f} %")
    with col_m3:
        st.metric(label="F1-Score (Keseimbangan)", value=f"{f1_score:.2f} %")
    with col_m4:
        st.metric(label="Precision / Recall", value=f"{precision:.1f}% / {recall:.1f}%")

    st.write("---")
    
    # 2. ANALISIS SILANG: K-MEANS X GMM (CROSS PROFILING)
    st.subheader("Analisis Silang Spasial vs Keandalan Data")
    
    if not df_cross.empty:
        cc1, cc2 = st.columns([1.2, 1.0])
        
        with cc1:
            with chart_card("Matriks Distribusi Menara (K-Means vs GMM)", "Melihat irisan jumlah aset menara antara cluster wilayah dan cluster keandalan"):
                # Penyelarasan format label sumbu chart
                df_cross_chart = df_cross.copy()
                df_cross_chart["prediction"] = "Cluster " + df_cross_chart["prediction"].astype(str)
                df_cross_chart["gmm_cluster"] = "GMM " + df_cross_chart["gmm_cluster"].astype(str)
                
                fig_cross = px.density_heatmap(
                    df_cross_chart, 
                    x="prediction", 
                    y="gmm_cluster", 
                    z="tower_count", 
                    text_auto=True, 
                    color_continuous_scale="Viridis",
                    labels={"prediction": "Zona Wilayah (K-Means)", "gmm_cluster": "Keandalan (GMM)", "tower_count": "Jumlah Menara"}
                )
                fig_cross.update_layout(margin=dict(t=10, b=10), height=350)
                st.plotly_chart(fig_cross, use_container_width=True)
                
        with cc2:
            with chart_card("Detail Metrik Fisik Hasil Cross Profiling", "Rata-rata sifat teknis menara pada setiap kombinasi cluster"):
                df_cross_display = df_cross.rename(columns={
                    "prediction": "Cluster K-Means",
                    "gmm_cluster": "Cluster GMM",
                    "tower_count": "Total Tower",
                    "avg_sam": "Avg SAM",
                    "avg_days_old": "Avg Usia Data (Hari)",
                    "avg_range_radius": "Avg Radius (m)"
                })
                st.dataframe(
                    df_cross_display.style.format({
                        "Total Tower": "{:,}",
                        "Avg SAM": "{:.2f}",
                        "Avg Usia Data (Hari)": "{:,.0f}",
                        "Avg Radius (m)": "{:.1f}"
                    }),
                    use_container_width=True,
                    height=310,
                    hide_index=True
                )
    else:
        st.warning("Data 'cross_profiling_output' tidak ditemukan di HDFS.")

    st.write("---")
    
    # 3. GRAFIK PERBANDINGAN DISTRIBUSI (TARGET VS PREDIKSI AI/hasil RF)
    st.subheader("Perbandingan Distribusi Target vs Prediksi AI")
    c1, c2 = st.columns(2)
    with c1:
        with chart_card("Distribusi Zona Asli Hasil K-Means", "Target klasifikasi awal berdasarkan data spasial asli"):
            fig_target = px.histogram(df_rf, x="kmeans_target_cluster", color="kmeans_target_cluster", color_discrete_sequence=PALETTE)
            fig_target.update_layout(height=300, margin=dict(t=10, b=10))
            st.plotly_chart(fig_target, use_container_width=True)
            
    with c2:
        with chart_card("Distribusi Zona Hasil Tebakan Random Forest AI", "Hasil prediksi klasifikasi berdasarkan fitur teknis non-GPS"):
            fig_pred = px.histogram(df_rf, x="rf_predicted_cluster", color="rf_predicted_cluster", color_discrete_sequence=PALETTE)
            fig_pred.update_layout(height=300, margin=dict(t=10, b=10))
            st.plotly_chart(fig_pred, use_container_width=True)

    st.write("---")
    
    # 4. MATRIKS EVALUASI & DETEKSI EROR MODEL
    st.subheader("Diagnostik Akurasi & Deteksi Kesalahan Model")
    c3, c4 = st.columns([1.2, 1.0])
    
    with c3:
        with chart_card("Confusion Matrix Heatmap", "Melihat pola cluster mana yang sering salah ditebak oleh AI"):
            cm_df = pd.crosstab(y_true, y_pred, rownames=['Asli (K-Means)'], colnames=['Tebakan (RF)'])
            fig_heatmap = px.imshow(
                cm_df, 
                text_auto=True, 
                labels=dict(x="Cluster Tebakan (RF)", y="Cluster Asli (K-Means)", color="Jumlah Tower"),
                color_continuous_scale="Purples"
            )
            fig_heatmap.update_layout(margin=dict(t=10, b=10), height=380)
            st.plotly_chart(fig_heatmap, use_container_width=True)
            
    with c4:
        with chart_card("Detail Performa Klasifikasi Per-Cluster", "Metrik evaluasi presisi mendalam untuk tiap-tiap zona"):
            report_df = pd.DataFrame(report).transpose().iloc[:-3] 
            report_df.columns = ["Precision", "Recall", "F1-Score", "Jumlah Data"]
            report_df[["Precision", "Recall", "F1-Score"]] = report_df[["Precision", "Recall", "F1-Score"]] * 100
            st.dataframe(
                report_df.style.format("{:.2f}%", subset=["Precision", "Recall", "F1-Score"])
                .format("{:,.0f}", subset=["Jumlah Data"]), 
                use_container_width=True,
                height=340
            )

    st.write("---")

    with st.expander("Data Prediksi Komplit"):
        st.dataframe(df_rf.head(100), use_container_width=True)

else:
    st.error("Gagal memuat output model Random Forest dari HDFS. Pastikan skrip '05_RF.py' sudah selesai dijalankan.")