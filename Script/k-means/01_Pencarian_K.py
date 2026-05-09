import mlflow
import mlflow.spark
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator
from pyspark.sql import SparkSession
from pyspark import StorageLevel

# 1. KONFIGURASI TRACKING MLFLOW
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("Pencarian_K_Optimal_ASEAN_Sampled")

# 2. INISIALISASI SPARK SESSION DENGAN OPTIMASI
spark = SparkSession.builder \
    .appName("Eksperimen_KMeans_ASEAN_Full_Data") \
    .config("spark.driver.memory", "10g") \
    .config("spark.executor.memory", "6g") \
    .config("spark.memory.fraction", "0.8") \
    .config("spark.sql.shuffle.partitions", "200") \
    .getOrCreate()

# 3. BACA DATA BERSIH ASEAN
print("Membaca data bersih ASEAN dari HDFS...")
path_input = "hdfs://localhost:9000/Project_akhir/data_bersih_asean"
df = spark.read.parquet(path_input)
df = df.cache()
total_data = df.count()
print(f"Total data ASEAN yang diproses: {total_data} baris")

# 4. PROSES PENCARIAN K OPTIMAL
daftar_k = [3, 4, 5, 6, 7]
best_silhouette = -1
best_k = -1
best_model = None

for k in daftar_k:
    with mlflow.start_run(run_name=f"ASEAN_Sample50_K_{k}"):
        print(f"Menjalankan KMeans untuk K={k}...")
        
        kmeans = KMeans(featuresCol="prediction_features", k=k, seed=42)
        model = kmeans.fit(df)
        
        predictions = model.transform(df)
        
        # Evaluasi Silhouette (Tahap paling berat)
        evaluator = ClusteringEvaluator(featuresCol="prediction_features")
        silhouette = evaluator.evaluate(predictions)
        
        mlflow.log_param("jumlah_k", k)
        mlflow.log_param("sample_fraction", 0.5)
        mlflow.log_metric("silhouette_score", silhouette)
        
        print(f"K={k} selesai. Silhouette Score: {silhouette:.4f}")

        if silhouette > best_silhouette:
            best_silhouette = silhouette
            best_k = k
            best_model = model

# 5. SIMPAN MODEL TERBAIK
if best_model is not None:
    print(f"\nModel Terbaik Ditemukan: K={best_k} dengan Silhouette={best_silhouette:.4f}")
    
    with mlflow.start_run(run_name=f"Best_Model_ASEAN_Sample50_K_{best_k}"):
        mlflow.spark.log_model(best_model, "model_kmeans_asean_optimal")

    path_hdfs_kmeans = "hdfs://localhost:9000/Project_akhir/k-means_asean"
    best_model.write().overwrite().save(path_hdfs_kmeans)
    print(f"Model berhasil disimpan.")

df.unpersist()
spark.stop()