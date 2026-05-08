from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# 1. INISIALISASI SPARK SESSION
spark = SparkSession.builder \
    .appName("Analisis_Dasar_Asia_Dashboard") \
    .config("spark.sql.shuffle.partitions", "200") \
    .getOrCreate()

# 2. LOAD DATA BERSIH
path_input = "hdfs://localhost:9000/Project_akhir/data_bersih"
df = spark.read.parquet(path_input)

# Path utama untuk menyimpan hasil agregasi visualisasi
PATH_VIZ = "hdfs://localhost:9000/Project_akhir/visualisasi"
# Shared Window Specification untuk perhitungan persentase berbasis Negara
window_country = Window.partitionBy("Country")

# TUJUAN NO 8: Pengelompokan Negara di Asia (Bar Chart)
region_df = df.groupBy("asia_region").count().orderBy(F.desc("count"))
region_df.coalesce(1).write.mode("overwrite").option("header", "true").csv(f"{PATH_VIZ}/asia_region")

# TUJUAN NO 5: Pertumbuhan Menara Tahunan (Line Chart)
growth_df = df.groupBy("created_year").count().orderBy("created_year")
growth_df.coalesce(1).write.mode("overwrite").option("header", "true").csv(f"{PATH_VIZ}/pertumbuhan_menara")

# TUJUAN NO 7: Top 10 Operator & Negara Dominan (Table)
# Hitung total menara per operator secara global di Asia
op_total = df.groupBy("Network").agg(F.count("*").alias("total_menara_asia"))

# Negara dengan jumlah menara terbanyak (dominan) untuk tiap operator
op_country_counts = df.groupBy("Network", "Country").agg(F.count("*").alias("cnt"))
window_op = Window.partitionBy("Network").orderBy(F.desc("cnt"))

dominant_country = op_country_counts.withColumn("rank", F.rank().over(window_op)) \
    .filter(F.col("rank") == 1) \
    .select("Network", F.col("Country").alias("negara_dominan")) \
    .dropDuplicates(["Network"])

# Menggabungkan hasil dalam bentuk tabel
top_10_final = op_total.join(dominant_country, "Network") \
    .orderBy(F.desc("total_menara_asia")) \
    .limit(10)
top_10_final.coalesce(1).write.mode("overwrite").option("header", "true").csv(f"{PATH_VIZ}/top_operator")

# TUJUAN NO 4: Hierarki Region-Negara-Operator (Sunburst)
# Agregasi tiga level: Region -> Country -> Network
sunburst_base = df.groupBy("asia_region", "Country", "Network") \
    .agg(F.count("*").alias("tower_count"))

# Hitung persentase share operator di dalam satu negara
sunburst_final = sunburst_base.withColumn(
    "total_in_country", F.sum("tower_count").over(window_country)
).withColumn(
    "percentage", (F.col("tower_count") / F.col("total_in_country")) * 100
).select(
    "asia_region", "Country", "Network", "tower_count", "percentage"
)

sunburst_final.coalesce(1).write.mode("overwrite").option("header", "true").csv(f"{PATH_VIZ}/sunburst_region_country_operator")

# TUJUAN NO 3: Perbandingan Teknologi per Negara (Stacked Bar Chart)
tech_comp_base = df.groupBy("Country", "generasi").agg(F.count("*").alias("count_tower"))

# Hitung persentase tiap generasi terhadap total menara di negara tersebut
tech_comp_final = tech_comp_base.withColumn(
    "total_towers", F.sum("count_tower").over(window_country)
).withColumn(
    "percentage", (F.col("count_tower") / F.col("total_towers")) * 100
)

# Pilih kolom akhir dan simpan untuk visualisasi
tech_comp_final.select("Country", "generasi", "count_tower", "percentage") \
    .coalesce(1).write.mode("overwrite") \
    .option("header", "true") \
    .csv(f"{PATH_VIZ}/perbandingan_teknologi")

spark.stop()