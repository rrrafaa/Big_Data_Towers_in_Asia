from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder \
    .appName("Profiling_Cluster_ASEAN") \
    .config("spark.sql.shuffle.partitions", "50") \
    .getOrCreate()

path_input = "hdfs://localhost:9000/Project_akhir/hasil_clustering_asean"
path_output = "hdfs://localhost:9000/Project_akhir/visualisasi_asean/profiling_cluster"
df_clustered = spark.read.parquet(path_input)

# PROFILING STATISTIK UTAMA (Koordinat & Total)
# titik tengah cluster di Map/Heatmap
cluster_stat = df_clustered.groupBy("prediction") \
    .agg(
        F.avg("LAT").alias("avg_lat"),
        F.avg("LON").alias("avg_lon"),
        F.avg("RANGE").alias("avg_range_radius"),
        F.avg("SAM").alias("avg_sample_count"),
        F.avg("data_age").alias("avg_data_age"),
        F.count("*").alias("total_tower")
    ).orderBy("prediction")

cluster_stat.coalesce(1).write.mode("overwrite") \
    .option("header", "true").csv(f"{path_output}/stats_utama")

# PROFILING BERDASARKAN NEGARA (Dominasi Wilayah)
cluster_country = df_clustered.groupBy("prediction", "Country") \
    .count() \
    .orderBy("prediction", F.desc("count"))

cluster_country.coalesce(1).write.mode("overwrite") \
    .option("header", "true").csv(f"{path_output}/Dominasi-negara")

# PROFILING Dominasi Operator per Cluster
cluster_operator = df_clustered.groupBy("prediction", "Network") \
    .count() \
    .orderBy("prediction", F.desc("count"))

cluster_operator.coalesce(1).write.mode("overwrite") \
    .option("header", "true").csv(f"{path_output}/Dominasi-operator")

# PROFILING BERDASARKAN TEKNOLOGI (Radio)
cluster_tech = df_clustered.groupBy("prediction", "generasi") \
    .count() \
    .orderBy("prediction", F.desc("count"))

cluster_tech.coalesce(1).write.mode("overwrite") \
    .option("header", "true").csv(f"{path_output}/Dominasi-teknologi")

# PROFILING BERDASARKAN TIPE JANGKAUAN (Urban, Suburban, Rural)
cluster_area = df_clustered.groupBy("prediction", "jangkauan") \
    .count() \
    .orderBy("prediction", F.desc("count"))

cluster_area.coalesce(1).write.mode("overwrite") \
    .option("header", "true").csv(f"{path_output}/Dominiasi-tipe-jangkauan")

# PROFILING KEANDALAN DATA (Indikator Aktivitas Digital)
cluster_reliability = df_clustered.groupBy("prediction", "keandalan_data") \
    .count() \
    .orderBy("prediction", F.desc("count"))

cluster_reliability.coalesce(1).write.mode("overwrite") \
    .option("header", "true").csv(f"{path_output}/Dominiasi-keandalan")

spark.stop()