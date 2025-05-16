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

import os
import time
import glob
import subprocess
import pandas as pd
from aiohttp import web

# Constants
DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_ROWS = 1000
DEFAULT_WORKERS = 2
SPARK_MASTER_URL = "spark://<your ACA app URL>:7077"

# Helper to get container IP (inside ACA)
def get_container_ip():
    try:
        output = subprocess.check_output(["ip", "-4", "addr", "show", "eth0"], text=True)
        for line in output.splitlines():
            if line.strip().startswith("inet") and "100.100." in line:
                return line.strip().split()[1].split("/")[0]
    except Exception as e:
        print("⚠️ Failed to get container IP:", e)
    return "127.0.0.1"

# Main HTTP handler
async def handle(request):
    import traceback

    try:
        model = request.query.get("model", DEFAULT_MODEL)
        rows = int(request.query.get("rows", DEFAULT_ROWS))
        workers = int(request.query.get("workers", DEFAULT_WORKERS))

        driver_ip = get_container_ip()
        jdbc_jar_path = "/opt/driver/mssql-jdbc-12.6.1.jre8.jar"

        cmd = [
            "spark-submit",
            "--master", SPARK_MASTER_URL,
            "--deploy-mode", "client",
            "--conf", f"spark.driver.host={driver_ip}",
            "--conf", "spark.driver.bindAddress=0.0.0.0",
            "--jars", jdbc_jar_path,
            "/app/spark-embedding.py",
            "--model_name", model,
            "--num_rows", str(rows),
            "--workers", str(workers)
        ]

        print(f"⚡ Running spark-submit: {' '.join(cmd)}")
        start_time = time.time()

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=1800, check=True)
            duration = time.time() - start_time
            print(f"✅ spark-submit succeeded in {duration:.2f} seconds")
        except subprocess.CalledProcessError as e:
            print(f"❌ spark-submit failed with exit code {e.returncode}")
            print(f"📋 STDERR:\n{e.stderr}")
            print(f"📋 STDOUT:\n{e.stdout}")

            import re
            ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
            clean_stderr = ansi_escape.sub('', e.stderr)
            clean_stdout = ansi_escape.sub('', e.stdout)

            return web.json_response({
                "status": "failed",
                "error": str(e),
                "command": cmd,
                "stderr_tail": clean_stderr[-1000:],
                "stdout_tail": clean_stdout[-1000:]
            }, status=500)

        duration = time.time() - start_time


        print("✅ spark-submit completed successfully")

        return web.json_response({
            "status": "success",
            "command": cmd,
            "stdout_tail": result.stdout[-1000:],
        }, status=200)

    except Exception as e:
        return web.json_response({
            "status": "crashed",
            "error": str(e),
            "trace": traceback.format_exc()
        }, status=500)

# Healthcheck
async def ping(request):
    return web.json_response({"status": "ok"})

# Server app
app = web.Application()
app.add_routes([web.get("/", handle), web.get("/ping", ping)])

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=8888)
