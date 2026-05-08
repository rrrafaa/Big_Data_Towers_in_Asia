#  PREPROCESSING DATA MENARA SELULER ASIA
#  Dataset  : Asia towers.csv 
#  Stack    : PySpark + HDFS
#  Output   : data_bersih.parquet
#  Tujuan   : Mendukung analisis K-Means, GMM, Random Forest,
#             Window Function, dan GroupBy untuk dashboard

from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField,
    StringType, IntegerType, FloatType, LongType
)
from pyspark.ml.feature import (
    StringIndexer, VectorAssembler,
    MinMaxScaler, OneHotEncoder
)

# 1. INISIALISASI SPARK SESSION
spark = SparkSession.builder \
    .appName("CellTower_Preprocessing_Asia") \
    .config("spark.sql.shuffle.partitions", "200") \
    .config("spark.executor.memory", "4g") \
    .config("spark.driver.memory", "2g") \
    .getOrCreate()

# 2. DEFINISI SCHEMA
#    Eksplisit schema = lebih cepat untuk 13 juta baris
schema = StructType([
    StructField("index",         LongType(),    True),
    StructField("radio",         StringType(),  True),
    StructField("MCC",           IntegerType(), True),
    StructField("MNC",           IntegerType(), True),
    StructField("TAC",           IntegerType(), True),
    StructField("CID",           LongType(),    True),
    StructField("unit",          IntegerType(), True),
    StructField("LON",           FloatType(),   True),
    StructField("LAT",           FloatType(),   True),
    StructField("RANGE",         IntegerType(), True),
    StructField("SAM",           IntegerType(), True),
    StructField("changeable",    IntegerType(), True),
    StructField("created",       LongType(),    True),
    StructField("updated",       LongType(),    True),
    StructField("averageSignal", IntegerType(), True),
    StructField("Country",       StringType(),  True),
    StructField("Network",       StringType(),  True),
    StructField("Continent",     StringType(),  True),
])

# 3. INPUT HDFS
HDFS_BASE   = "hdfs://localhost:9000/Project_akhir"
HDFS_INPUT  = f"{HDFS_BASE}/Asia towers.csv"
HDFS_OUTPUT = f"{HDFS_BASE}/data_bersih"

print(f"\n  Membaca data dari HDFS : {HDFS_INPUT}")

df_raw = spark.read.csv(
    HDFS_INPUT,
    header=True,
    schema=schema
)

# 4. CLEANING DATA
KOLOM_HAPUS = ["Continent", "averageSignal", "changeable"]
df = df_raw.drop(*KOLOM_HAPUS)

# penghapusan baris data nul
KOLOM_KRUSIAL = [
    "radio", "MCC", "MNC", "TAC",
    "LON",   "LAT", "RANGE", "SAM",
    "Country", "Network", "created", "updated"
]

df_no_null = df.dropna(subset=KOLOM_KRUSIAL)

df_no_zero = df_no_null.filter(
    (F.col("MCC")   != 0) &
    (F.col("MNC")   != 0) &
    (F.col("TAC")   != 0) &
    (F.col("SAM")   != 0) &
    (F.col("RANGE") != 0)
    # LON & LAT = 0 ditangani di step filter koordinat (step 5)
)

# 7. VALIDASI KOLOM COUNTRY & NETWORK
#    - Country : hanya huruf dan spasi, minimal 2 karakter
#    - Network : boleh huruf, angka, spasi, strip, titik
#                (nama operator spt "Celcom 4G" atau "U-Mobile")
df_valid_str = df_no_zero.filter(
    F.col("Country").rlike(r"^[a-zA-Z\s]{2,}$") &
    F.col("Network").rlike(r"^[a-zA-Z0-9\s\-\.\&\+\(\)\/]{2,}$")
)

# 8. VALIDASI PRESISI DESIMAL LON & LAT - Minimal 2 angka di belakang koma.
#    Cara: cast ke string, ekstrak bagian desimal, cek panjangnya.
df_valid_coord = df_valid_str.filter(
    (
        F.length(
            F.regexp_extract(
                F.abs(F.col("LON")).cast("string"),
                r"\.(\d+)", 1
            )
        ) >= 2
    ) &
    (
        F.length(
            F.regexp_extract(
                F.abs(F.col("LAT")).cast("string"),
                r"\.(\d+)", 1
            )
        ) >= 2
    )
)

# 9. FILTER NILAI TIDAK VALID (RANGE, KOORDINAT, RADIO)
df_filtered = df_valid_coord.filter(
    # LON harus antara -180 dan 180
    (F.col("LON").between(-180, 180)) &
    # LAT harus antara -90 dan 90
    (F.col("LAT").between(-90, 90)) &
    # LON dan LAT tidak boleh 0,0 (titik di Teluk Guinea, bukan Asia)
    ~((F.col("LON") == 0) & (F.col("LAT") == 0)) &
    # RANGE tidak boleh negatif
    (F.col("RANGE") >= 0) &
    # SAM minimal 1
    (F.col("SAM") >= 1) &
    # Updated harus >= created
    (F.col("updated") >= F.col("created")) &
    # Radio hanya teknologi yang valid
    (F.col("radio").isin(["GSM", "UMTS", "LTE", "NR", "CDMA"]))
)

