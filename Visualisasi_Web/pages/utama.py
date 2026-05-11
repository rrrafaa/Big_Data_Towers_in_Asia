import streamlit as st
import plotly.express as px

from utils.hdfs_connection import read_csv_from_hdfs
from utils.ui import apply_dashboard_styles, chart_card, PALETTE, PALETTE_SCALE, style_figure


PATHS = {
    "stats": "/Project_akhir/visualisasi_asean/profiling_cluster/stats_utama",
    "tech": "/Project_akhir/visualisasi_asean/profiling_cluster/Dominasi-teknologi",
    "hierarchy": "/Project_akhir/visualisasi_asean/profiling_cluster/Hierarki-Cluster-Lengkap",
    "reliability": "/Project_akhir/visualisasi_asean/profiling_cluster/Dominiasi-keandalan",
    "coverage": "/Project_akhir/visualisasi_asean/profiling_cluster/Dominiasi-tipe-jangkauan",
}

CLUSTER_LABELS = {
    0: "C0 - Filipina",
    1: "C1 - Indonesia Barat",
    2: "C2 - Malaysia-Singapura",
    3: "C3 - Daratan (Mainland)",
    4: "C4 - Kalimantan-Brunei",
}

SHORT_CLUSTER_LABELS = {
    0: "C0 Filipina",
    1: "C1 Ind-Barat",
    2: "C2 Mal-Sing",
    3: "C3 Mainland",
    4: "C4 Kali-Brunei",
}

TOWER_DISPLAY_THRESHOLD = 1000
MODERNIZATION_COLORS = {"2G": PALETTE[4], "4G + 5G": PALETTE[1]}

st.set_page_config(layout="wide", page_title="Halaman Utama Cluster")
apply_dashboard_styles()

st.title("Cluster Wilayah Menara di Asia")
st.caption("Dashboard ini menyajikan analisis terkait hasil dari clustering menara asia dengan menggunakan model k-means. Data yang ditampilkan mencakup karakteristik cluster, dominasi teknologi, keandalan data, tipe jangkauan, serta hierarki negara dan operator di setiap cluster. Informasi ini dapat digunakan untuk memahami profil infrastruktur menara di berbagai wilayah Asia Tenggara.")


def normalize_columns(df):
    if df.empty:
        return df
    df.columns = [col.lower() for col in df.columns]
    return df


def has_cols(df, cols):
    return all(col in df.columns for col in cols)


def missing_cols(df, cols):
    return [col for col in cols if col not in df.columns]


def normalize_cluster_id(value):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return value


def cluster_label(value, short=False):
    cluster_id = normalize_cluster_id(value)
    labels = SHORT_CLUSTER_LABELS if short else CLUSTER_LABELS
    return labels.get(cluster_id, f"Cluster {cluster_id}")


def cluster_region_name(value):
    label = cluster_label(value)
    return label.split(" - ", 1)[1] if " - " in label else label


