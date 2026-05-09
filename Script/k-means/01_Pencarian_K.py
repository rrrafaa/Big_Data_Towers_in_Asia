import mlflow
import mlflow.spark
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator
from pyspark.sql import SparkSession

# 1. KONFIGURASI TRACKING
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("Pencarian_K_Optimal_Asia")

# 2. INISIALISASI SPARK DENGAN OPTIMASI MEMORI
# Kita alokasikan RAM lebih besar untuk Driver agar sanggup menampung hasil evaluasi
spark = SparkSession.builder \
    .appName("Eksperimen_KMeans_Asia_HeavySample") \
    .config("spark.driver.memory", "8g") \
    .config("spark.executor.memory", "4g") \
    .config("spark.sql.shuffle.partitions", "50") \
    .getOrCreate()

# 3. BACA DATA
print("Membaca data dari HDFS...")
df_full = spark.read.parquet("hdfs://localhost:9000/Project_akhir/data_bersih")

# --- MENGGUNAKAN SAMPEL 20% (~2.6 Juta Baris) ---
print("Mengambil sampel 20% data (Sekitar 2.6 Juta Baris)...")
df = df_full.sample(withReplacement=False, fraction=0.2, seed=42).cache()
print(f"Total data diproses: {df.count()} baris")

daftar_k = [3, 4, 5, 6]
best_silhouette = -1
best_k = -1
best_model = None

for k in daftar_k:
    with mlflow.start_run(run_name=f"HeavySample_K_{k}"):
        print(f"Running KMeans untuk K={k}...")
        
        kmeans = KMeans(featuresCol="prediction_features", k=k, seed=42)
        model = kmeans.fit(df)
        
        predictions = model.transform(df)
        
        # Bagian ini yang paling berat untuk RAM:
        evaluator = ClusteringEvaluator(featuresCol="prediction_features")
        silhouette = evaluator.evaluate(predictions)
        
        mlflow.log_param("jumlah_k", k)
        mlflow.log_param("sample_fraction", 0.2)
        mlflow.log_metric("silhouette_score", silhouette)
        
        print(f"K={k} selesai. Silhouette: {silhouette:.4f}")

        if silhouette > best_silhouette:
            best_silhouette = silhouette
            best_k = k
            best_model = model

# 4. SIMPAN MODEL TERBAIK
if best_model is not None:
    with mlflow.start_run(run_name=f"Best_Model_HeavySample_K_{best_k}"):
        mlflow.log_metric("silhouette_score_terbaik", best_silhouette)
        mlflow.spark.log_model(best_model, "model_kmeans_optimal")

    path_hdfs_kmeans = "hdfs://localhost:9000/Project_akhir/k-means"
    best_model.write().overwrite().save(path_hdfs_kmeans)
    print(f"Model terbaik K={best_k} berhasil disimpan ke HDFS.")

spark.stop()