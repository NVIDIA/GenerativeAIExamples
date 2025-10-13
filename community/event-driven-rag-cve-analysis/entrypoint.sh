#!/bin/bash

# Activate "morpheus" conda environment
. /opt/conda/etc/profile.d/conda.sh
conda activate morpheus

# Run whatever user wants
exec "$@"
