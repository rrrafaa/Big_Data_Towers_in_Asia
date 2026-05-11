from pyspark.sql import SparkSession
from pyspark.sql import functions as F

spark = SparkSession.builder.appName("GMM_Profiling").getOrCreate()
df_gmm = spark.read.parquet("hdfs://localhost:9000/Project_akhir/hasil_gmm_reliability")

# Profiling per Cluster
profiling_cluster = df_gmm.groupBy("gmm_cluster").agg(
    F.avg("SAM").alias("avg_sam"),
    F.avg("data_age").alias("avg_age"),
    F.count("index").alias("tower_count")
).orderBy("avg_sam", ascending=False)

# Simpan untuk Dashboard
profiling_cluster.write.mode("overwrite").csv("hdfs://localhost:9000/Project_akhir/dashboard/gmm_cluster_profile", header=True)

# Profiling per Operator (Siapa paling andal?)
op_reliability = df_gmm.groupBy("Network", "gmm_cluster").count()
op_reliability.write.mode("overwrite").csv("hdfs://localhost:9000/Project_akhir/dashboard/gmm_operator_reliability", header=True)