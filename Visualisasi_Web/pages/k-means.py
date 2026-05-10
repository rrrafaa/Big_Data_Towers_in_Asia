import streamlit as st
import plotly.express as px
from utils.hdfs_connection import read_csv_from_hdfs
from utils.ui import apply_dashboard_styles, chart_card

PATHS = {
    "stats": "/Project_akhir/visualisasi_asean/profiling_cluster/stats_utama",
    "tech": "/Project_akhir/visualisasi_asean/profiling_cluster/Dominasi-teknologi",
    "country": "/Project_akhir/visualisasi_asean/profiling_cluster/Dominasi-negara",
    "operator": "/Project_akhir/visualisasi_asean/profiling_cluster/Dominasi-operator",
    "top10": "/Project_akhir/visualisasi_asean/top_10_operator_asean",
    "reliability": "/Project_akhir/visualisasi_asean/profiling_cluster/Dominasi-keandalan",
}

TECH_COLORS = ["#0f766e", "#1d4ed8", "#7c3aed", "#ea580c", "#dc2626"]
OPERATOR_COLORS = ["#0f766e", "#2563eb", "#7c3aed", "#ea580c", "#db2777"]
RELIABILITY_COLORS = ["#14532d", "#16a34a", "#84cc16", "#f59e0b", "#dc2626"]


apply_dashboard_styles()
st.title("Hasil Klusterisasi K-Means")
st.caption("Visualisasi profil cluster telekomunikasi ASEAN dengan tata letak yang lebih rapi dan fokus.")


def normalize_columns(df):
    """Standarkan nama kolom DataFrame menjadi huruf kecil agar akses kolom konsisten."""
    if df.empty:
        return df
    df.columns = [c.lower() for c in df.columns]
    return df


def has_cols(df, cols):
    """Cek apakah semua nama kolom yang dibutuhkan tersedia di DataFrame."""
    return all(col in df.columns for col in cols)


def missing_cols(df, cols):
    """Kembalikan daftar kolom yang belum tersedia pada DataFrame."""
    return [col for col in cols if col not in df.columns]


def detect_top10_columns(df):
    """Deteksi kolom label dan nilai untuk data Top 10 operator."""
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    value_candidates = ["total_tower", "count", "total"]
    label_candidates = ["network", "operator", "name"]

    value_col = next((c for c in value_candidates if c in df.columns), None)
    label_col = next((c for c in label_candidates if c in df.columns), None)

    if value_col is None and len(numeric_cols) == 1:
        value_col = numeric_cols[0]
    if label_col is None:
        non_numeric_cols = [c for c in df.columns if c not in numeric_cols]
        if len(non_numeric_cols) == 1:
            label_col = non_numeric_cols[0]

    return value_col, label_col


def style_figure(fig, margin=None):
    """Apply the shared Plotly styling used across dashboard figures."""
    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(244,247,251,0.95)",
        font=dict(color="#17324d"),
        margin=margin or dict(l=10, r=10, t=40, b=10),
    )
    return fig

with st.spinner("Mengambil seluruh data visualisasi dari HDFS..."):
    df_stats = normalize_columns(read_csv_from_hdfs(PATHS["stats"]))
    df_tech = normalize_columns(read_csv_from_hdfs(PATHS["tech"]))
    df_country = normalize_columns(read_csv_from_hdfs(PATHS["country"]))
    df_operator = normalize_columns(read_csv_from_hdfs(PATHS["operator"]))
    df_top10 = normalize_columns(read_csv_from_hdfs(PATHS["top10"]))
    df_reliability = normalize_columns(read_csv_from_hdfs(PATHS["reliability"]))


with chart_card(
    "1) Peta Sebaran Infrastruktur",
    "Peta dibuat satu baris penuh agar persebaran cluster dan intensitas tower lebih mudah dibaca.",
):
    if not df_stats.empty and has_cols(df_stats, ["avg_lat", "avg_lon", "total_tower", "avg_range_radius"]):
        fig_map = px.scatter_mapbox(
            df_stats,
            lat="avg_lat",
            lon="avg_lon",
            size="total_tower",
            color="avg_range_radius",
            color_continuous_scale="Teal",
            zoom=3,
            mapbox_style="carto-positron",
        )
        fig_map.update_traces(marker=dict(opacity=0.85))
        fig_map.update_layout(margin={"r": 0, "t": 20, "l": 0, "b": 0})
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        miss = missing_cols(df_stats, ["avg_lat", "avg_lon", "total_tower", "avg_range_radius"])
        st.warning(f"Data peta belum tersedia atau kolom kurang: {miss}" if miss else "Data peta belum tersedia.")

