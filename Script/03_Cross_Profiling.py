from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder \
    .appName("CrossAnalysis_KMeans_GMM") \
    .config("spark.sql.shuffle.partitions", "50") \
    .getOrCreate()

df_base = spark.read.parquet("hdfs://localhost:9000/Project_akhir/hasil_clustering_asean")

current_timestamp = 1715360400
df_kmeans = df_base.withColumn("data_age_days", 
    F.when((F.lit(current_timestamp) - F.col("updated")) / 86400 < 0, 0)
    .otherwise((F.lit(current_timestamp) - F.col("updated")) / 86400)
).select(
    "index", "prediction", "Country", "Network",
    "generasi", "jangkauan", "keandalan_data",
    "SAM", "data_age_days", "LAT", "LON", "RANGE"
)
df_gmm = spark.read.parquet(
    "hdfs://localhost:9000/Project_akhir/hasil_gmm_reliability"
).select("index", "gmm_cluster")

# 2. JOIN BERDASARKAN index TOWER
df_combined = df_kmeans.join(df_gmm, on="index", how="inner")
df_combined.cache()

PATH_OUT = "hdfs://localhost:9000/Project_akhir/visualisasi_asean/cross_analysis"

# 3. PROFILING A — CROSS TABLE UTAMA
#    KMeans Cluster × GMM Cluster → Matriks kesenjangan 5×K
cross_matrix = df_combined \
    .groupBy("prediction", "gmm_cluster") \
    .agg(
        F.count("index").alias("tower_count"),
        F.avg("SAM").alias("avg_sam"),
        F.avg("data_age_days").alias("avg_age_days"),
        F.avg("RANGE").alias("avg_range")
    ) \
    .orderBy("prediction", "gmm_cluster")

cross_matrix.coalesce(1).write.mode("overwrite") \
    .option("header", "true") \
    .csv(f"{PATH_OUT}/cross_matrix_utama")

# 4. PROFILING B — ZONA KRITIS
#    Tower yang SEKALIGUS: k-means 4 & gmm 4

# Perhitungan GMM "terbengkalai" --masih pertanyaan
gmm_profile = df_combined.groupBy("gmm_cluster").agg(
    F.avg("SAM").alias("avg_sam"),
    F.avg("data_age_days").alias("avg_age_days"),
    F.count("index").alias("tower_count")
).orderBy("avg_sam")  

# Ambil gmm_cluster dengan avg_sam terendah secara programatik
gmm_cluster_terbengkalai = gmm_profile.first()["gmm_cluster"]
print(f"GMM Cluster Terbengkalai (SAM terendah): {gmm_cluster_terbengkalai}")

# Filter zona kritis: K-Means C4 + GMM terbengkalai
zona_kritis = df_combined.filter(
    (F.col("prediction") == 4) &
    (F.col("gmm_cluster") == gmm_cluster_terbengkalai)
)

zona_kritis_summary = zona_kritis \
    .groupBy("Country", "Network") \
    .agg(
        F.count("index").alias("tower_count"),
        F.avg("SAM").alias("avg_sam"),
        F.avg("data_age_days").alias("avg_age_days"),
        F.avg("RANGE").alias("avg_range")
    ) \
    .orderBy(F.asc("avg_sam"))  # Mengurutkan dari yang terbengkalai

zona_kritis_summary.coalesce(1).write.mode("overwrite") \
    .option("header", "true") \
    .csv(f"{PATH_OUT}/zona_kritis_c4_gmm")

# 5. PROFILING C — SKOR KESENJANGAN PER NEGARA
#    Composite Digital Gap Score per negara
#    Score tinggi = kesenjangan lebih parah

# Hitung total tower per negara sebagai pembagi
total_per_country = df_combined.groupBy("Country") \
    .agg(F.count("index").alias("total_tower"))

# Hitung komponen skor
gap_components = df_combined.groupBy("Country") \
    .agg(
        F.count("index").alias("total_tower"),
        F.avg("RANGE").alias("avg_range"),
        F.avg("SAM").alias("avg_sam"),
        F.avg("data_age_days").alias("avg_age_days"),
        # Proporsi 2G (teknologi tertinggal)
        (F.sum(F.when(F.col("generasi") == "2G", 1).otherwise(0)) /
         F.count("index") * 100).alias("pct_2g"),
        # Proporsi keandalan rendah
        (F.sum(F.when(F.col("keandalan_data") == "low", 1).otherwise(0)) /
         F.count("index") * 100).alias("pct_low_reliability"),
        # Proporsi 4G+5G (modernisasi)
        (F.sum(F.when(F.col("generasi").isin(["4G", "5G"]), 1).otherwise(0)) /
         F.count("index") * 100).alias("pct_modern"),
        # Proporsi rural
        (F.sum(F.when(F.col("jangkauan") == "Rural", 1).otherwise(0)) /
         F.count("index") * 100).alias("pct_rural"),
        # Proporsi tower di GMM cluster terbengkalai
        (F.sum(F.when(F.col("gmm_cluster") == gmm_cluster_terbengkalai, 1).otherwise(0)) /
         F.count("index") * 100).alias("pct_gmm_abandoned")
    )

# Hitung composite score (semua dinormalisasi 0-100, score tinggi = buruk)
# Formula: rata-rata tertimbang indikator negatif - bonus modernisasi
gap_score = gap_components.withColumn(
    "digital_gap_score",
    (
        F.col("pct_2g") * 0.25 +
        F.col("pct_low_reliability") * 0.25 +
        F.col("pct_rural") * 0.20 +
        F.col("pct_gmm_abandoned") * 0.20 -
        F.col("pct_modern") * 0.10 
    )
).orderBy(F.desc("digital_gap_score"))

gap_score.coalesce(1).write.mode("overwrite") \
    .option("header", "true") \
    .csv(f"{PATH_OUT}/digital_gap_score_per_negara")

# 6. PROFILING D — DISTRIBUSI GMM PER NEGARA
#    Negara mana yang tower-nya paling banyak masuk cluster "terbengkalai" GMM?
gmm_per_negara = df_combined \
    .groupBy("Country", "gmm_cluster") \
    .agg(F.count("index").alias("tower_count")) \
    .orderBy("Country", "gmm_cluster")

gmm_per_negara.coalesce(1).write.mode("overwrite") \
    .option("header", "true") \
    .csv(f"{PATH_OUT}/gmm_distribusi_per_negara")

# 7. PROFILING E — CROSS: TEKNOLOGI × GMM
#    Apakah tower 2G lebih banyak di GMM "terbengkalai"? untuk membuktikan korelasi teknologi tua ↔ data tidak andal
tech_vs_gmm = df_combined \
    .groupBy("generasi", "gmm_cluster") \
    .agg(F.count("index").alias("tower_count")) \
    .orderBy("generasi", "gmm_cluster")

tech_vs_gmm.coalesce(1).write.mode("overwrite") \
    .option("header", "true") \
    .csv(f"{PATH_OUT}/teknologi_vs_gmm_cluster")

df_combined.unpersist()
spark.stop()