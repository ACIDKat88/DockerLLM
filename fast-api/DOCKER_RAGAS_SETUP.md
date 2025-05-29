# Setting Up RAGAS Evaluation in Docker

This guide explains how to set up RAGAS (Retrieval Augmented Generation Assessment) for Docker containers with the Qwen3 0.6B model for evaluation.

## Overview

The Docker-based RAGAS setup:
1. Uses a small, efficient model (Qwen3 0.6B, ~523MB) for evaluation
2. Keeps the model files in mounted volumes for persistence
3. Works with your existing Docker containers
4. Evaluates RAG system performance with industry-standard metrics

## Setup Steps

### 1. Download the Model Files

First, download the Qwen3 0.6B model files to the appropriate directories:

```bash
chmod +x download_qwen_model.sh
./download_qwen_model.sh
```

This script:
- Downloads the Qwen3 0.6B model (~523MB)
- Copies it to both `fast-api/models/qwen3-0.6b` and `databases/models/qwen3-0.6b`
- Creates the necessary configuration files

### 2. Configure Your Docker Setup

#### Using docker-compose

Add the RAGAS configuration to your existing docker-compose setup by including our extension:

```bash
# From the project root directory
docker-compose -f docker-compose.yml -f fast-api/docker-compose.ragas.yml up -d
```

#### Manual Docker Configuration

If you're not using docker-compose, mount the model directory when starting your containers:

```bash
docker run -v $(pwd)/fast-api/models/qwen3-0.6b:/app/models/qwen3-0.6b -e MODEL_PATH=/app/models/qwen3-0.6b your-image
```

### 3. Verify the Setup

To verify the RAGAS evaluator is working correctly:

```bash
# Check the logs of your FastAPI service
docker-compose logs fastapi | grep "RAGAS"

# Or run a test directly
docker-compose exec fastapi python -c "import ragas_evaluator; print('RAGAS available:', ragas_evaluator.RAGAS_AVAILABLE)"
```

## How It Works

In Docker containers:

1. `docker_ragas_evaluator.py` replaces the standard evaluator
2. It uses HuggingFace Transformers to load the model files directly
3. The model runs on CPU (or GPU if available)
4. All metrics are calculated locally without external API calls

## Troubleshooting

Common issues:

- **Model Not Found**: Ensure the download script ran successfully and check the paths:
  ```bash
  ls -la fast-api/models/qwen3-0.6b
  ```

- **Out of Memory**: Qwen3 0.6B is small but still requires ~1.5GB RAM:
  ```bash
  # Add memory limit to your containers
  docker-compose -f docker-compose.yml -f fast-api/docker-compose.ragas.yml up -d --memory=2g fastapi
  ```

- **RAGAS Import Errors**: Ensure the dependencies are installed:
  ```bash
  docker-compose exec fastapi pip install ragas langchain-community transformers torch
  ```

## For GPU Acceleration (Optional)

If you have a GPU available:

1. Install the NVIDIA Container Toolkit:
   ```bash
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
   sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
   ```

2. Add GPU support to your docker-compose file:
   ```yaml
   services:
     fastapi:
       deploy:
         resources:
           reservations:
             devices:
               - driver: nvidia
                 count: 1
                 capabilities: [gpu]
   ``` 