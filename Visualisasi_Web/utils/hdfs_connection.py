from hdfs import InsecureClient
import pandas as pd
import io
import streamlit as st

def get_hdfs_client():
    return InsecureClient('http://localhost:9870', user='marit')

@st.cache_data # Cache agar dashboard ga lemot waktu refresh
def read_csv_from_hdfs(path_hdfs):
    client = get_hdfs_client()
    try:
        files = client.list(path_hdfs)
        csv_file = [f for f in files if f.endswith('.csv')][0]
        full_path = f"{path_hdfs}/{csv_file}"
        
        with client.read(full_path) as reader:
            return pd.read_csv(io.BytesIO(reader.read()))
    except Exception as e:
        st.error(f"Gagal membaca HDFS: {e}")
        return pd.DataFrame()