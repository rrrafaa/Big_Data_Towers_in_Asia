from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import *
from pyspark.ml.feature import (
    StringIndexer, VectorAssembler,
    MinMaxScaler, OneHotEncoder
)

# 1. INISIALISASI
spark = SparkSession.builder \
    .appName("CellTower_Preprocessing_ASEAN_Full_Logic") \
    .config("spark.sql.shuffle.partitions", "200") \
    .getOrCreate()

# 2. DEFINISI SCHEMA & INPUT
schema = StructType([
    StructField("index", LongType(), True), StructField("radio", StringType(), True),
    StructField("MCC", IntegerType(), True), StructField("MNC", IntegerType(), True),
    StructField("TAC", IntegerType(), True), StructField("CID", LongType(), True),
    StructField("unit", IntegerType(), True), StructField("LON", FloatType(), True),
    StructField("LAT", FloatType(), True), StructField("RANGE", IntegerType(), True),
    StructField("SAM", IntegerType(), True), StructField("changeable", IntegerType(), True),
    StructField("created", LongType(), True), StructField("updated", LongType(), True),
    StructField("averageSignal", IntegerType(), True), StructField("Country", StringType(), True),
    StructField("Network", StringType(), True), StructField("Continent", StringType(), True),
])

HDFS_INPUT  = "hdfs://localhost:9000/Project_akhir/Asia towers.csv"
HDFS_OUTPUT = "hdfs://localhost:9000/Project_akhir/data_bersih_asean"

df_raw = spark.read.csv(HDFS_INPUT, header=True, schema=schema)

# 3. FILTER AWAL: ASIA TENGGARA
SE_ASIA = ["Brunei", "Cambodia", "East Timor", "Indonesia", "Laos", 
           "Malaysia", "Myanmar", "Philippines", "Singapore", "Thailand", "Vietnam"]

df = df_raw.filter(F.col("Country").isin(SE_ASIA))
df = df.drop("Continent", "averageSignal", "changeable")

# 4. PENGHAPUSAN BARIS NULL (KOLOM KRUSIAL)
KOLOM_KRUSIAL = [
    "radio", "MCC", "MNC", "TAC", "LON", "LAT", 
    "RANGE", "SAM", "Country", "Network", "created", "updated"
]
df_no_null = df.dropna(subset=KOLOM_KRUSIAL)

# 5. FILTER NILAI NOL
df_no_zero = df_no_null.filter(
    (F.col("MCC")   != 0) &
    (F.col("MNC")   != 0) &
    (F.col("TAC")   != 0) &
    (F.col("SAM")   != 0) &
    (F.col("RANGE") != 0)
)

# 6. VALIDASI FORMAT STRING (COUNTRY & NETWORK)
df_valid_str = df_no_zero.filter(
    F.col("Country").rlike(r"^[a-zA-Z\s]{2,}$") &
    F.col("Network").rlike(r"^[a-zA-Z0-9\s\-\.\&\+\(\)\/]{2,}$")
)

# 7. VALIDASI PRESISI DESIMAL (MIN 2 ANGKA BELAKANG KOMA)
df_valid_coord = df_valid_str.filter(
    (F.length(F.regexp_extract(F.abs(F.col("LON")).cast("string"), r"\.(\d+)", 1)) >= 2) &
    (F.length(F.regexp_extract(F.abs(F.col("LAT")).cast("string"), r"\.(\d+)", 1)) >= 2)
)

# 8. FILTER VALIDITAS TEKNIS & AREA ASEAN
df_filtered = df_valid_coord.filter(
    (F.col("LON").between(90, 145)) & 
    (F.col("LAT").between(-11, 28)) & 
    (F.col("updated") >= F.col("created")) & # Logika data_age
    (F.col("radio").isin(["GSM", "UMTS", "LTE", "NR", "CDMA"]))
)

# 9. HAPUS DUPLIKAT & CACHE
df_clean = df_filtered.dropDuplicates(["MCC", "MNC", "TAC", "CID"])
df_clean.cache()

