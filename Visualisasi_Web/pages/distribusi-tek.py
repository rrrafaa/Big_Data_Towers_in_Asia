import streamlit as st
import plotly.express as px
from utils.hdfs_connection import read_csv_from_hdfs
from utils.ui import apply_dashboard_styles, chart_card, PALETTE, style_figure

# 1. Konfigurasi Halaman
st.set_page_config(layout="wide", page_title="Overall Radio Distribution")
apply_dashboard_styles()

st.title("🌐 Distribusi Teknologi Total (Asia)")
st.caption("Gambaran komposisi teknologi jaringan di seluruh area penelitian tanpa sekat negara.")

# 2. Definisi Path HDFS
PATH_OVERALL = "/Project_akhir/visualisasi_asean/overall_radio_distribution"

# 3. Load Data
with st.spinner("Menghitung total distribusi..."):
    df_overall = read_csv_from_hdfs(PATH_OVERALL)

if not df_overall.empty:
    # Standarisasi kolom
    df_overall.columns = [c.lower() for c in df_overall.columns]
    
    # Kolom dari Spark kamu: radio, count, percentage

    with chart_card("Proporsi Teknologi dan Hierarki Dominasi"):
        col1, col2 = st.columns([1, 1])

        with col1:
            fig_pie = px.pie(
                df_overall,
                values="count",
                names="radio",
                hole=0.4,
                color_discrete_sequence=PALETTE,
            )
            fig_pie.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(style_figure(fig_pie), use_container_width=True)

        with col2:
            fig_funnel = px.funnel(
                df_overall,
                y="radio",
                x="count",
                color="radio",
                color_discrete_sequence=PALETTE,
            )
            st.plotly_chart(style_figure(fig_funnel), use_container_width=True)

    with chart_card("Rekapitulasi Angka"):
        metrics = st.columns(len(df_overall))
        for i, row in df_overall.iterrows():
            with metrics[i]:
                st.metric(
                    label=f"Total {row['radio']}",
                    value=f"{int(row['count']):,}",
                    delta=f"{row['percentage']:.2f}% dari Total",
                )

else:
    st.error("Data distribusi keseluruhan tidak ditemukan di HDFS.")
