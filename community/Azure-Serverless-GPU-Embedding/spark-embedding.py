# Copyright (c) 2025, NVIDIA CORPORATION.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


# ===============================================================
# 📦 Imports
# ===============================================================
import math
import time
import pandas as pd
import numpy as np
import torch

import model_navigator as nav
import tensorrt as trt

from pyspark.sql import SparkSession
import pyspark.sql.functions as F
from pyspark.ml import Transformer
from pyspark.ml.param.shared import HasInputCol, HasOutputCol, Param, Params
from pyspark.ml.functions import predict_batch_udf
from pyspark.sql.types import ArrayType, FloatType
from sentence_transformers import SentenceTransformer

import argparse

# ===============================================================
# 🧠 HuggingFaceSentenceEmbedder Class (fixed with lambda)
# ===============================================================
class HuggingFaceSentenceEmbedder(Transformer, HasInputCol, HasOutputCol):
    NUM_OPT_ROWS = 100
    BATCH_SIZE_DEFAULT = 64

    runtime = Param(Params._dummy(), "runtime", "Runtime: cpu, cuda, or tensorrt")
    batchSize = Param(Params._dummy(), "batchSize", "Batch size for embeddings", int)
    modelName = Param(Params._dummy(), "modelName", "Hugging Face model name")

    def __init__(self, inputCol=None, outputCol=None, runtime="cuda", batchSize=None, modelName=None):
        super().__init__()
        default_runtime = "cuda" if torch.cuda.is_available() else "cpu"
        effective_runtime = runtime if torch.cuda.is_available() else "cpu"

        self._setDefault(runtime=default_runtime, batchSize=self.BATCH_SIZE_DEFAULT)
        self._set(
            inputCol=inputCol,
            outputCol=outputCol,
            runtime=effective_runtime,
            batchSize=batchSize or self.BATCH_SIZE_DEFAULT,
            modelName=modelName,
        )
        self.row_count = 0

    def setBatchSize(self, value): self._set(batchSize=value); return self
    def getBatchSize(self): return self.getOrDefault(self.batchSize)
    def setRuntime(self, value): self._set(runtime=value); return self
    def getRuntime(self): return self.getOrDefault(self.runtime)
    def setModelName(self, value): self._set(modelName=value); return self
    def getModelName(self): return self.getOrDefault(self.modelName)

    def setRowCount(self, count):
        self.row_count = count
        if count < self.NUM_OPT_ROWS or not torch.cuda.is_available():
            self.set(self.runtime, "cpu")
        return self

    def _optimize(self, model):
        conf = nav.OptimizeConfig(
            target_formats=(nav.Format.TENSORRT,),
            runners=("TensorRT",),
            optimization_profile=nav.OptimizationProfile(
                max_batch_size=self.BATCH_SIZE_DEFAULT
            ),
            custom_configs=[
                nav.TorchConfig(autocast=True),
                nav.TorchScriptConfig(autocast=True),
                nav.TensorRTConfig(
                    precision=(nav.TensorRTPrecision.FP16,),
                    onnx_parser_flags=[trt.OnnxParserFlag.NATIVE_INSTANCENORM.value],
                ),
            ],
        )

        def _get_dataloader():
            dummy_inputs = ["dummy input"] * self.BATCH_SIZE_DEFAULT
            return [(self.BATCH_SIZE_DEFAULT, (dummy_inputs, {"show_progress_bar": False}))]

        nav.optimize(model.encode, dataloader=_get_dataloader(), config=conf)

    def _predict_batch_fn(self):
        runtime = self.getRuntime()
        model_name = self.getModelName()

        device = "cuda" if torch.cuda.is_available() and runtime != "cpu" else "cpu"
        print(f"🚀 [Worker] Loading model '{model_name}' on device '{device}' runtime '{runtime}'")

        model = SentenceTransformer(model_name, device=device).eval()

        if runtime == "tensorrt" and device == "cuda":
            print(f"⚙️ [Worker] Initializing TensorRT for '{model_name}'")
            nav.inplace_config.strategy = nav.SelectedRuntimeStrategy("trt-fp16", "TensorRT")
            moduleName = model_name.split("/")[-1]
            model = nav.Module(model, name=moduleName, forward_func="encode")
            try:
                nav.load_optimized()
                print(f"✅ [Worker] Loaded optimized TRT model")
            except Exception:
                print(f"🔧 [Worker] Optimizing model...")
                self._optimize(model)
                nav.load_optimized()
                print(f"✅ [Worker] Optimization and load complete")

        def predict(texts: pd.Series) -> np.ndarray:
            with torch.no_grad():
                embeddings = model.encode(
                    texts.tolist(),
                    convert_to_numpy=True,
                    show_progress_bar=False,
                )
            if embeddings.ndim == 1:
                embeddings = embeddings.reshape(1, -1)
            return embeddings

        return predict

    def _transform(self, dataset, spark=None):
        input_col = self.getInputCol()
        output_col = self.getOutputCol()

        size = dataset.count()
        self.setRowCount(size)

        encode = predict_batch_udf(
            lambda: self._predict_batch_fn(),  # ✅ fixed: use lambda
            return_type=ArrayType(FloatType()),
            batch_size=self.getBatchSize(),
        )

        return dataset.withColumn(output_col, encode(F.col(input_col)))

    def transform(self, dataset, spark=None):
        return self._transform(dataset, spark)

