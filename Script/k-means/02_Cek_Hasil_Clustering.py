from pyspark.sql import SparkSession

# 1. Inisialisasi Spark
spark = SparkSession.builder \
    .appName("Cek_Hasil_Clustering") \
    .getOrCreate()

# 2. Baca folder HDFS tersebut
path = "hdfs://localhost:9000/Project_akhir/hasil_clustering_asean"
df_hasil = spark.read.parquet(path)

# 3. Cek apakah benar hanya ada K=5 (cek nilai unik di kolom 'prediction')
print("Daftar Cluster yang ada di data:")
df_hasil.select("prediction").distinct().show()

# 4. Tampilkan beberapa baris data untuk melihat hasilnya
df_hasil.select("Country", "Network", "radio", "prediction").show(20)

# 5. Hitung jumlah menara per cluster (untuk profiling awal)
df_hasil.groupBy("prediction").count().orderBy("prediction").show()