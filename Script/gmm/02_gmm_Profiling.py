from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder.appName("GMM_Profiling_Final").getOrCreate()

path_gmm = "hdfs://localhost:9000/Project_akhir/hasil_gmm_reliability"
df_gmm = spark.read.parquet(path_gmm)

# 2. PROFILING PER CLUSTER (Mendefinisikan Karakteristik Cluster)
profiling_cluster = df_gmm.groupBy("gmm_cluster").agg(
    F.avg("SAM").alias("avg_sam"),
    F.avg("data_age_days").alias("avg_days_old"),
    F.count("index").alias("tower_count")
).orderBy("avg_sam", ascending=False) 

profiling_cluster.coalesce(1).write.mode("overwrite") \
    .option("header", "true") \
    .csv("hdfs://localhost:9000/Project_akhir/visualisasi_asean/gmm_cluster_profile")

# 3. PROFILING PER OPERATOR & NEGARA (Siapa Paling Andal?)
op_reliability = df_gmm.groupBy("Country", "Network", "gmm_cluster").agg(
    F.count("index").alias("tower_count")
)

op_reliability.coalesce(1).write.mode("overwrite") \
    .option("header", "true") \
    .csv("hdfs://localhost:9000/Project_akhir/visualisasi_asean/gmm_operator_reliability")