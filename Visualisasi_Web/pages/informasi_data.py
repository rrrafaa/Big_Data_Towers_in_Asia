import streamlit as st
import plotly.express as px
from utils.hdfs_connection import read_csv_from_hdfs
from utils.ui import apply_dashboard_styles, chart_card, PALETTE, style_figure

# 1. Konfigurasi Halaman
st.set_page_config(layout="wide", page_title="Pertumbuhan Tahunan")
apply_dashboard_styles()

st.title("Analisis Pertumbuhan Menara Tahunan")
st.caption(
    "Visualisasi tren pertumbuhan menara di Asia berdasarkan tahun pembuatan data."
)

# 2. Definisi Path HDFS sesuai informasi kamu
PATH_GROWTH = "/Project_akhir/visualisasi_asean/pertumbuhan_tahunan"

# 3. Load Data
with st.spinner("Mengambil data tren dari Hadoop..."):
    df_growth = read_csv_from_hdfs(PATH_GROWTH)

if not df_growth.empty:
    # Standarisasi kolom (lower case)
    df_growth.columns = [c.lower() for c in df_growth.columns]
    
    # Pastikan data diurutkan berdasarkan tahun agar garis tidak berantakan
    # Kolom dari Spark kamu: created_year, count
    df_growth = df_growth.sort_values(by='created_year')
    
    # Konversi created_year ke string agar tidak muncul koma (misal: 2,021) di chart
    df_growth['created_year'] = df_growth['created_year'].astype(str)

    # --- VISUALISASI: LINE CHART ---
    with chart_card("Tren Pertumbuhan Menara di Asia (Overall)"):
        fig_line = px.line(
            df_growth,
            x="created_year",
            y="count",
            labels={"created_year": "Tahun", "count": "Jumlah Menara Baru"},
            markers=True,
            text="count",
        )
        fig_line.update_traces(line_color=PALETTE[3], line_width=3, textposition="top center")
        fig_line.update_layout(xaxis_tickangle=0, hovermode="x unified")
        st.plotly_chart(style_figure(fig_line), use_container_width=True)

    with chart_card("Ringkasan Pertumbuhan Tahunan"):
        col1, col2, col3 = st.columns(3)

        with col1:
            total_all_time = df_growth["count"].sum()
            st.metric("Total Menara Terdata", f"{total_all_time:,}")

        with col2:
            max_year = df_growth.loc[df_growth["count"].idxmax()]
            st.metric("Puncak Pertumbuhan", f"Tahun {max_year['created_year']}", f"{max_year['count']:,} Menara")

        with col3:
            if len(df_growth) >= 2:
                last_val = int(df_growth.iloc[-1]["count"])
                prev_val = int(df_growth.iloc[-2]["count"])
                diff = last_val - prev_val
                st.metric("Perubahan Tahun Terakhir", f"{last_val:,}", f"{diff:,}")
            else:
                st.metric("Perubahan Tahun Terakhir", "N/A", "Data belum cukup")

else:
    st.error("Data pertumbuhan tahunan tidak ditemukan di HDFS.")
