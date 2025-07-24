# Build stage
FROM python:3.10-slim AS builder

# Set working directory
WORKDIR /app

# Install system dependencies required for building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir huggingface_hub transformers

# Production stage
FROM python:3.10-slim

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Set environment variables
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV MPLCONFIGDIR=/tmp/matplotlib
ENV TRANSFORMERS_CACHE=/root/.cache/huggingface/transformers
ENV HF_HOME=/root/.cache/huggingface
ENV XDG_CACHE_HOME=/root/.cache

# Create non-root user
RUN useradd -m appuser

# Set working directory
WORKDIR /app

# Copy application files
COPY api_app.py .
COPY hybrid.py .
COPY prompts.py .
COPY db_utils.py .
COPY embedd_class.py .
COPY retriever.py .
COPY reranker.py .
COPY download_model.py .
COPY download_cross_encoder.py .
COPY db_pool.py .


# Create cache directories and set correct ownership
RUN mkdir -p /home/appuser/.cache/huggingface \
    && mkdir -p /home/appuser/.cache/huggingface/transformers \
    && mkdir -p /tmp/matplotlib \
    && chmod -R 777 /home/appuser/.cache \ 
    && chmod -R 777 /app  \
    && chmod -R 777 /tmp/matplotlib 



# Create models directory and run download scripts
RUN python download_model.py || echo "Model download failed, will try at runtime" && \
    python download_cross_encoder.py || echo "Cross-encoder download failed, will try at runtime"

USER appuser

# Expose port 8000
EXPOSE 8000

# Run the FastAPI application
CMD ["uvicorn", "api_app:app", "--host", "0.0.0.0", "--port", "8000"] 