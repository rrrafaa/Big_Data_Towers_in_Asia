import streamlit as st
import plotly.express as px
from utils.hdfs_connection import read_csv_from_hdfs

st.set_page_config(layout="wide", page_title="Analisis Operator")

st.title("🏢 Analisis Dominasi Operator ASEAN")

# Path HDFS
PATH_OP_DOM = "/Project_akhir/visualisasi_asean/profiling_cluster/Dominasi-operator"
PATH_TOP_10 = "/Project_akhir/visualisasi_asean/top_10_operator_asean"

with st.spinner("Menarik data operator dari cluster..."):
    df_op = read_csv_from_hdfs(PATH_OP_DOM)
    df_top10 = read_csv_from_hdfs(PATH_TOP_10)

if not df_op.empty:
    # 1. STANDARISASI: Paksa semua nama kolom jadi huruf kecil
    df_op.columns = [c.lower() for c in df_op.columns]
    
    # Biar tampilan di chart cantik (Cluster 0, Cluster 1, dst)
    df_op['prediction'] = "Cluster " + df_op['prediction'].astype(str)

    # --- VISUALISASI 1: SUNBURST ---
    st.subheader("1. Struktur Hirarki Network per Cluster")
    
    # KARENA DI SPARK CUMA ADA 'prediction' dan 'Network'
    # Maka path-nya HANYA boleh dua ini (setelah di-lower jadi 'network')
    fig_sun = px.sunburst(df_op, 
                          path=['prediction', 'network'], 
                          values='count',
                          color='prediction',
                          title="Peta Persaingan Network per Wilayah Cluster",
                          color_discrete_sequence=px.colors.qualitative.Prism)
    
    st.plotly_chart(fig_sun, use_container_width=True)

    # --- VISUALISASI 2: TOP 10 OPERATOR ---
    st.divider()
    st.subheader("2. Top 10 Operator Terbesar di ASEAN")
    
    if not df_top10.empty:
        # 1. Standarisasi kolom (semua jadi huruf kecil)
        df_top10.columns = [c.lower() for c in df_top10.columns]
        
        # 2. Cari kolom mana yang berisi jumlah (biasanya 'total_tower', 'count', atau 'total')
        # Kita cari kolom yang tipenya angka
        numeric_cols = df_top10.select_dtypes(include=['number']).columns.tolist()
        val_col = numeric_cols[0] if numeric_cols else None
        
        # 3. Cari kolom mana yang berisi nama (biasanya 'network' atau 'operator')
        name_cols = [c for c in df_top10.columns if c != val_col]
        label_col = name_cols[0] if name_cols else None

        if val_col and label_col:
            # Urutkan berdasarkan kolom angka yang ditemukan
            df_top10 = df_top10.sort_values(by=val_col, ascending=True).tail(10)
            
            fig_top = px.bar(df_top10, 
                             x=val_col, 
                             y=label_col, 
                             orientation='h',
                             text=val_col,
                             title="10 Besar Pemilik Menara Terbanyak",
                             color=val_col,
                             color_continuous_scale='Blues')
            
            st.plotly_chart(fig_top, use_container_width=True)
        else:
            st.warning("Format kolom data Top 10 tidak sesuai.")
    else:
        st.warning("Data Top 10 tidak ditemukan.")