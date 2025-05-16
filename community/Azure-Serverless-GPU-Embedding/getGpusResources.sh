#!/bin/bash
nvidia-smi --query-gpu=index --format=csv,noheader | \
  awk '{print "{\"name\": \"gpu\", \"addresses\": [\""$1"\"]}"}'
