import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from utils.hdfs_connection import read_csv_from_hdfs
from utils.ui import apply_dashboard_styles, chart_card, PALETTE

st.set_page_config(
    page_title="Keandalan Data (GMM)",
    layout="wide"
)
apply_dashboard_styles()
PATHS_GMM = {
    "stats": "/Project_akhir/visualisasi_asean/gmm_cluster_profile/stats_utama_gmm",
    "operator": "/Project_akhir/visualisasi_asean/gmm_cluster_profile/distribusi_keandalan_operator"
}

df_stats = read_csv_from_hdfs(PATHS_GMM["stats"])
df_op_gmm = read_csv_from_hdfs(PATHS_GMM["operator"])

# Mapping nama 
GMM_LABELS = {
    0: "Klaster 0 — Keandalan Sangat Tinggi (Outlier Aktif)",
    1: "Klaster 1 — Data Andal & Sangat Segar",
    2: "Klaster 2 — Data Menengah / Segar tapi SAM Rendah",
    3: "Klaster 3 — Data Rendah / Jarang Diperbarui",
    4: "Klaster 4 — Data Sangat Rendah / Tidak Terverifikasi"
}

GMM_SHORT = {
    0: "K0 — Outlier Aktif",
    1: "K1 — Andal & Segar",
    2: "K2 — Menengah",
    3: "K3 — Jarang Diperbarui",
    4: "K4 — Sangat Rendah"
}

PALETTE_MAP = {
    "K0 — Outlier Aktif": "#FAA275",      
    "K1 — Andal & Segar": "#FF8C61",      
    "K2 — Menengah": "#CE6A85",      
    "K3 — Jarang Diperbarui": "#985277",            
    "K4 — Sangat Rendah": "#5C374C",   
}

if not df_stats.empty:
    df_stats["gmm_cluster"] = df_stats["gmm_cluster"].astype(int)
    df_stats["gmm_cluster_name"]  = df_stats["gmm_cluster"].map(GMM_LABELS)
    df_stats["gmm_cluster_short"] = df_stats["gmm_cluster"].map(GMM_SHORT)
    df_stats = df_stats.sort_values("gmm_cluster").reset_index(drop=True)

if not df_op_gmm.empty:
    df_op_gmm["gmm_cluster"] = df_op_gmm["gmm_cluster"].astype(int)
    df_op_gmm["gmm_cluster_name"]  = df_op_gmm["gmm_cluster"].map(GMM_LABELS)
    df_op_gmm["gmm_cluster_short"] = df_op_gmm["gmm_cluster"].map(GMM_SHORT)

st.title("Analisis Keandalan Data dengan GMM")
st.caption(
    "Mengukur Validitas Infrastruktur ASEAN Berdasarkan Kualitas Sinyal (SAM) dan "
    "Kedaluwarsa Data (Age Days) · Model Terbaik: **K = 5** · BIC Terbaik: -68,196,699.77"
)
st.markdown("---")

# BAGIAN 1: PROFILING STATISTIK UTAMA (METRIC CARDS)
st.subheader("Ringkasan Estimasi & Profil Volume Klaster GMM")

if not df_stats.empty:
    cols_kpi = st.columns(len(df_stats))
    for idx, row in df_stats.iterrows():
        with cols_kpi[idx]:
            st.metric(
                label=f"GMM Cluster {int(row['gmm_cluster'])}",
                value=f"{int(row['tower_count']):,}",
                delta=f"Usia: {float(row['avg_days_old']):,.0f} Hari",
                delta_color="inverse",
            )
            st.caption(f"**{row['gmm_cluster_short']}**\n\nAvg SAM: **{float(row['avg_sam']):.1f}**")
else:
    st.warning("Data 'stats_utama_gmm' gagal dimuat dari HDFS.")

st.write("#")

# BAGIAN 2 & 3: SPLIT LAYOUT (PEMETAAN GEOGRAFIS vs KARAKTERISTIK TEKNOTAMA)
# Kolom Kiri: Distribusi & Penetrasi Negara | Kolom Kanan: Bar Chart Metrik
main_col1, main_col2 = st.columns([1.3, 1.0])