# 10. HAPUS DUPLIKAT
#     MCC + MNC + TAC + CID = identitas global unik satu menara
df_clean = df_filtered.dropDuplicates(["MCC", "MNC", "TAC", "CID"])

df_clean.cache()

# 11. FEATURE ENGINEERING
# 11.1 Ekstrak tahun dari Unix timestamp
df_fe = df_clean \
    .withColumn(
        "created_year",
        F.year(F.from_unixtime(F.col("created").cast(LongType())))
    ) \
    .withColumn(
        "updated_year",
        F.year(F.from_unixtime(F.col("updated").cast(LongType())))
    )

# 11.2 Flag ever_updated
#      1 = pernah diperbarui setelah pertama dibuat
#      0 = belum pernah diperbarui
df_fe = df_fe.withColumn(
    "ever_updated",
    F.when(F.col("updated") > F.col("created"), 1).otherwise(0)
)

# 11.3 Data age (detik)
#      Selisih updated - created dalam detik
#      Semakin besar = menara sudah lama dipantau → lebih andal
df_fe = df_fe.withColumn(
    "data_age",
    (F.col("updated") - F.col("created")).cast(LongType())
)

# 11.4 Generasi teknologi
df_fe = df_fe.withColumn(
    "generasi",
    F.when(F.col("radio") == "GSM",  "2G")
     .when(F.col("radio") == "CDMA", "2G")
     .when(F.col("radio") == "UMTS", "3G")
     .when(F.col("radio") == "LTE",  "4G")
     .when(F.col("radio") == "NR",   "5G")
     .otherwise("Unknown")
)

# 11.5 Kategori jangkauan sinyal
df_fe = df_fe.withColumn(
    "jangkauan",
    F.when(F.col("RANGE") <= 500,  "Urban")
     .when(F.col("RANGE") <= 2000, "Suburban")
     .otherwise("Rural")
)

# 11.6 Keandalan data berdasarkan SAM
df_fe = df_fe.withColumn(
    "keandalan_data",
    F.when(F.col("SAM") >= 10, "high")
     .when(F.col("SAM") >= 3,  "medium")
     .otherwise("low")
)

# 11.7 Pengelompokan wilayah Asia
SE_ASIA      = ["Brunei", "Cambodia", "East Timor", "Indonesia",
                "Laos", "Malaysia", "Myanmar", "Philippines",
                "Singapore", "Thailand", "Vietnam"]
EAST_ASIA    = ["China", "Hong Kong", "Japan", "Macao",
                "Mongolia", "South Korea", "Taiwan"]
SOUTH_ASIA   = ["Afghanistan", "Bangladesh", "Bhutan",
                "Maldives", "Nepal", "Pakistan", "Sri Lanka", "Diego Garcia"]
CENTRAL_ASIA = ["Kazakhstan", "Kyrgyzstan", "Tajikistan",
                "Turkmenistan", "Uzbekistan"]
WEST_ASIA    = ["Abkhazia", "Bahrain", "Iran", "Iraq", "Israel",
                "Jordan", "Kuwait", "Lebanon", "Oman",
                "Palestinian Territory", "Qatar", "Saudi Arabia",
                "Syria", "United Arab Emirates", "Yemen"]
NORTH_ASIA   = ["Russia"]

df_fe = df_fe.withColumn(
    "asia_region",
    F.when(F.col("Country").isin(SE_ASIA),      "Asia Tenggara")
     .when(F.col("Country").isin(EAST_ASIA),    "Asia Timur")
     .when(F.col("Country").isin(SOUTH_ASIA),   "Asia Selatan")
     .when(F.col("Country").isin(CENTRAL_ASIA), "Asia Tengah")
     .when(F.col("Country").isin(WEST_ASIA),    "Asia Barat")
     .when(F.col("Country").isin(NORTH_ASIA),   "Asia Utara")
     .otherwise("Lainnya")
)

# 11.8 Koordinat visualisasi (3 desimal) untuk rendering peta
df_fe = df_fe \
    .withColumn("LAT_VIS", F.round(F.col("LAT"), 3)) \
    .withColumn("LON_VIS", F.round(F.col("LON"), 3))

# 12. ENCODING
# 12.1 radio → radio_index (K-Means, Random Forest)
indexer_radio = StringIndexer(
    inputCol="radio", outputCol="radio_index", handleInvalid="keep"
)
df_enc = indexer_radio.fit(df_fe).transform(df_fe)

# 12.2 generasi → generasi_index
indexer_gen = StringIndexer(
    inputCol="generasi", outputCol="generasi_index", handleInvalid="keep"
)
df_enc = indexer_gen.fit(df_enc).transform(df_enc)

# 12.3 jangkauan → jangkauan_index
indexer_jangkauan = StringIndexer(
    inputCol="jangkauan", outputCol="jangkauan_index", handleInvalid="keep"
)
df_enc = indexer_jangkauan.fit(df_enc).transform(df_enc)

