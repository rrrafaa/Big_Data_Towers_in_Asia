import mlflow
import mlflow.spark
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator
from pyspark.sql import SparkSession

import sys
import io
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# 1. KONFIGURASI TRACKING MLFLOW
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("Pencarian_K_Optimal_ASEAN_Full")

# 2. INISIALISASI SPARK SESSION (Optimasi Memori)
spark = SparkSession.builder \
    .appName("Training_KMeans_ASEAN_Full") \
    .config("spark.driver.memory", "10g") \
    .config("spark.executor.memory", "6g") \
    .config("spark.memory.fraction", "0.8") \
    .config("spark.sql.shuffle.partitions", "200") \
    .getOrCreate()

# 3. BACA DATA (Output dari Preprocessing)
path_input = "hdfs://localhost:9000/Project_akhir/data_bersih_asean"
print(f"Membaca data dari: {path_input}")
df = spark.read.parquet(path_input)

# Cache data agar proses looping K lebih cepat
df = df.cache()
total_data = df.count()
print(f"Total data yang akan dilatih: {total_data} baris")

# 4. PROSES PENCARIAN K OPTIMAL
daftar_k = [3, 4, 5, 6]
best_silhouette = -1
best_k = -1
best_model = None
best_predictions = None

for k in daftar_k:
    with mlflow.start_run(run_name=f"Training_K_{k}"):
        
        # Latih model pada 100% data
        kmeans = KMeans(featuresCol="prediction_features", k=k, seed=42)
        model = kmeans.fit(df)
        
        # Prediksi pada 100% data (untuk mendapatkan label cluster)
        predictions_full = model.transform(df)
        
        # Evaluasi Silhouette menggunakan 10% sampel (Trik agar tidak Pending/Hang)
        df_sample_eval = predictions_full.sample(False, 0.1, seed=42)
        evaluator = ClusteringEvaluator(featuresCol="prediction_features")
        silhouette = evaluator.evaluate(df_sample_eval)
        
        # Logging ke MLflow
        mlflow.log_param("k", k)
        mlflow.log_metric("silhouette_score", silhouette)
        print(f"Selesai K={k} | Silhouette: {silhouette:.4f}")
        
        # Simpan model & prediksi jika ini yang terbaik
        if silhouette > best_silhouette:
            best_silhouette = silhouette
            best_k = k
            best_model = model
            best_predictions = predictions_full

# 5. SIMPAN HASIL CLUSTERING (100% DATA) DAN MODEL TERBAIK
if best_model is not None:
    print(f"\nModel Terbaik: K={best_k} (Silhouette: {best_silhouette:.4f})")
    
    # Simpan hasil prediksi 100% data ke HDFS untuk di-profiling nanti
    path_output_full = "hdfs://localhost:9000/Project_akhir/hasil_clustering_asean"
    best_predictions.write.mode("overwrite").parquet(path_output_full)
    print(f"Hasil clustering 100% data disimpan ke: {path_output_full}")
    
    # Log model final ke MLflow
    with mlflow.start_run(run_name=f"Final_Best_Model_K_{best_k}"):
        mlflow.spark.log_model(best_model, "model_kmeans_asean_optimal")

spark.stop()