# 10. FEATURE ENGINEERING
df_fe = df_clean \
    .withColumn("created_year", F.year(F.from_unixtime(F.col("created")))) \
    .withColumn("data_age", (F.col("updated") - F.col("created")).cast(LongType())) \
    .withColumn("ever_updated", F.when(F.col("updated") > F.col("created"), 1).otherwise(0)) \
    .withColumn("generasi", 
        F.when(F.col("radio").isin(["GSM", "CDMA"]), "2G")
         .when(F.col("radio") == "UMTS", "3G")
         .when(F.col("radio") == "LTE", "4G")
         .when(F.col("radio") == "NR", "5G").otherwise("Unknown")) \
    .withColumn("jangkauan", 
        F.when(F.col("RANGE") <= 500, "Urban")
         .when(F.col("RANGE") <= 2000, "Suburban").otherwise("Rural")) \
    .withColumn("keandalan_data", 
        F.when(F.col("SAM") >= 10, "high")
         .when(F.col("SAM") >= 3, "medium").otherwise("low")) \
    .withColumn("LAT_VIS", F.round(F.col("LAT"), 3)) \
    .withColumn("LON_VIS", F.round(F.col("LON"), 3))

# 11. ENCODING
indexer_radio = StringIndexer(inputCol="radio", outputCol="radio_index", handleInvalid="keep")
df_enc = indexer_radio.fit(df_fe).transform(df_fe)

indexer_gen = StringIndexer(inputCol="generasi", outputCol="generasi_index", handleInvalid="keep")
df_enc = indexer_gen.fit(df_enc).transform(df_enc)

indexer_jangkauan = StringIndexer(inputCol="jangkauan", outputCol="jangkauan_index", handleInvalid="keep")
df_enc = indexer_jangkauan.fit(df_enc).transform(df_enc)

indexer_rel = StringIndexer(inputCol="keandalan_data", outputCol="reliability_index", handleInvalid="keep")
df_enc = indexer_rel.fit(df_enc).transform(df_enc)

indexer_country = StringIndexer(inputCol="Country", outputCol="country_index", handleInvalid="keep")
df_enc = indexer_country.fit(df_enc).transform(df_enc)

# 11.1 ONE HOT ENCODING (Hanya Country karena Region sudah seragam)
ohe_geo = OneHotEncoder(inputCols=["country_index"], outputCols=["country_encoded"], handleInvalid="keep")
df_enc = ohe_geo.fit(df_enc).transform(df_enc)

# 12. SCALING & VECTOR ASSEMBLY
# A. Spatial (Heatmap)
assembler_spatial = VectorAssembler(inputCols=["LON", "LAT", "RANGE"], outputCol="spatial_raw")
df_enc = assembler_spatial.transform(df_enc)
scaler_spatial = MinMaxScaler(inputCol="spatial_raw", outputCol="features_spatial")
df_enc = scaler_spatial.fit(df_enc).transform(df_enc)

# B. Identitas (MCC, MNC, Unit)
assembler_mcc = VectorAssembler(inputCols=["MCC", "MNC", "unit"], outputCol="mcc_mnc_raw")
df_enc = assembler_mcc.transform(df_enc)
scaler_mcc = MinMaxScaler(inputCol="mcc_mnc_raw", outputCol="mcc_mnc_scaled")
df_enc = scaler_mcc.fit(df_enc).transform(df_enc)

# C. Prediction Features (Lengkap untuk K-Means & RF)
# Menggunakan country_encoded sebagai pengganti region_encoded
assembler_pred = VectorAssembler(
    inputCols=["features_spatial", "mcc_mnc_scaled", "radio_index", "country_encoded"],
    outputCol="prediction_features"
)
df_enc = assembler_pred.transform(df_enc)

# D. Reliability Metrics (GMM)
assembler_rel = VectorAssembler(inputCols=["SAM", "data_age"], outputCol="reliability_raw")
df_enc = assembler_rel.transform(df_enc)
scaler_rel = MinMaxScaler(inputCol="reliability_raw", outputCol="reliability_metrics")
df_enc = scaler_rel.fit(df_enc).transform(df_enc)

# 13. PENYIMPANAN AKHIR
KOLOM_FINAL = [
    "index", "MCC", "MNC", "TAC", "CID", "unit", "radio", "radio_index", 
    "generasi", "generasi_index", "LON", "LAT", "LON_VIS", "LAT_VIS", 
    "RANGE", "jangkauan", "jangkauan_index", "SAM", "keandalan_data", 
    "reliability_index", "created", "updated", "created_year", "ever_updated", 
    "data_age", "Country", "country_index", "country_encoded", "Network",
    "features_spatial", "prediction_features", "reliability_metrics"
]

df_final = df_enc.select(KOLOM_FINAL)

df_final.coalesce(1).write.mode("overwrite").parquet(HDFS_OUTPUT)

df_clean.unpersist()
spark.stop()