row2_col1, row2_col2 = st.columns(2, gap="large")
with row2_col1:
    with chart_card(
        "2) Dominasi Teknologi per Cluster",
        "Palet warna diperbarui agar perbedaan teknologi antar cluster terlihat lebih jelas.",
    ):
        if not df_tech.empty and has_cols(df_tech, ["prediction", "count", "generasi"]):
            df_tech["prediction"] = df_tech["prediction"].astype(str)
            fig_tech = px.bar(
                df_tech.sort_values(by="prediction"),
                x="prediction",
                y="count",
                color="generasi",
                barmode="stack",
                labels={"prediction": "ID Cluster", "count": "Jumlah Menara", "generasi": "Teknologi"},
                color_discrete_sequence=TECH_COLORS,
            )
            st.plotly_chart(style_figure(fig_tech), use_container_width=True)
        else:
            miss = missing_cols(df_tech, ["prediction", "count", "generasi"])
            st.warning(f"Data teknologi belum tersedia atau kolom kurang: {miss}" if miss else "Data teknologi belum tersedia.")

with row2_col2:
    with chart_card(
        "3) Komposisi Negara per Cluster",
        "Treemap dipisahkan dalam kartu tersendiri supaya pembacaan proporsi tiap cluster lebih nyaman.",
    ):
        if not df_country.empty and has_cols(df_country, ["prediction", "country", "count"]):
            df_country["prediction"] = df_country["prediction"].astype(str)
            fig_country = px.treemap(
                df_country,
                path=["prediction", "country"],
                values="count",
                color="count",
                color_continuous_scale="Sunset",
            )
            st.plotly_chart(style_figure(fig_country), use_container_width=True)
        else:
            miss = missing_cols(df_country, ["prediction", "country", "count"])
            st.warning(f"Data negara belum tersedia atau kolom kurang: {miss}" if miss else "Data negara belum tersedia.")


row3_col1, row3_col2 = st.columns([9, 11], gap="large")
with row3_col1:
    with chart_card(
        "4) Struktur Operator per Cluster",
        "Lebar kartu dibuat sedikit lebih ramping agar pilihan operator tidak terasa terlalu besar.",
    ):
        if not df_operator.empty and has_cols(df_operator, ["prediction", "network", "count"]):
            df_operator["prediction"] = "Cluster " + df_operator["prediction"].astype(str)
            fig_operator = px.sunburst(
                df_operator,
                path=["prediction", "network"],
                values="count",
                color="prediction",
                color_discrete_sequence=OPERATOR_COLORS,
            )
            st.plotly_chart(
                style_figure(fig_operator, margin=dict(l=0, r=0, t=30, b=0)),
                use_container_width=True,
            )
        else:
            miss = missing_cols(df_operator, ["prediction", "network", "count"])
            st.warning(f"Data operator belum tersedia atau kolom kurang: {miss}" if miss else "Data operator belum tersedia.")

with row3_col2:
    with chart_card(
        "5) Keandalan Data per Cluster",
        "Stacked bar dipertahankan dengan warna yang lebih kontras untuk membedakan tiap kategori keandalan.",
    ):
        if not df_reliability.empty and has_cols(df_reliability, ["prediction", "keandalan_data", "count"]):
            df_reliability["prediction"] = "Cluster " + df_reliability["prediction"].astype(str)
            fig_rel = px.bar(
                df_reliability,
                x="prediction",
                y="count",
                color="keandalan_data",
                barmode="stack",
                color_discrete_sequence=RELIABILITY_COLORS,
            )
            st.plotly_chart(style_figure(fig_rel), use_container_width=True)
        else:
            miss = missing_cols(df_reliability, ["prediction", "keandalan_data", "count"])
            st.warning(f"Data keandalan belum tersedia atau kolom kurang: {miss}" if miss else "Data keandalan belum tersedia.")


with chart_card(
    "6) Top 10 Operator ASEAN",
    "Grafik Top 10 operator tetap menggunakan satu baris penuh agar ranking operator lebih mudah dibandingkan.",
):
    if not df_top10.empty:
        value_col, label_col = detect_top10_columns(df_top10)
        if value_col and label_col:
            fig_top = px.bar(
                df_top10.sort_values(by=value_col, ascending=True).tail(10),
                x=value_col,
                y=label_col,
                orientation="h",
                text=value_col,
                color=value_col,
                color_continuous_scale="PuBuGn",
            )
            fig_top.update_traces(textposition="outside")
            st.plotly_chart(style_figure(fig_top), use_container_width=True)
        else:
            st.warning("Format data Top 10 operator belum sesuai.")
    else:
        st.warning("Data Top 10 operator belum tersedia.")


with chart_card(
    "7) Ringkasan Proporsi Keandalan",
    "Ringkasan akhir dipisahkan agar tetap memiliki jarak visual yang jelas dari grafik lainnya.",
):
    if not df_reliability.empty and has_cols(df_reliability, ["keandalan_data", "count"]):
        fig_rel_pie = px.pie(
            df_reliability,
            values="count",
            names="keandalan_data",
            hole=0.5,
            color_discrete_sequence=RELIABILITY_COLORS,
        )
        st.plotly_chart(style_figure(fig_rel_pie), use_container_width=True)
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
