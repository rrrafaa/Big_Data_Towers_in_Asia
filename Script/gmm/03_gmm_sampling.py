from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder \
    .appName("GMM_Sampling_To_HDFS") \
    .getOrCreate()

# 1. Baca data hasil clustering GMM dari HDFS
path_input = "hdfs://localhost:9000/Project_akhir/hasil_gmm_reliability"
df_gmm = spark.read.parquet(path_input)

# 2. Ambil sampel acak (misal 0.5% agar target data ~20.000 baris, pas untuk plot)
df_sampled = df_gmm.sample(False, 0.005, seed=42) 

# 3. Pilih kolom yang dibutuhkan untuk visualisasi scatter plot
df_final_sample = df_sampled.select("SAM", "data_age_days", "gmm_cluster")

# 4. SIMPAN KE HDFS (Gunakan coalesce(1) agar menjadi 1 file CSV di dalam folder HDFS)
path_output_hdfs = "hdfs://localhost:9000/Project_akhir/visualisasi_asean/gmm_scatter_sample"

df_final_sample.coalesce(1).write.mode("overwrite") \
    .option("header", "true") \
    .csv(path_output_hdfs)

print(f"Selesai! Data sampel untuk scatter plot berhasil disimpan ke HDFS: {path_output_hdfs}")
spark.stop()