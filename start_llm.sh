#!/bin/bash


echo "Starting Qwen3 LLM Server..."


mlx_lm.server \
--model mlx-community/Qwen3-4B-4bit \
--host 0.0.0.0 \
--port 8000
