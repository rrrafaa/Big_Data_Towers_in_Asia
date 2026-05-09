# test_koneksi.py
from utils.hdfs_connection import get_hdfs_client

try:
    client = get_hdfs_client()
    folders = client.list('/')
    print("KONEKSI BERHASIL!")
    print(f"Daftar folder di root HDFS: {folders}")
    
    files = client.list('/Project_akhir/visualisasi_asean')
    print(f"AKSES BERHASIL! Ditemukan {len(files)} folder/file di visualisasi_asean.")

except Exception as e:
    print("KONEKSI GAGAL!")
    print(f"Pesan Error: {e}")