# ===============================================================
# 🚀 Spark Session
# ===============================================================
jdbc_jar_path = "/opt/driver/mssql-jdbc-12.6.1.jre8.jar"

spark = (
    SparkSession.builder
    .appName("WorkerOnlyEmbeddingsParallelUpdate")
    .config("spark.executor.resource.gpu.amount", "1")
    .config("spark.task.resource.gpu.amount", "1")
    .config("spark.executor.cores", "1")
    .config("spark.executor.resource.gpu.discoveryScript", "/spark-rapids-ml/getGpusResources.sh")
    .config("spark.jars", jdbc_jar_path)
    .config("spark.driver.extraClassPath", jdbc_jar_path)
    .config("spark.executor.extraClassPath", jdbc_jar_path)
    .getOrCreate()
)

# ===============================================================
# 🛢 JDBC Connection
# ===============================================================
jdbc_url = "jdbc:sqlserver://xxxx.database.windows.net:1433;database=xxxx"
jdbc_properties = {
    "user": "*****",
    "password": "****",
    "driver": "com.microsoft.sqlserver.jdbc.SQLServerDriver"
}

# ===============================================================
# ⚙️ Control Variables
# ===============================================================
parser = argparse.ArgumentParser()
parser.add_argument("--model_name", required=True)
parser.add_argument("--k", type=int, default=5)
parser.add_argument("--num_rows", type=int, default=1000)
parser.add_argument("--workers", type=int, default=2)

args = parser.parse_args()

model_name = args.model_name
k = args.k
num_rows = args.num_rows
workers = args.workers

total_records_to_process = num_rows
number_of_workers = workers
batch_size = math.ceil(total_records_to_process / number_of_workers)

print(f"⚙️ Configuration: {total_records_to_process} total rows, {number_of_workers} workers, {batch_size} batch size per worker.")

# ===============================================================
# 🔁 Batching Loop
# ===============================================================
processed_records = 0
batch_number = 0

while processed_records < total_records_to_process:
    print(f"🚀 Processing batch {batch_number + 1}...")

    remaining_records = total_records_to_process - processed_records
    current_batch_size = min(batch_size, remaining_records)

    df = spark.read.jdbc(
        url=jdbc_url,
        table=f"(SELECT TOP {current_batch_size} id, text FROM dbo.embeddings WHERE embedding IS NULL ORDER BY id ASC) AS subq",
        properties=jdbc_properties
    )

    count = df.count()
    if count == 0:
        print("✅ No more rows to process. Finished early.")
        break

    embedder = (
        HuggingFaceSentenceEmbedder(inputCol="text", outputCol="embedding")
        .setModelName(model_name)
        .setBatchSize(32)
        .setRuntime("tensorrt")
    )

    df_embedded = embedder.transform(df)

    df_embedded.select("id", F.to_json(F.col("embedding")).alias("embedding")).write.jdbc(
        url=jdbc_url,
        table="dbo.embeddings_temp_updates",
        mode="overwrite",
        properties=jdbc_properties
    )
    print(f"✅ Batch {batch_number + 1}: embeddings saved to temp table.")

    conn = spark._sc._jvm.java.sql.DriverManager.getConnection(
        jdbc_url + ";user=xxxxx;password=xxxxx;encrypt=true;trustServerCertificate=false"
    )
    stmt = conn.createStatement()

    merge_query = """
    MERGE INTO dbo.embeddings AS target
    USING dbo.embeddings_temp_updates AS source
    ON target.id = source.id
    WHEN MATCHED THEN
        UPDATE SET target.embedding = source.embedding;
    """
    stmt.execute(merge_query)
    stmt.close()
    conn.close()

    print(f"✅✅✅ Batch {batch_number + 1}: embeddings merged into main table.")

    processed_records += count
    batch_number += 1
    print(f"📈 Progress: {processed_records}/{total_records_to_process} processed.")

    time.sleep(1)

print("🏁🏁🏁 All requested records processed successfully!")

