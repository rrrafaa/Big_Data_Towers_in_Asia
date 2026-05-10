import streamlit as st
import plotly.express as px

from utils.hdfs_connection import read_csv_from_hdfs

st.set_page_config(page_title="Big Data ASEAN Dashboard", layout="wide", page_icon="📡")


def normalize_columns(df):
    if df.empty:
        return df
    df.columns = [c.lower() for c in df.columns]
    return df


def has_cols(df, cols):
    return all(col in df.columns for col in cols)


st.title("📡 Dashboard Infrastruktur Telekomunikasi ASEAN")
st.caption(
    "Seluruh visualisasi digabung dalam satu halaman untuk tampilan dashboard yang lebih rapi."
)

PATHS = {
    "stats": "/Project_akhir/visualisasi_asean/profiling_cluster/stats_utama",
    "tech": "/Project_akhir/visualisasi_asean/profiling_cluster/Dominasi-teknologi",
    "country": "/Project_akhir/visualisasi_asean/profiling_cluster/Dominasi-negara",
    "operator": "/Project_akhir/visualisasi_asean/profiling_cluster/Dominasi-operator",
    "top10": "/Project_akhir/visualisasi_asean/top_10_operator_asean",
    "reliability": "/Project_akhir/visualisasi_asean/profiling_cluster/Dominiasi-keandalan",
}

with st.spinner("Mengambil seluruh data visualisasi dari HDFS..."):
    df_stats = normalize_columns(read_csv_from_hdfs(PATHS["stats"]))
    df_tech = normalize_columns(read_csv_from_hdfs(PATHS["tech"]))
    df_country = normalize_columns(read_csv_from_hdfs(PATHS["country"]))
    df_operator = normalize_columns(read_csv_from_hdfs(PATHS["operator"]))
    df_top10 = normalize_columns(read_csv_from_hdfs(PATHS["top10"]))
    df_reliability = normalize_columns(read_csv_from_hdfs(PATHS["reliability"]))


row1_col1, row1_col2 = st.columns(2)
with row1_col1:
    st.subheader("1) Peta Sebaran Infrastruktur")
    if not df_stats.empty and has_cols(df_stats, ["avg_lat", "avg_lon", "total_tower", "avg_range_radius"]):
        fig_map = px.scatter_mapbox(
            df_stats,
            lat="avg_lat",
            lon="avg_lon",
            size="total_tower",
            color="avg_range_radius",
            color_continuous_scale="YlOrRd",
            zoom=3,
            mapbox_style="carto-positron",
        )
        fig_map.update_traces(marker=dict(opacity=0.8))
        fig_map.update_layout(margin={"r": 0, "t": 20, "l": 0, "b": 0})
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        st.warning("Data peta belum tersedia atau format kolom tidak sesuai.")

with row1_col2:
    st.subheader("2) Dominasi Teknologi per Cluster")
    if not df_tech.empty and has_cols(df_tech, ["prediction", "count", "generasi"]):
        df_tech["prediction"] = df_tech["prediction"].astype(str)
        fig_tech = px.bar(
            df_tech.sort_values(by="prediction"),
            x="prediction",
            y="count",
            color="generasi",
            barmode="stack",
            labels={"prediction": "ID Cluster", "count": "Jumlah Menara", "generasi": "Teknologi"},
            color_discrete_sequence=px.colors.qualitative.Set3,
        )
        st.plotly_chart(fig_tech, use_container_width=True)
    else:
        st.warning("Data teknologi belum tersedia atau format kolom tidak sesuai.")


row2_col1, row2_col2 = st.columns(2)
with row2_col1:
    st.subheader("3) Komposisi Negara per Cluster")
    if not df_country.empty and has_cols(df_country, ["prediction", "country", "count"]):
        df_country["prediction"] = df_country["prediction"].astype(str)
        fig_country = px.treemap(
            df_country,
            path=["prediction", "country"],
            values="count",
            color="count",
            color_continuous_scale="Viridis",
        )
        st.plotly_chart(fig_country, use_container_width=True)
    else:
        st.warning("Data negara belum tersedia atau format kolom tidak sesuai.")

with row2_col2:
    st.subheader("4) Struktur Operator per Cluster")
    if not df_operator.empty and has_cols(df_operator, ["prediction", "network", "count"]):
        df_operator["prediction"] = "Cluster " + df_operator["prediction"].astype(str)
        fig_operator = px.sunburst(
            df_operator,
            path=["prediction", "network"],
            values="count",
            color="prediction",
            color_discrete_sequence=px.colors.qualitative.Prism,
        )
        st.plotly_chart(fig_operator, use_container_width=True)
    else:
        st.warning("Data operator belum tersedia atau format kolom tidak sesuai.")


row3_col1, row3_col2 = st.columns(2)
with row3_col1:
    st.subheader("5) Top 10 Operator ASEAN")
    if not df_top10.empty:
        numeric_cols = df_top10.select_dtypes(include=["number"]).columns.tolist()
        value_col = numeric_cols[0] if numeric_cols else None
        label_cols = [c for c in df_top10.columns if c != value_col]
        label_col = label_cols[0] if label_cols else None
        if value_col and label_col:
            fig_top = px.bar(
                df_top10.sort_values(by=value_col, ascending=True).tail(10),
                x=value_col,
                y=label_col,
                orientation="h",
                text=value_col,
                color=value_col,
                color_continuous_scale="Blues",
            )
            st.plotly_chart(fig_top, use_container_width=True)
        else:
            st.warning("Format data Top 10 operator belum sesuai.")
    else:
        st.warning("Data Top 10 operator belum tersedia.")

with row3_col2:
    st.subheader("6) Keandalan Data per Cluster")
    if not df_reliability.empty and has_cols(df_reliability, ["prediction", "keandalan_data", "count"]):
        df_reliability["prediction"] = "Cluster " + df_reliability["prediction"].astype(str)
        fig_rel = px.bar(
            df_reliability,
            x="prediction",
            y="count",
            color="keandalan_data",
            barmode="stack",
            color_discrete_sequence=px.colors.sequential.Greens_r,
        )
        st.plotly_chart(fig_rel, use_container_width=True)
    else:
        st.warning("Data keandalan belum tersedia atau format kolom tidak sesuai.")


st.subheader("7) Ringkasan Proporsi Keandalan")
if not df_reliability.empty and has_cols(df_reliability, ["keandalan_data", "count"]):
    fig_rel_pie = px.pie(
        df_reliability,
        values="count",
        names="keandalan_data",
        hole=0.5,
        color_discrete_sequence=px.colors.qualitative.Pastel,
    )
    st.plotly_chart(fig_rel_pie, use_container_width=True)
else:
    st.warning("Data ringkasan keandalan belum tersedia.")

with st.expander("Lihat data mentah dari HDFS"):
    tab_names = ["Stats", "Teknologi", "Negara", "Operator", "Top 10", "Keandalan"]
    tabs = st.tabs(tab_names)
    for tab, df in zip(tabs, [df_stats, df_tech, df_country, df_operator, df_top10, df_reliability]):
        with tab:
            if df.empty:
                st.info("Tidak ada data.")
            else:
                st.dataframe(df, use_container_width=True)
