import streamlit as st
import plotly.express as px
from utils.hdfs_connection import read_csv_from_hdfs
from utils.ui import apply_dashboard_styles, chart_card, PALETTE, PALETTE_SCALE, style_figure

PATHS = {
    "stats": "/Project_akhir/visualisasi_asean/profiling_cluster/stats_utama",
    "tech": "/Project_akhir/visualisasi_asean/profiling_cluster/Dominasi-teknologi",
    "hierarchy": "/Project_akhir/visualisasi_asean/profiling_cluster/Hierarki-Cluster-Lengkap",
    "top10": "/Project_akhir/visualisasi_asean/top_10_operator_asean",
    "reliability": "/Project_akhir/visualisasi_asean/profiling_cluster/Dominiasi-keandalan",
}

TECH_COLORS = PALETTE
RELIABILITY_COLORS = PALETTE
NON_NUMERIC_CLUSTER_SORT_KEY = 999
BADGE_OPACITY_HEX = "22"


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


def format_compact(value):
    """Format angka besar ke bentuk ringkas (K/M/B)."""
    number = float(value)
    abs_number = abs(number)
    if abs_number >= 1_000_000_000:
        return f"{number / 1_000_000_000:.1f}B"
    if abs_number >= 1_000_000:
        return f"{number / 1_000_000:.1f}M"
    if abs_number >= 1_000:
        return f"{number / 1_000:.0f}K"
    return f"{number:.0f}"


def format_range_million(value):
    """Format nilai rata-rata range menjadi satuan juta (m)."""
    return f"{float(value) / 1_000_000:.3f}m"


def build_cluster_region_lookup(df_hier):
    """Bangun label area ringkas per cluster dari data hierarki."""
    if df_hier.empty or not has_cols(df_hier, ["prediction", "country", "count"]):
        return {}

    df_country = (
        df_hier.groupby(["prediction", "country"], as_index=False)["count"]
        .sum()
        .sort_values(["prediction", "count"], ascending=[True, False])
    )
    lookup = {}
    for prediction, group in df_country.groupby("prediction"):
        countries = group["country"].dropna().astype(str).head(2).tolist()
        lookup[str(prediction)] = "-".join(countries) if countries else f"Cluster {prediction}"
    return lookup

with st.spinner("Mengambil seluruh data visualisasi dari HDFS..."):
    df_stats = normalize_columns(read_csv_from_hdfs(PATHS["stats"]))
    df_tech = normalize_columns(read_csv_from_hdfs(PATHS["tech"]))
    df_hier = normalize_columns(read_csv_from_hdfs(PATHS["hierarchy"]))
    df_top10 = normalize_columns(read_csv_from_hdfs(PATHS["top10"]))
    df_reliability = normalize_columns(read_csv_from_hdfs(PATHS["reliability"]))


