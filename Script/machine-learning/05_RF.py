#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import findspark
findspark.init()

import mlflow
import mlflow.spark
from pyspark.sql import SparkSession
from pyspark.sql import functions as F
from pyspark.ml.feature import VectorAssembler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.evaluation import MulticlassClassificationEvaluator
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder

def main():
    # Inisialisasi Spark Session & MLflow
    mlflow.set_tracking_uri("http://localhost:5000")
    mlflow.set_experiment("RF_Classification_CellTower_ASEAN")

    # Konfigurasi memori dioptimalkan untuk dialokasikan kembali via spark-submit
    spark = SparkSession.builder \
        .appName("Production_RandomForest_ASEAN_V2") \
        .config("spark.sql.shuffle.partitions", "200") \
        .getOrCreate()

    try:
        # Memuat Data dari HDFS & Join
        path_kmeans = "hdfs://localhost:9000/Project_akhir/hasil_clustering_asean"
        path_gmm = "hdfs://localhost:9000/Project_akhir/hasil_gmm_reliability"

        df_kmeans = spark.read.parquet(path_kmeans)
        df_gmm = spark.read.parquet(path_gmm)

        # Join data berdasarkan kolom index
        df_rf_input = df_kmeans.join(
            df_gmm.select("index", "gmm_cluster"), 
            on="index", 
            how="inner"
        )

        df_rf_input = df_rf_input.cache()
        total_records = df_rf_input.count()

        # Analisis Cross Profiling
        print(">>> Memulai analisis Cross Profiling...")
        path_cross_profile = "hdfs://localhost:9000/Project_akhir/visualisasi_asean/cross_profiling_output"

        cross_matrix = df_rf_input.groupBy("prediction", "gmm_cluster") \
            .agg(
                F.count("index").alias("tower_count"),
                F.avg("SAM").alias("avg_sam"),
                F.avg("data_age_days").alias("avg_days_old"),
                F.avg("RANGE").alias("avg_range_radius")
            ).orderBy("prediction", "gmm_cluster")

        cross_matrix.coalesce(1).write.mode("overwrite") \
            .option("header", "true") \
            .csv(path_cross_profile)

        print(">>> Analisis Cross Profiling selesai. Menampilkan 30 baris pertama:")
        cross_matrix.show(30)

        # Rekayasa Fitur (Feature Engineering)
        # Cast gmm_cluster ke DoubleType agar kompatibel dengan VectorAssembler
        df_rf_input = df_rf_input.withColumn("gmm_cluster", F.col("gmm_cluster").cast("double"))

        # Fitur teknis independen (Tanpa LON, LAT, RANGE mentah)
        fitur_klasifikasi = [
            "SAM",             # kualitas pengukuran sinyal
            "data_age_days",   # tingkat pembaruan data
            "radio_index",     # teknologi radio (encoded)
            "country_index",   # negara (encoded)
            "generasi_index",  # generasi jaringan (encoded)
            "jangkauan_index", # tipe jangkauan urban/suburban/rural (encoded dari RANGE)
            "gmm_cluster"      # profil keandalan dari GMM
        ]

        assembler_rf = VectorAssembler(
            inputCols=fitur_klasifikasi,
            outputCol="rf_features",
            handleInvalid="skip"
        )
        df_rf_ready = assembler_rf.transform(df_rf_input)

        # Target label menggunakan hasil zonasi K-Means murni (prediction)
        df_rf_ready = df_rf_ready.withColumn("target_label", F.col("prediction").cast("double"))
        train_data, test_data = df_rf_ready.randomSplit([0.8, 0.2], seed=42)
        train_data = train_data.cache()
        test_data = test_data.cache()
        
        # Training 5-Fold Cross Validation
        with mlflow.start_run(run_name="RF_Zonasi_CrossValidation"):
            
            rf = RandomForestClassifier(
                featuresCol="rf_features",
                labelCol="target_label",
                predictionCol="prediction_rf",
                seed=42
            )

            # Pendefinisian Evaluator Utama (Mengoptimalkan F1-Score)
            evaluator_cv = MulticlassClassificationEvaluator(
                labelCol="target_label", 
                predictionCol="prediction_rf", 
                metricName="f1"
            )

            # Parameter Grid untuk Tuning Ringan (1 Kombinasi)
            paramGrid = ParamGridBuilder() \
                .addGrid(rf.numTrees, [50]) \
                .addGrid(rf.maxDepth, [8]) \
                .build()

            # CrossValidator dengan 5-Fold (Parallelism=1 agar RAM stabil)
            cv = CrossValidator(
                estimator=rf,
                estimatorParamMaps=paramGrid,
                evaluator=evaluator_cv,
                numFolds=5,
                seed=42,
                parallelism=1
            )

            cv_model = cv.fit(train_data)
            best_rf_model = cv_model.bestModel
            
            # Pengujian keakuratan model ke Data Test yang murni belum pernah dilihat model
            print(">>> Melakukan prediksi pada data test...")
            predictions = best_rf_model.transform(test_data)
            predictions = predictions.cache()
            predictions.count()  # Pemicu cache

            # Evaluasi metrik akhir murni
            def get_metric(metric_name):
                return MulticlassClassificationEvaluator(
                    labelCol="target_label", 
                    predictionCol="prediction_rf", 
                    metricName=metric_name
                ).evaluate(predictions)

            print(">>> Menghitung metrik evaluasi...")
            accuracy  = get_metric("accuracy")
            precision = get_metric("weightedPrecision")
            recall    = get_metric("weightedRecall")
            f1_score  = get_metric("f1")

            # Logging parameter terbaik dan metrik ke MLflow
            mlflow.log_param("best_numTrees", best_rf_model.getNumTrees)
            mlflow.log_param("best_maxDepth", best_rf_model.getOrDefault("maxDepth"))
            mlflow.log_param("fitur_digunakan", str(fitur_klasifikasi))
            mlflow.log_metric("cv_test_accuracy",  accuracy)
            mlflow.log_metric("cv_test_precision", precision)
            mlflow.log_metric("cv_test_recall",    recall)
            mlflow.log_metric("cv_test_f1_score",  f1_score)
            mlflow.spark.log_model(best_rf_model, "random_forest_best_model")

            # Confusion Matrix & Menyimpan Hasil Akhir ke HDFS
            print("\n>>> Membuat Confusion Matrix:")
            confusion_matrix = predictions.groupBy("target_label") \
                .pivot("prediction_rf") \
                .count() \
                .na.fill(0) \
                .orderBy("target_label")
            confusion_matrix.show()

            print(">>> Menyimpan model terbaik ke HDFS...")
            path_model_rf = "hdfs://localhost:9000/Project_akhir/model_rf_klasifikasi"
            best_rf_model.write().overwrite().save(path_model_rf)

            print(">>> Menyimpan file hasil prediksi komplit ke HDFS...")
            path_pred_out = "hdfs://localhost:9000/Project_akhir/visualisasi_asean/rf_prediction_output"
            output_cols = [
                "index", "LAT", "LON", "Country", "Network", "radio", "generasi", "jangkauan", 
                "RANGE", "SAM", "data_age_days", "prediction", "gmm_cluster", "prediction_rf"
            ]

            predictions.select(output_cols) \
                .withColumnRenamed("prediction", "kmeans_target_cluster") \
                .withColumnRenamed("prediction_rf", "rf_predicted_cluster") \
                .coalesce(1).write.mode("overwrite") \
                .option("header", "true") \
                .csv(path_pred_out)

    except Exception as e:
        print(f"\n[ERROR] Terjadi kegagalan proses: {str(e)}")
    
    finally:
        # Cleanup Memori Total
        if 'df_rf_input' in locals():
            df_rf_input.unpersist()
        if 'train_data' in locals():
            train_data.unpersist()
        if 'test_data' in locals():
            test_data.unpersist()
        if 'predictions' in locals():
            predictions.unpersist()

        spark.stop()

if __name__ == "__main__":
    main()