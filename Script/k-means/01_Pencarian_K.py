import mlflow
import mlflow.spark
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator
from pyspark.sql import SparkSession

# 1. KONFIGURASI TRACKING MLFLOW
mlflow.set_tracking_uri("http://localhost:5000")
# Mengubah nama eksperimen agar spesifik ke ASEAN
mlflow.set_experiment("Pencarian_K_Optimal_ASEAN")

# 2. INISIALISASI SPARK SESSION
spark = SparkSession.builder \
    .appName("Eksperimen_KMeans_ASEAN_Full_Data") \
    .config("spark.driver.memory", "8g") \
    .config("spark.executor.memory", "4g") \
    .config("spark.sql.shuffle.partitions", "100") \
    .getOrCreate()

# 3. BACA DATA BERSIH ASEAN
print("Membaca data bersih ASEAN dari HDFS...")
# Menggunakan path output dari file preprocessing terbaru
path_input = "hdfs://localhost:9000/Project_akhir/data_bersih_asean"
df = spark.read.parquet(path_input).cache()

total_data = df.count()
print(f"Total data ASEAN yang akan diproses: {total_data} baris")

# 4. PROSES PENCARIAN K OPTIMAL
# Mencari jumlah klaster (K) terbaik untuk memetakan kesenjangan digital (Heatmap)
daftar_k = [3, 4, 5, 6, 7] # Ditambah k=7 untuk variasi klaster di negara ASEAN
best_silhouette = -1
best_k = -1
best_model = None

for k in daftar_k:
    with mlflow.start_run(run_name=f"ASEAN_FullData_K_{k}"):
        print(f"Menjalankan KMeans untuk K={k}...")
        
        # Menggunakan 'prediction_features' sesuai tujuan analisis kesenjangan digital
        kmeans = KMeans(featuresCol="prediction_features", k=k, seed=42)
        model = kmeans.fit(df)
        
        # Melakukan prediksi/clustering
        predictions = model.transform(df)
        
        # Evaluasi menggunakan Silhouette Score
        evaluator = ClusteringEvaluator(featuresCol="prediction_features")
        silhouette = evaluator.evaluate(predictions)
        
        # Logging ke MLflow
        mlflow.log_param("jumlah_k", k)
        mlflow.log_param("wilayah", "Asia Tenggara")
        mlflow.log_metric("silhouette_score", silhouette)
        
        print(f"K={k} selesai. Silhouette Score: {silhouette:.4f}")

        # Update model terbaik
        if silhouette > best_silhouette:
            best_silhouette = silhouette
            best_k = k
            best_model = model

# 5. SIMPAN MODEL TERBAIK KE HDFS
if best_model is not None:
    print(f"\nModel Terbaik Ditemukan: K={best_k} dengan Silhouette={best_silhouette:.4f}")
    
    with mlflow.start_run(run_name=f"Best_Model_ASEAN_K_{best_k}"):
        mlflow.log_metric("silhouette_score_terbaik", best_silhouette)
        mlflow.spark.log_model(best_model, "model_kmeans_asean_optimal")

    # Path penyimpanan model untuk digunakan di dashboard visualisasi heatmap
    path_hdfs_kmeans = "hdfs://localhost:9000/Project_akhir/k-means_asean"
    best_model.write().overwrite().save(path_hdfs_kmeans)
    print(f"Model terbaik K={best_k} berhasil disimpan ke HDFS di: {path_hdfs_kmeans}")

# 6. PENUTUP
df.unpersist()
spark.stop()