with chart_card(
    "Ringkasan per Cluster",
    "Ringkasan profiling cluster yang menjadi referensi peta sebaran infrastruktur.",
):
    if not df_stats.empty and has_cols(df_stats, ["prediction", "total_tower", "avg_range_radius"]):
        region_lookup = build_cluster_region_lookup(df_hier)
        summary_df = df_stats.copy()
        summary_df["prediction"] = summary_df["prediction"].astype(str)
        summary_df = summary_df.sort_values(
            by="prediction",
            key=lambda series: series.map(
                lambda value: int(value) if str(value).isdigit() else NON_NUMERIC_CLUSTER_SORT_KEY
            ),
        )

        st.markdown(
            """
            <style>
            .cluster-summary-title {
                font-size: 1.55rem;
                letter-spacing: 0.06em;
                font-weight: 700;
                color: #4c3040;
                margin: 0 0 0.8rem 0;
                text-transform: uppercase;
            }
            .cluster-summary-card {
                background: #f6f2ed;
                border-radius: 14px;
                padding: 0.9rem 1rem;
                min-height: 140px;
                border: 1px solid rgba(92, 55, 76, 0.1);
            }
            .cluster-summary-badge {
                display: inline-block;
                font-weight: 700;
                border-radius: 999px;
                padding: 0.2rem 0.7rem;
                margin-right: 0.3rem;
                font-size: 0.85rem;
            }
            .cluster-summary-area {
                font-size: 1rem;
                font-weight: 600;
                color: #4e474a;
            }
            .cluster-summary-total {
                margin-top: 0.55rem;
                margin-bottom: 0.05rem;
                font-size: 2rem;
                line-height: 1;
                font-weight: 700;
                color: #22201f;
            }
            .cluster-summary-range {
                font-size: 0.9rem;
                font-weight: 600;
                color: #3f3c3d;
                text-transform: uppercase;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="cluster-summary-title">RINGKASAN PER CLUSTER</div>', unsafe_allow_html=True)

        columns = st.columns(max(1, len(summary_df)))
        for idx, (column, row) in enumerate(zip(columns, summary_df.itertuples(index=False))):
            cluster_id = str(getattr(row, "prediction"))
            area_label = region_lookup.get(cluster_id, f"Cluster {cluster_id}")
            total_tower_label = format_compact(getattr(row, "total_tower"))
            avg_range_label = format_range_million(getattr(row, "avg_range_radius"))
            badge_bg = f"{PALETTE[idx % len(PALETTE)]}{BADGE_OPACITY_HEX}"
            badge_text = PALETTE[idx % len(PALETTE)]

            with column:
                st.markdown(
                    f"""
                    <div class="cluster-summary-card">
                        <span class="cluster-summary-badge" style="background:{badge_bg}; color:{badge_text};">C{cluster_id}</span>
                        <span class="cluster-summary-area">{area_label}</span>
                        <div class="cluster-summary-total">{total_tower_label}</div>
                        <div class="cluster-summary-range">Range avg {avg_range_label}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    else:
        miss = missing_cols(df_stats, ["prediction", "total_tower", "avg_range_radius"])
        st.warning(
            f"Data ringkasan cluster belum tersedia atau kolom kurang: {miss}"
            if miss else "Data ringkasan cluster belum tersedia."
        )


with chart_card(
    "1) Peta Sebaran Infrastruktur"
):
    if not df_stats.empty and has_cols(df_stats, ["avg_lat", "avg_lon", "total_tower", "avg_range_radius"]):
        fig_map = px.scatter_mapbox(
            df_stats,
            lat="avg_lat",
            lon="avg_lon",
            size="total_tower",
            color="avg_range_radius",
            color_continuous_scale=PALETTE_SCALE,
            zoom=3,
            mapbox_style="carto-positron",
        )
        fig_map.update_traces(marker=dict(opacity=0.85))
        fig_map.update_layout(margin={"r": 0, "t": 20, "l": 0, "b": 0})
        st.plotly_chart(fig_map, use_container_width=True)
    else:
        miss = missing_cols(df_stats, ["avg_lat", "avg_lon", "total_tower", "avg_range_radius"])
        st.warning(f"Data peta belum tersedia atau kolom kurang: {miss}" if miss else "Data peta belum tersedia.")

with chart_card(
    "2) Dominasi Teknologi per Cluster"
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


with chart_card(
    "3) Hierarki Cluster, Negara, dan Operator"
):
    if not df_hier.empty and has_cols(df_hier, ["prediction", "country", "network", "count"]):
        df_hier["prediction"] = "Cluster " + df_hier["prediction"].astype(str)
        fig_hier = px.sunburst(
            df_hier,
            path=["prediction", "country", "network"],
            values="count",
            color="prediction",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        fig_hier.update_traces(
            textinfo="label+percent entry",
            hovertemplate="<b>%{label}</b><br>Jumlah Menara: %{value}<br>Persentase: %{percentEntry:.2f}%",
        )
        st.plotly_chart(style_figure(fig_hier), use_container_width=True)
    else:
        miss = missing_cols(df_hier, ["prediction", "country", "network", "count"])
        st.warning(f"Data hierarki belum tersedia atau kolom kurang: {miss}" if miss else "Data hierarki belum tersedia.")


with chart_card(
    "4) Keandalan Data per Cluster"
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
    "5) Top 10 Operator ASEAN"
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
                color_continuous_scale=PALETTE_SCALE,
            )
            fig_top.update_traces(textposition="outside")
            st.plotly_chart(style_figure(fig_top), use_container_width=True)
        else:
            st.warning("Format data Top 10 operator belum sesuai.")
    else:
        st.warning("Data Top 10 operator belum tersedia.")


with chart_card(
    "6) Ringkasan Proporsi Keandalan"
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
    tab_names = ["Stats", "Teknologi", "Hierarki", "Top 10", "Keandalan"]
    tabs = st.tabs(tab_names)
    for tab, df in zip(tabs, [df_stats, df_tech, df_hier, df_top10, df_reliability]):
        with tab:
            if df.empty:
                st.info("Tidak ada data.")
            else:
                st.dataframe(df, use_container_width=True)