# KOLOM KIRI: DISTRIBUSI GEOGRAFIS & PENETRASI OPERATOR 
with main_col1:
    st.subheader("Pemetaan & Penetrasi Keandalan Data Geografis")
    
    if not df_op_gmm.empty:
        df_country_gmm = (
            df_op_gmm
            .groupby(["Country", "gmm_cluster", "gmm_cluster_short"], as_index=False)["tower_count"]
            .sum()
            .sort_values(["Country", "gmm_cluster"])
        )

        with chart_card("Komposisi Rasio Keandalan Data Infrastruktur per Negara ASEAN", 
                        "Menilai tata kelola pembaharuan log menara operator di tiap negara"):
            fig_country = px.bar(
                df_country_gmm,
                x="Country",
                y="tower_count",
                color="gmm_cluster_short",
                color_discrete_map=PALETTE_MAP,
                barmode="relative",
                labels={"Country": "Negara ASEAN", "tower_count": "Total Menara", "gmm_cluster_short": "Status Keandalan"},
                category_orders={"gmm_cluster_short": [GMM_SHORT[k] for k in sorted(GMM_SHORT)]},
            )
            fig_country.update_layout(
                legend=dict(title="Status Keandalan", orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                margin=dict(t=50, b=10),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                height=300
            )
            fig_country.update_xaxes(showgrid=False)
            fig_country.update_yaxes(showgrid=True, gridcolor="#f0f0f0", tickformat=",")
            st.plotly_chart(fig_country, use_container_width=True)

        with chart_card("Matriks Detail Sebaran Kualitas Data Menara Berdasarkan Operator Telekomunikasi", 
                        "Ukuran lingkaran mewakili volume total aset menara seluler"):
            
            fcol1, fcol2 = st.columns(2)
            with fcol1:
                all_countries = sorted(df_op_gmm["Country"].unique().tolist())
                sel_country = st.selectbox("Filter Negara", options=["Semua Negara"] + all_countries)
            with fcol2:
                all_clusters = sorted(df_op_gmm["gmm_cluster"].unique().tolist())
                cluster_options = {GMM_SHORT[k]: k for k in all_clusters}
                sel_cluster_label = st.selectbox("Filter Klaster Keandalan", options=["Semua Klaster"] + list(cluster_options.keys()))

            df_scatter = df_op_gmm.copy()
            if sel_country != "Semua Negara":
                df_scatter = df_scatter[df_scatter["Country"] == sel_country]
            if sel_cluster_label != "Semua Klaster":
                df_scatter = df_scatter[df_scatter["gmm_cluster"] == cluster_options[sel_cluster_label]]

            if df_scatter.empty:
                st.info("Tidak ada kecocokan data komparatif untuk kombinasi filter ini.")
            else:
                fig_scatter = px.scatter(
                    df_scatter,
                    x="Country",
                    y="Network",
                    size="tower_count",
                    color="gmm_cluster_short",
                    color_discrete_map=PALETTE_MAP,
                    size_max=35,
                    category_orders={"gmm_cluster_short": [GMM_SHORT[k] for k in sorted(GMM_SHORT)]},
                    hover_data={"Country": True, "Network": True, "gmm_cluster_short": True, "tower_count": ":,"},
                    labels={"gmm_cluster_short": "Status Keandalan", "Network": "Provider Jaringan", "Country": "Negara", "tower_count": "Aset Menara"},
                )
                fig_scatter.update_layout(
                    height=350,
                    legend=dict(title="Status Keandalan", orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
                    margin=dict(t=50, b=10),
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                )
                fig_scatter.update_xaxes(showgrid=True, gridcolor="#f0f0f0")
                fig_scatter.update_yaxes(showgrid=True, gridcolor="#f0f0f0")
                st.plotly_chart(fig_scatter, use_container_width=True)
    else:
        st.warning("Data 'distribusi_keandalan_operator' gagal dimuat.")

# KOLOM KANAN: KARAKTERISTIK TEKNIS METRIK GMM
with main_col2:
    st.subheader("Profil Komposisi Fitur Teoretis")
    
    if not df_stats.empty:
        # Chart Atas: Kepadatan Sinyal (SAM)
        with chart_card("Perbandingan Kepadatan Sinyal (SAM) antar Klaster", 
                        "Semakin tinggi bar, tingkat akurasi pengukuran sinyal semakin valid"):
            fig_sam = px.bar(
                df_stats,
                x="gmm_cluster_short",
                y="avg_sam",
                color="gmm_cluster_short",
                color_discrete_map=PALETTE_MAP,
                text=df_stats["avg_sam"].apply(lambda v: f"{v:.1f}"),
                labels={"gmm_cluster_short": "Klaster GMM", "avg_sam": "Rata-rata SAM"},
            )
            fig_sam.update_traces(textposition="outside", showlegend=False)
            fig_sam.update_layout(
                margin=dict(t=20, b=10),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                height=300
            )
            fig_sam.update_xaxes(showgrid=False, categoryorder="category ascending")
            fig_sam.update_yaxes(showgrid=True, gridcolor="#f0f0f0")
            st.plotly_chart(fig_sam, use_container_width=True)

        # Chart Bawah: Usia Data (Days Old)
        with chart_card("Perbandingan Usia Data (Days Old) antar Klaster", 
                        "Semakin pendek bar, data menara seluler semakin segar (up-to-date)"):
            fig_age = px.bar(
                df_stats,
                x="gmm_cluster_short",
                y="avg_days_old",
                color="gmm_cluster_short",
                color_discrete_map=PALETTE_MAP,
                text=df_stats["avg_days_old"].apply(lambda v: f"{v:,.0f}"),
                labels={"gmm_cluster_short": "Klaster GMM", "avg_days_old": "Rata-rata Usia Data (Hari)"},
            )
            fig_age.update_traces(textposition="outside", showlegend=False)
            fig_age.update_layout(
                margin=dict(t=20, b=10),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                height=300
            )
            fig_age.update_xaxes(showgrid=False, categoryorder="category ascending")
            fig_age.update_yaxes(showgrid=True, gridcolor="#f0f0f0")
            st.plotly_chart(fig_age, use_container_width=True)

st.markdown("---")

# BAGIAN 4: INSIGHT & AUDIT DATA MENTAH
st.subheader("Ringkasan Insight & Audit Data Mentah")

# Expander Insight Ringkasan GMM
with st.expander("Interpretasi Hasil Clustering Model GMM", expanded=False):
    st.markdown("""
| Klaster GMM | Avg SAM | Avg Usia Data | Interpretasi Keandalan Infrastruktur |
|---|---|---|---|
| **K0 — Outlier Aktif** | ~367.2 | ~3,769 hari | Pengukuran sinyal super aktif/padat, siklus pembaruan log sangat lama. |
| **K1 — Andal & Segar** | ~80.0 | ~5,496 hari | Tingkat akurasi tinggi, record data historis stabil. |
| **K2 — Menengah** | ~22.4 | ~693 hari | **Klaster Ter-segar**; Infrastruktur ekspansi baru (di bawah 2 tahun). |
| **K4 — Jarang Diperbarui** | ~12.2 | ~2,424 hari | Kualitas sampel sinyal menengah ke bawah dengan siklus update lambat. |
| **K5 — Sangat Rendah** | ~5.0 | ~2,829 hari | **Dominasi Terbesar**; Rekaman data minim, memerlukan crowdsourcing ulang. |

**Kesimpulan Utama:** Pemodelan GMM berhasil mengklasifikasikan data berdasarkan densitas sinyal dan umur log untuk memisahkan infrastruktur yang dipelihara dengan aktif dari yang membutuhkan re-mapping spasial.
""")

# Expander Data Mentah
with st.expander("Hasil Komputasi Agregasi Spark GMM Langsung dari HDFS"):
    tab1, tab2 = st.tabs(["Tabel Statistik Utama", "Tabel Distribusi Komplit Vendor"])
    
    with tab1:
        if not df_stats.empty:
            display_stats = df_stats[["gmm_cluster", "gmm_cluster_name", "avg_sam", "avg_days_old", "tower_count"]].rename(
                columns={"gmm_cluster": "Klaster", "gmm_cluster_name": "Label Klaster", "avg_sam": "Avg SAM", "avg_days_old": "Avg Usia Data (Hari)", "tower_count": "Jumlah Menara"}
            )
            st.dataframe(
                display_stats.style.format({"Avg SAM": "{:.2f}", "Avg Usia Data (Hari)": "{:,.0f}", "Jumlah Menara": "{:,}"}),
                use_container_width=True, hide_index=True
            )
            
    with tab2:
        if not df_op_gmm.empty:
            t2_country = st.selectbox("Filter Negara (Tabel)", options=["Semua"] + sorted(df_op_gmm["Country"].unique().tolist()))
            df_vendor_display = df_op_gmm.copy()
            if t2_country != "Semua":
                df_vendor_display = df_vendor_display[df_vendor_display["Country"] == t2_country]
                
            display_vendor = df_vendor_display[["Country", "Network", "gmm_cluster", "gmm_cluster_name", "tower_count"]].rename(
                columns={"Country": "Negara", "Network": "Operator", "gmm_cluster": "Klaster", "gmm_cluster_name": "Label Klaster", "tower_count": "Jumlah Menara"}
            ).sort_values(["Negara", "Operator", "Klaster"])
            
            st.dataframe(
                display_vendor.style.format({"Jumlah Menara": "{:,}"}),
                use_container_width=True, hide_index=True, height=350
            )