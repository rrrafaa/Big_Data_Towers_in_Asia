from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.window import Window

# 1. INISIALISASI SPARK SESSION
spark = SparkSession.builder \
    .appName("Analisis_Dasar_ASEAN_Dashboard") \
    .config("spark.sql.shuffle.partitions", "200") \
    .getOrCreate()

# 2. LOAD DATA BERSIH (Pastikan path sesuai dengan output preprocessing)
path_input = "hdfs://localhost:9000/Project_akhir/data_bersih_asean"
df = spark.read.parquet(path_input)

# Path untuk menyimpan hasil agregasi visualisasi
PATH_VIZ = "hdfs://localhost:9000/Project_akhir/visualisasi_asean"
window_country = Window.partitionBy("Country")

# --- TUJUAN NO 1: Persebaran Penggunaan Teknologi Radio (Pie Chart / Global ASEAN) ---
# Mengetahui % GSM vs UMTS vs LTE vs 5G di seluruh wilayah Asia Tenggara
tech_overall = df.groupBy("radio").count()
total_asean = df.count()
tech_overall_final = tech_overall.withColumn(
    "percentage", (F.col("count") / total_asean) * 100
).orderBy(F.desc("count"))

tech_overall_final.coalesce(1).write.mode("overwrite").option("header", "true").csv(f"{PATH_VIZ}/overall_radio_distribution")

# --- TUJUAN NO 2: Perbandingan Teknologi per Negara (Stacked Bar Chart) ---
# Mengetahui di negara ASEAN ini berapa persen persebaran masing-masing teknologi
tech_comp_base = df.groupBy("Country", "radio").agg(F.count("*").alias("count_tower"))

tech_comp_final = tech_comp_base.withColumn(
    "total_towers_country", F.sum("count_tower").over(window_country)
).withColumn(
    "percentage", (F.col("count_tower") / F.col("total_towers_country")) * 100
).orderBy("Country", F.desc("percentage"))

tech_comp_final.coalesce(1).write.mode("overwrite").option("header", "true").csv(f"{PATH_VIZ}/perbandingan_teknologi_negara")

# --- TUJUAN NO 3: Hierarki Negara-Operator (Sunburst) ---
# Struktur: SE Asia (Center) -> Country -> Network
# Catatan: Kolom asia_region dihapus karena semua data adalah Asia Tenggara
sunburst_base = df.groupBy("Country", "Network") \
    .agg(F.count("*").alias("tower_count"))

sunburst_final = sunburst_base.withColumn(
    "total_in_country", F.sum("tower_count").over(window_country)
).withColumn(
    "percentage_share", (F.col("tower_count") / F.col("total_in_country")) * 100
).withColumn("region", F.lit("Asia Tenggara")) # Flag statis untuk lapisan terdalam sunburst

sunburst_final.select("region", "Country", "Network", "tower_count", "percentage_share") \
    .coalesce(1).write.mode("overwrite").option("header", "true").csv(f"{PATH_VIZ}/sunburst_asean_operator")

# --- TUJUAN NO 4: Pertumbuhan Menara Tahunan (Line Chart) ---
# Mengetahui pertumbuhan menara dari tahun ke tahun secara overall di ASEAN
growth_df = df.groupBy("created_year").count().orderBy("created_year")

growth_df.coalesce(1).write.mode("overwrite").option("header", "true").csv(f"{PATH_VIZ}/pertumbuhan_tahunan")

# --- TUJUAN NO 5: Top 10 Operator Terbesar di ASEAN (Table) ---
# Menampilkan operator, jumlah menara, dan negara di mana mereka paling dominan
op_total = df.groupBy("Network").agg(F.count("*").alias("total_menara_asean"))

# Cari negara dominan untuk tiap operator
window_op = Window.partitionBy("Network").orderBy(F.desc("cnt"))
op_country_counts = df.groupBy("Network", "Country").agg(F.count("*").alias("cnt"))

dominant_country = op_country_counts.withColumn("rank", F.rank().over(window_op)) \
    .filter(F.col("rank") == 1) \
    .select("Network", F.col("Country").alias("negara_dominan")) \
    .dropDuplicates(["Network"])

top_10_final = op_total.join(dominant_country, "Network") \
    .orderBy(F.desc("total_menara_asean")) \
    .limit(10)

top_10_final.coalesce(1).write.mode("overwrite").option("header", "true").csv(f"{PATH_VIZ}/top_10_operator_asean")

spark.stop()