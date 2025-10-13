#!/bin/bash
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

set -e

MODE=${APP_MODE:-jupyter}

if [ "$MODE" = "trigger" ]; then
  unset PYSPARK_DRIVER_PYTHON
  unset PYSPARK_DRIVER_PYTHON_OPTS
  echo "🚀 Starting Trigger HTTP Server on port 8888"
  exec python3 /app/trigger-mode.py

elif [ "$MODE" = "jupyter" ]; then
  echo "🚀 Starting Jupyter Notebook on port 8888"

  export JUPYTER_WORKDIR="/"
  mkdir -p "$JUPYTER_WORKDIR"
  cd /opt/spark/work-dir/

  echo "spark.master spark://127.0.0.1:7077" >> /opt/spark/conf/spark-defaults.conf
  mkdir -p /root/.jupyter /root/.local/share/jupyter/runtime
  rm -f /root/.jupyter/jupyter_notebook_config.json
  rm -f /root/.jupyter/jupyter_server_config.json
  rm -rf /root/.local/share/jupyter/runtime/

  cat <<EOF > /root/.jupyter/jupyter_notebook_config.py
c.ServerApp.token = ''
c.ServerApp.password = ''
c.ServerApp.open_browser = False
c.ServerApp.allow_root = True
c.ServerApp.ip = '0.0.0.0'
c.ServerApp.port = 8888
c.ServerApp.disable_check_xsrf = True
EOF

  exec jupyter-lab --ip 0.0.0.0 --allow-root \
    --ServerApp.token='' \
    --ServerApp.password='' \
    --ServerApp.root_dir="$JUPYTER_WORKDIR" \
    --ServerApp.disable_check_xsrf=True

else
  echo "❌ Unknown APP_MODE: $MODE"
  exit 1
fi
