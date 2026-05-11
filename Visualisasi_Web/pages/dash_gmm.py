import streamlit as st
import plotly.express as px
from utils.hdfs_connection import read_csv_from_hdfs
from utils.ui import apply_dashboard_styles, chart_card, PALETTE, PALETTE_SCALE, style_figure

PATHS = {
    "operator": "/Project_akhir/visualisasi_asean/gmm_operator_reliability",
    "cluster": "/Project_akhir/visualisasi_asean/gmm_cluster_profile",
}

apply_dashboard_styles()
st.title("📊 Analisis Keandalan Data Menara (GMM)")
st.caption("Visualisasi profil cluster dan keandalan operator berdasarkan hasil Gaussian Mixture Model (GMM).")


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


with st.spinner("Mengambil data GMM dari HDFS..."):
    df_cluster = normalize_columns(read_csv_from_hdfs(PATHS["cluster"]))
    df_operator = normalize_columns(read_csv_from_hdfs(PATHS["operator"]))


# --- BAGIAN 1: PROFIL KARAKTERISTIK CLUSTER ---
with chart_card(
    "1) Karakteristik Cluster (Akurasi vs Kebaruan)",
    "Perbandingan rata-rata sampel (SAM) dan usia data per cluster GMM.",
):
    if not df_cluster.empty and has_cols(df_cluster, ["gmm_cluster", "avg_sam", "avg_days_old"]):
        col1, col2 = st.columns([1, 2])
        with col1:
            st.write("Tabel Rata-rata per Cluster")
            numeric_cols = [c for c in ["avg_sam"] if c in df_cluster.columns]
            if numeric_cols:
                st.dataframe(
                    df_cluster.style.highlight_max(axis=0, subset=numeric_cols),
                    use_container_width=True,
                )
            else:
                st.dataframe(df_cluster, use_container_width=True)
        with col2:
            fig_cluster = px.bar(
                df_cluster,
                x="gmm_cluster",
                y=["avg_sam", "avg_days_old"],
                barmode="group",
                labels={"value": "Skala Nilai", "variable": "Metrik"},
                color_discrete_sequence=[PALETTE[0], PALETTE[2]],
            )
            st.plotly_chart(style_figure(fig_cluster), use_container_width=True)
        st.info(
            "**Cara Membaca:** Cluster dengan **avg_sam Tinggi** dan **avg_days_old Rendah** = Data Sangat Andal (Gold). "
            "Cluster dengan **avg_sam Rendah** dan **avg_days_old Tinggi** = Data Usang (Legacy)."
        )
    else:
        miss = missing_cols(df_cluster, ["gmm_cluster", "avg_sam", "avg_days_old"])
        st.warning(f"Data cluster belum tersedia atau kolom kurang: {miss}" if miss else "Data cluster belum tersedia.")


# --- BAGIAN 2: DISTRIBUSI KEANDALAN PER OPERATOR ---
with chart_card(
    "2) Distribusi Keandalan per Operator",
    "Proporsi cluster GMM untuk setiap operator, difilter berdasarkan negara.",
):
    if not df_operator.empty and has_cols(df_operator, ["country", "network", "tower_count", "gmm_cluster"]):
        countries = sorted(df_operator["country"].unique().tolist())
        default_sel = countries[:2] if len(countries) >= 2 else countries
        selected_country = st.multiselect("Pilih Negara:", countries, default=default_sel)

        if selected_country:
            df_filtered = df_operator[df_operator["country"].isin(selected_country)]
            fig_op = px.bar(
                df_filtered,
                x="network",
                y="tower_count",
                color="gmm_cluster",
                labels={"tower_count": "Jumlah Menara", "gmm_cluster": "ID Cluster", "network": "Operator"},
                barmode="relative",
                color_continuous_scale=PALETTE_SCALE,
            )
            st.plotly_chart(style_figure(fig_op), use_container_width=True)
        else:
            st.info("Pilih minimal satu negara untuk menampilkan grafik.")
    else:
        miss = missing_cols(df_operator, ["country", "network", "tower_count", "gmm_cluster"])
        st.warning(f"Data operator belum tersedia atau kolom kurang: {miss}" if miss else "Data operator belum tersedia.")


# --- BAGIAN 3: TREEMAP HIERARKI ---
with chart_card(
    "3) Hierarki Keandalan: Negara > Operator > Cluster",
    "Treemap yang menggambarkan distribusi menara berdasarkan negara, operator, dan cluster GMM.",
):
    if not df_operator.empty and has_cols(df_operator, ["country", "network", "tower_count", "gmm_cluster"]):
        countries_tree = sorted(df_operator["country"].unique().tolist())
        default_tree = countries_tree[:2] if len(countries_tree) >= 2 else countries_tree
        selected_tree = st.multiselect(
            "Pilih Negara (Treemap):", countries_tree, default=default_tree, key="tree_country"
        )
        df_tree = df_operator[df_operator["country"].isin(selected_tree)] if selected_tree else df_operator
        if not df_tree.empty:
            fig_tree = px.treemap(
                df_tree,
                path=["country", "network", "gmm_cluster"],
                values="tower_count",
                color="gmm_cluster",
                color_continuous_scale="RdYlGn_r",
            )
            st.plotly_chart(style_figure(fig_tree), use_container_width=True)
        else:
            st.info("Tidak ada data untuk negara yang dipilih.")
    else:
        st.warning("Data operator belum tersedia untuk treemap.")


with st.expander("Lihat data mentah dari HDFS"):
    tab_cluster, tab_operator = st.tabs(["Profil Cluster", "Keandalan Operator"])
    with tab_cluster:
        if df_cluster.empty:
            st.info("Tidak ada data.")
        else:
            st.dataframe(df_cluster, use_container_width=True)
    with tab_operator:
        if df_operator.empty:
            st.info("Tidak ada data.")
        else:
            st.dataframe(df_operator, use_container_width=True)