# 12.4 keandalan_data → reliability_index (GMM)
indexer_rel = StringIndexer(
    inputCol="keandalan_data", outputCol="reliability_index", handleInvalid="keep"
)
df_enc = indexer_rel.fit(df_enc).transform(df_enc)

# 12.5 asia_region → region_index
indexer_region = StringIndexer(
    inputCol="asia_region", outputCol="region_index", handleInvalid="keep"
)
df_enc = indexer_region.fit(df_enc).transform(df_enc)

# 12.6 country → country_index
indexer_country = StringIndexer(
    inputCol="Country", outputCol="country_index", handleInvalid="keep"
)
df_enc = indexer_country.fit(df_enc).transform(df_enc)

# 12.6 region_index → region_encoded (OHE vector)
#      OHE di Spark: StringIndexer dulu, baru OneHotEncoder
ohe_geo = OneHotEncoder(
    inputCols=["region_index", "country_index"],
    outputCols=["region_encoded", "country_encoded"],
    handleInvalid="keep"
)
df_enc = ohe_geo.fit(df_enc).transform(df_enc)

# 13. SCALING & VECTOR ASSEMBLY
# 13.1 features_spatial : LON, LAT, RANGE (MinMaxScaled)
#    Digunakan : K-Means (heatmap kesenjangan digital)
assembler_spatial = VectorAssembler(
    inputCols=["LON", "LAT", "RANGE"],
    outputCol="spatial_raw",
    handleInvalid="skip"
)
df_enc = assembler_spatial.transform(df_enc)

scaler_spatial = MinMaxScaler(
    inputCol="spatial_raw", outputCol="features_spatial"
)
df_enc = scaler_spatial.fit(df_enc).transform(df_enc)

# 13.2 MCC, MNC, unit di-scale 
assembler_mcc = VectorAssembler(
    inputCols=["MCC", "MNC", "unit"],
    outputCol="mcc_mnc_raw",
    handleInvalid="skip"
)
df_enc = assembler_mcc.transform(df_enc)

scaler_mcc = MinMaxScaler(
    inputCol="mcc_mnc_raw", outputCol="mcc_mnc_scaled"
)
df_enc = scaler_mcc.fit(df_enc).transform(df_enc)
print("  mcc_mnc_scaled selesai")

# 13.3 prediction_features : Vektor lengkap untuk K-Means 
# Gabungan: spatial + mcc/mnc + radio + region
assembler_pred = VectorAssembler(
    inputCols=[
        "features_spatial",  # LON, LAT, RANGE (scaled)
        "mcc_mnc_scaled",    # MCC, MNC, unit  (scaled)
        "radio_index",       # teknologi (label encoded)
        "region_encoded",     # wilayah Asia (OHE vector)
    ],
    outputCol="prediction_features",
    handleInvalid="skip"
)
df_enc = assembler_pred.transform(df_enc)

# 13.4 reliability_metrics : Vektor untuk GMM
assembler_rel = VectorAssembler(
    inputCols=["SAM", "data_age"],
    outputCol="reliability_raw",
    handleInvalid="skip"
)
df_enc = assembler_rel.transform(df_enc)

scaler_rel = MinMaxScaler(
    inputCol="reliability_raw", outputCol="reliability_metrics"
)
df_enc = scaler_rel.fit(df_enc).transform(df_enc)
print("  reliability_metrics selesai (untuk GMM)")

# 14. DATA AKHIR
KOLOM_FINAL = [
    # Identitas menara
    "index", "MCC", "MNC", "TAC", "CID", "unit",

    # Jaringan & teknologi
    "radio",             # GSM / UMTS / LTE / NR / CDMA
    "generasi",          # 2G / 3G / 4G / 5G
    "radio_index",       # encoded (ML)
    "generasi_index",    # encoded (ML)

    # Koordinat asli
    "LON", "LAT",

    # Koordinat visualisasi (3 desimal, untuk dashboard peta)
    "LON_VIS", "LAT_VIS",

    # Jangkauan
    "RANGE",
    "jangkauan",         # Urban / Suburban / Rural
    "jangkauan_index",   # encoded (ML)

    # Sample & keandalan
    "SAM",
    "keandalan_data",    # high / medium / low
    "reliability_index", # encoded (ML)

    # Waktu
    "created",
    "updated",
    "created_year",      # int tahun dibuat
    "updated_year",      # int tahun update terakhir
    "ever_updated",      # flag 0/1
    "data_age",          # detik selisih created vs updated

    # Lokasi
    "Country",
    "country_index",
    "country_encoded",
    "Network",
    "asia_region",       # Asia Tenggara / Timur / dll
    "region_index",      # encoded (ML)
    "region_encoded",    # OHE vector

    # Feature Vectors
    "features_spatial",      # Vector: LON, LAT, RANGE (scaled) → K-Means heatmap
    "prediction_features",   # Vector: lengkap → K-Means clustering
    "reliability_metrics",   # Vector: SAM + data_age (scaled)  → GMM
]

df_final = df_enc.select(KOLOM_FINAL)

# 15. PENIMPANAN
df_final.coalesce(1).write \
    .mode("overwrite") \
    .parquet(HDFS_OUTPUT)

df_clean.unpersist()
spark.stop()