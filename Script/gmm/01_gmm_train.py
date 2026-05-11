import mlflow
import mlflow.spark
from pyspark.ml.clustering import GaussianMixture
from pyspark.sql import SparkSession
from pyspark.sql import functions as F

# 1. INISIALISASI
mlflow.set_tracking_uri("http://localhost:5000")
mlflow.set_experiment("GMM_Reliability_Analysis")

spark = SparkSession.builder \
    .appName("Training_GMM_ASEAN") \
    .config("spark.driver.memory", "10g") \
    .getOrCreate()

# 2. BACA DATA (Output dari Preprocessing)
path_input = "hdfs://localhost:9000/Project_akhir/data_bersih_asean"
df = spark.read.parquet(path_input).cache()

# 3. PENCARIAN K OPTIMAL (GMM Components)
best_ll = -float('inf')
best_k = 2
best_model = None

for k in range(2, 6):  # Mencoba cluster 2 sampai 5
    with mlflow.start_run(run_name=f"GMM_K_{k}"):
        gmm = GaussianMixture(k=k, featuresCol="reliability_metrics", predictionCol="gmm_cluster", seed=42)
        model = gmm.fit(df)
        
        # Log Likelihood: Metrik utama GMM
        summary = model.summary
        ll = summary.logLikelihood

        # BIC: Bayesian Information Criterion untuk evaluasi model
        num_features = df.select("reliability_metrics").first()[0].size
        n = df.count()
        k_params = (k * num_features) + (k - 1) 
        import math
        bic = k_params * math.log(n) - 2 * ll

        mlflow.log_param("k", k)
        mlflow.log_metric("log_likelihood", ll)
        mlflow.log_metric("BIC", bic)
        
        print(f"K={k} | Log Likelihood: {ll} | BIC: {bic:.4f}")

        if ll > best_ll:
            best_ll = ll
            best_k = k
            best_model = model

# 4. SIMPAN HASIL DAN MODEL
if best_model is not None:
    predictions = best_model.transform(df)
    path_output = "hdfs://localhost:9000/Project_akhir/hasil_gmm_reliability"
    predictions.write.mode("overwrite").parquet(path_output)
    
    # Simpan Model ke MLflow
    mlflow.spark.log_model(best_model, "gmm_best_model")

df.unpersist()
spark.stop()