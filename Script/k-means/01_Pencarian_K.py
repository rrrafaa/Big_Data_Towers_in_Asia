import mlflow
import mlflow.spark
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator
from pyspark.sql import SparkSession

mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("Pencarian_K_Optimal_Asia")

# 1. INISIALISASI
spark = SparkSession.builder \
    .appName("Eksperimen_KMeans_Asia") \
    .config("spark.sql.shuffle.partitions", "200") \
    .getOrCreate()

df = spark.read.parquet("hdfs://localhost:9000/Project_akhir/data_bersih")

# Daftar nilai K yang ingin dicoba
daftar_k = [3, 4, 5, 6]

for k in daftar_k:
    with mlflow.start_run(run_name=f"KMeans_K_{k}"):
        
        # 3. TRAINING MODEL
        kmeans = KMeans(featuresCol="prediction_features", k=k, seed=42)
        model = kmeans.fit(df)
        
        # 4. PREDIKSI
        predictions = model.transform(df)
        
        # 5. EVALUASI (Silhouette Score)
        evaluator = ClusteringEvaluator(featuresCol="prediction_features")
        silhouette = evaluator.evaluate(predictions)
        
        # 6. LOGGING KE MLFLOW
        mlflow.log_param("jumlah_k", k)
        mlflow.log_metric("silhouette_score", silhouette)

        mlflow.spark.log_model(model, "model_kmeans")
spark.stop()