def render_cluster_card(cluster_id, total_tower, avg_range):
    tower_value = float(total_tower)
    tower_int = int(round(tower_value))
    if tower_int < TOWER_DISPLAY_THRESHOLD:
        tower_text = str(tower_int)
    elif tower_int % TOWER_DISPLAY_THRESHOLD == 0:
        tower_text = f"{int(tower_int / TOWER_DISPLAY_THRESHOLD)}K"
    else:
        tower_text = f"{tower_int / TOWER_DISPLAY_THRESHOLD:.1f}K"

    st.markdown(
        f"""
        <div style="
            background-color: #fdfcf5;
            border-radius: 14px;
            padding: 16px;
            border: 1px solid #eee;
            box-shadow: 2px 2px 6px rgba(0,0,0,0.03);
            min-height: 154px;">
            <span style="
                background-color: #e8f0fe;
                color: #1967d2;
                padding: 2px 8px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 0.78em;">C{cluster_id}</span>
            <span style="font-size: 0.9em; margin-left: 6px; color: #555;">{cluster_region_name(cluster_id)}</span>
            <h3 style="margin: 16px 0 8px 0; color: #222; font-size: 2em;">{tower_text}</h3>
            <p style="font-size: 0.8em; color: #666; margin: 0;">Avg Coverage Radius</p>
            <p style="font-size: 0.95em; color: #666; margin: 4px 0 0 0;"><strong>{avg_range:.3f}m</strong></p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def prepare_modernization_profile(df_tech):
    if df_tech.empty or not has_cols(df_tech, ["prediction", "generasi", "count"]):
        return df_tech

    df_profile = df_tech.copy()
    df_profile["prediction"] = df_profile["prediction"].apply(normalize_cluster_id)
    df_profile["generasi"] = (
        df_profile["generasi"].astype(str).str.replace(" ", "", regex=False).str.upper()
    )
    df_profile["bucket"] = None
    df_profile.loc[df_profile["generasi"].eq("2G"), "bucket"] = "2G"
    df_profile.loc[df_profile["generasi"].isin(["4G", "5G"]), "bucket"] = "4G + 5G"
    df_profile = df_profile[df_profile["bucket"].notna()]

    if df_profile.empty:
        return df_profile

    cluster_totals = (
        df_tech.assign(prediction=df_tech["prediction"].apply(normalize_cluster_id))
        .groupby("prediction", as_index=False)["count"]
        .sum()
        .rename(columns={"count": "cluster_total"})
    )

    df_profile = (
        df_profile.groupby(["prediction", "bucket"], as_index=False)["count"]
        .sum()
        .merge(cluster_totals, on="prediction", how="left")
    )
    df_profile["percentage"] = (df_profile["count"] / df_profile["cluster_total"]) * 100
    df_profile["cluster_name"] = df_profile["prediction"].apply(lambda value: cluster_label(value, short=True))
    return df_profile.sort_values(["prediction", "bucket"])


with st.spinner("Mengambil seluruh data visualisasi dari HDFS..."):
    df_stats = normalize_columns(read_csv_from_hdfs(PATHS["stats"]))
    df_tech = normalize_columns(read_csv_from_hdfs(PATHS["tech"]))
    df_hier = normalize_columns(read_csv_from_hdfs(PATHS["hierarchy"]))
    df_reliability = normalize_columns(read_csv_from_hdfs(PATHS["reliability"]))
    df_coverage = normalize_columns(read_csv_from_hdfs(PATHS["coverage"]))

left_col, right_col = st.columns([1, 2], gap="large")

with left_col:
    with chart_card("Dominasi Teknologi per Cluster"):
        if not df_tech.empty and has_cols(df_tech, ["prediction", "count", "generasi"]):
            tech_chart = df_tech.copy()
            tech_chart["prediction"] = tech_chart["prediction"].apply(normalize_cluster_id)
            tech_chart["cluster_name"] = tech_chart["prediction"].apply(cluster_label)
            fig_tech = px.bar(
                tech_chart.sort_values("prediction"),
                x="cluster_name",
                y="count",
                color="generasi",
                barmode="stack",
                labels={"cluster_name": "Kluster Wilayah", "count": "Jumlah Menara", "generasi": "Teknologi"},
                color_discrete_sequence=PALETTE,
            )
            fig_tech.update_layout(height=290, legend_title_text="Teknologi")
            st.plotly_chart(style_figure(fig_tech, margin=dict(l=10, r=10, t=40, b=70)), use_container_width=True)

            st.caption("Dari chart ini terlihat bahwa setiap cluster memiliki dominasi dengan teknologi 3G. Namun, cluster C3 menunjukkan dominasi di setiap teknologi pada tower yang terdata. Dan terlihat bahwa teknologi 5G Sangat kecil sehingga tidak begitu telihat jika dikombinasikan dengan teknologi lain yang jumlahnya jauh lebih banyak. Hal ini menunjukkan bahwa modernisasi infrastruktur menara di Asia Tenggara masih dalam tahap awal, dengan sebagian besar menara masih menggunakan teknologi 3G, dan hanya sedikit yang sudah beralih ke 4G atau 5G. -- Cluster C3 yang menunjukkan dominasi di setiap teknologi pada tower yang terdata bisa jadi merupakan cluster yang lebih maju dalam hal adopsi teknologi, atau mungkin memiliki lebih banyak menara secara keseluruhan. Sementara itu, dominasi 3G di sebagian besar cluster menunjukkan bahwa banyak wilayah masih bergantung pada teknologi yang lebih lama, yang bisa menjadi tantangan untuk peningkatan kecepatan dan kapasitas jaringan di masa depan.")
        else:
            st.warning(f"Data teknologi belum lengkap: {missing_cols(df_tech, ['prediction', 'count', 'generasi'])}")

    with chart_card("Keandalan Data per Cluster"):
        if not df_reliability.empty and has_cols(df_reliability, ["prediction", "keandalan_data", "count"]):
            reliability_chart = df_reliability.copy()
            reliability_chart["prediction"] = reliability_chart["prediction"].apply(normalize_cluster_id)
            reliability_chart["cluster_name"] = reliability_chart["prediction"].apply(cluster_label)
            fig_rel = px.bar(
                reliability_chart.sort_values("prediction"),
                x="cluster_name",
                y="count",
                color="keandalan_data",
                barmode="stack",
                labels={"cluster_name": "Kluster Wilayah", "count": "Jumlah Menara", "keandalan_data": "Keandalan"},
                color_discrete_sequence=PALETTE,
            )
            fig_rel.update_layout(height=260, legend_title_text="Keandalan")
            st.plotly_chart(style_figure(fig_rel, margin=dict(l=10, r=10, t=40, b=45)), use_container_width=True)

            st.caption("Keandalan data menara di setiap cluster menunjukkan variasi yang signifikan. Cluster C3 memiliki proporsi menara dengan keandalan tinggi yang lebih besar dibandingkan cluster lainnya, yang mengartikan bahwa data terkait dengan tower memiliki lebih banyak sampel dan lebih terbaru. Namun, cluster C0 menunjukkan proporsi menara dengan keandalan rendah yang lebih besar, yang bisa berarti bahwa data terkait tower di cluster ini memiliki lebih sedikit sampel atau lebih tua. Cluster C1, C2, dan C4 menunjukkan campuran antara keandalan tinggi dan rendah, yang mungkin mencerminkan variasi dalam kualitas data di dalam cluster tersebut. Perbedaan ini bisa disebabkan oleh faktor-faktor seperti lokasi geografis, tingkat urbanisasi, atau infrastruktur jaringan yang berbeda di setiap cluster.")
        else:
            st.warning(f"Data keandalan belum lengkap: {missing_cols(df_reliability, ['prediction', 'keandalan_data', 'count'])}")

    with chart_card("Profil 2G vs 4G + 5G (Kesenjangan Modernisasi)"):
        df_profile = prepare_modernization_profile(df_tech)
        if not df_profile.empty and has_cols(df_profile, ["cluster_name", "bucket", "percentage"]):
            fig_profile = px.bar(
                df_profile,
                x="cluster_name",
                y="percentage",
                color="bucket",
                barmode="group",
                labels={"cluster_name": "Kluster Wilayah", "percentage": "Persentase", "bucket": "Profil"},
                color_discrete_map=MODERNIZATION_COLORS,
            )
            fig_profile.update_layout(height=250, yaxis_ticksuffix="%")
            st.plotly_chart(style_figure(fig_profile, margin=dict(l=10, r=10, t=40, b=45)), use_container_width=True)
            st.caption("Profil modernisasi infrastruktur menara di setiap cluster menunjukkan bahwa sebagian besar menara masih menggunakan teknologi 2G, dengan persentase yang bervariasi antara cluster. Cluster C2 dan C3 memiliki persentase tertinggi untuk teknologi 4G + 5G, yang menunjukkan bahwa cluster ini mungkin lebih maju dalam adopsi teknologi baru dibandingkan cluster lainnya. Sementara itu, cluster C4 memiliki persentase tertinggi untuk teknologi 2G, yang bisa menunjukkan bahwa cluster ini masih sangat bergantung pada teknologi lama. Cluster C0, C1 menunjukkan campuran antara kedua teknologi, yang mungkin mencerminkan proses transisi yang sedang berlangsung di wilayah tersebut.")
        else:
            st.warning("Data profil 2G vs 4G + 5G belum dapat dibentuk dari data dominasi teknologi.")

    with chart_card("Distribusi Tipe Jangkauan per Cluster"):
        if not df_coverage.empty and has_cols(df_coverage, ["prediction", "jangkauan", "count"]):
            coverage_chart = df_coverage.copy()
            coverage_chart["prediction"] = coverage_chart["prediction"].apply(normalize_cluster_id)
            coverage_chart["cluster_name"] = coverage_chart["prediction"].apply(cluster_label)
            fig_coverage = px.sunburst(
                coverage_chart,
                path=["cluster_name", "jangkauan"],
                values="count",
                color="cluster_name",
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
            fig_coverage.update_layout(height=420)
            st.plotly_chart(style_figure(fig_coverage, margin=dict(l=10, r=10, t=40, b=10)), use_container_width=True)
            st.caption("Distribusi tipe jangkauan per cluster menunjukkan bahwa sebagian besar menara di setiap cluster memiliki jangkauan suburban, yang bisa mencerminkan konsentrasi infrastruktur menara di area pertengahan, tidak dalam perkotaan namun juga tidak berada di dearah perdesaan. Namun, terdapat variasi dalam proporsi jangkauan suburban dan rural di setiap cluster. Cluster C3 memiliki proporsi jangkauan suburban yang lebih besar dibandingkan cluster lainnya, yang mungkin menunjukkan bahwa cluster ini mencakup wilayah dengan karakteristik campuran antara urban dan suburban.")
        else:
            st.warning(f"Data jangkauan belum lengkap: {missing_cols(df_coverage, ['prediction', 'jangkauan', 'count'])}")

with right_col:
    with chart_card("Peta Sebaran & Ringkasan Infrastruktur"):
        if not df_stats.empty and has_cols(df_stats, ["prediction", "avg_lat", "avg_lon", "total_tower", "avg_range_radius"]):
            stats_chart = df_stats.copy()
            stats_chart["prediction"] = stats_chart["prediction"].apply(normalize_cluster_id)
            stats_chart["cluster_info"] = stats_chart["prediction"].apply(cluster_label)
            stats_sorted = stats_chart.sort_values("prediction")

            cards = st.columns(len(stats_sorted))
            for idx, (_, row) in enumerate(stats_sorted.iterrows()):
                with cards[idx]:
                    render_cluster_card(
                        cluster_id=row["prediction"],
                        total_tower=row["total_tower"],
                        avg_range=row["avg_range_radius"],
                    )

            fig_map = px.scatter_mapbox(
                stats_chart,
                lat="avg_lat",
                lon="avg_lon",
                size="total_tower",
                color="avg_range_radius",
                color_continuous_scale=PALETTE_SCALE,
                hover_name="cluster_info",
                zoom=3,
                mapbox_style="carto-positron",
                labels={"avg_range_radius": "Avg Range Radius"},
            )
            fig_map.update_traces(marker=dict(opacity=0.85))
            fig_map.update_layout(margin=dict(l=0, r=0, t=10, b=0), height=620)
            st.plotly_chart(fig_map, use_container_width=True)

            st.caption("Peta sebaran menara berdasarkan rata-rata lokasi geografis (latitude dan longitude) menunjukkan distribusi menara di wilayah Asia Tenggara. Ukuran titik pada peta mewakili jumlah menara di setiap cluster, dengan titik yang lebih besar menunjukkan cluster dengan jumlah menara yang lebih banyak. Warna titik mewakili rata-rata radius jangkauan menara di setiap cluster, dengan warna yang lebih gelap menunjukkan jangkauan yang lebih luas. Dari peta ini, terlihat bahwa cluster C3 memiliki konsentrasi menara yang tinggi dengan jangkauan yang luas, sementara cluster C4 memiliki konsentrasi menara yang lebih rendah dengan jangkauan yang lebih kecil. Cluster lainnya menunjukkan variasi dalam jumlah menara dan jangkauan, mencerminkan karakteristik geografis dan infrastruktur yang berbeda di setiap cluster.")
        else:
            st.warning(f"Data statistik belum lengkap: {missing_cols(df_stats, ['prediction', 'avg_lat', 'avg_lon', 'total_tower', 'avg_range_radius'])}")

    with chart_card("Hierarki Cluster, Negara, dan Operator"):
        if not df_hier.empty and has_cols(df_hier, ["prediction", "country", "network", "count"]):
            hier_chart = df_hier.copy()
            hier_chart["prediction"] = hier_chart["prediction"].apply(cluster_label)
            fig_hier = px.sunburst(
                hier_chart,
                path=["prediction", "country", "network"],
                values="count",
                color="prediction",
                color_discrete_sequence=px.colors.qualitative.Pastel,
            )
            fig_hier.update_traces(
                textinfo="label+percent entry",
                hovertemplate="<b>%{label}</b><br>Jumlah Menara: %{value}<br>Persentase: %{percentEntry:.2f}%<extra></extra>",
            )
            fig_hier.update_layout(height=730)
            st.plotly_chart(style_figure(fig_hier, margin=dict(l=10, r=10, t=40, b=10)), use_container_width=True)

            st.caption("Hierarki cluster, negara, dan operator menunjukkan distribusi menara berdasarkan wilayah, negara, dan operator. Setiap cluster memiliki kontribusi yang berbeda dari berbagai negara dan operator. Misalnya, cluster C3 mungkin didominasi oleh beberapa negara dengan operator tertentu, sementara cluster lain mungkin memiliki distribusi yang lebih merata di antara beberapa negara dan operator. Informasi ini dapat memberikan wawasan tentang konsentrasi infrastruktur menara di wilayah tertentu dan bagaimana operator berperan dalam penyediaan layanan telekomunikasi di setiap cluster.")
        else:
            st.warning(f"Data hierarki belum lengkap: {missing_cols(df_hier, ['prediction', 'country', 'network', 'count'])}")

st.write("---")  # Garis pemisah horizontal
st.subheader("Insight Yang Dapat Diambil dari Analisis Cluster")
st.error("Prioritas 1 — Cluster 4 adalah *alarm merah* kesenjangan digital. Meski jumlah menara paling kecil (195K), ia mencakup wilayah geografis yang sangat beragam: Kalimantan Tengah/Timur, Brunei, hingga East Timor. Adopsi 4G hanya 14.2% (terendah ASEAN), keandalan data *high* hanya 12.5%, dan proporsi rural 7.6%. Kecilnya jumlah tower di kawasan yang luas menandakan blank spot nyata. Cluster ini sangat rentan terhadap ketimpangan akses digital, terutama di daerah pedalaman Kalimantan dan Brunei yang memiliki tantangan geografis. Prioritas utama harus diberikan untuk meningkatkan infrastruktur di cluster ini, dengan fokus pada peningkatan adopsi 4G/5G, memperbaiki keandalan data, dan memperluas jangkauan ke wilayah rural untuk mengurangi kesenjangan digital yang signifikan di kawasan ini.")
st.error("Prioritas 2 — Cluster 3 (Thailand, Vietnam, Myanmar, Laos, Kamboja)paradoks skala. Ini cluster terbesar (1.5 juta menara), tapi radius rata-rata tertinggi (1.825m) justru berarti tower tersebar sangat tipis di area daratan luas: Thailand, Vietnam, Myanmar, Laos, Kamboja. Masih ada 15.9% menara 2G aktif, artinya jutaan pengguna di wilayah ini belum terupgrade ke internet mobile modern. Keandalan data *high* hanya 28.5% (tertinggi ASEAN), tapi masih ada 51.2% menara dengan keandalan *low*. Cluster ini menunjukkan tantangan besar dalam hal modernisasi infrastruktur dan kualitas data, meskipun memiliki jumlah menara yang sangat besar. Fokus harus diberikan pada peningkatan adopsi teknologi 4G/5G, serta upaya untuk meningkatkan keandalan data, terutama di wilayah rural yang mungkin memiliki akses terbatas ke infrastruktur telekomunikasi.")
st.warning("Cluster 1 (Indonesia Barat: Jawa, Sumatera): memperlihatkan kesenjangan kualitas, bukan kuantitas. Volume besar (944K tower), tapi 51.2% keandalan *low* dan 4G hanya 16.7%. Jawa dan Sumatera padat penduduk, tapi kualitas dan modernisasi sinyal belum sebanding dengan kepadatan penggunanya. Cluster ini menunjukkan bahwa meskipun memiliki jumlah menara yang besar, kualitas dan modernisasi infrastruktur masih menjadi tantangan. Prioritas harus diberikan untuk meningkatkan keandalan data dan mempercepat adopsi teknologi 4G/5G, terutama di daerah perkotaan yang padat penduduk untuk memastikan layanan yang memadai bagi pengguna.")
st.success("Cluster 2 (Malaysia, Singapura) adalah benchmark. Dengan 50% adopsi 4G/5G dan keandalan tertinggi, ia menjadi tolok ukur yang realistis untuk negara ASEAN lain karena berada di konteks regional yang sama. Meskipun jumlah menara lebih sedikit dibandingkan cluster lain, kualitas dan modernisasi infrastruktur di cluster ini menunjukkan bahwa peningkatan signifikan masih mungkin dicapai dengan fokus pada peningkatan adopsi teknologi dan keandalan data.")


with st.expander("Lihat data mentah"):
    tabs = st.tabs(["Stats", "Teknologi", "Hierarki", "Keandalan", "Jangkauan"])
    for tab, df in zip(tabs, [df_stats, df_tech, df_hier, df_reliability, df_coverage]):
        with tab:
            if df.empty:
                st.info("Tidak ada data.")
            else:
                st.dataframe(df, use_container_width=True)
