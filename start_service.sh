#!/bin/bash

# Disable uvloop to fix LLMEvaluator metrics issue
export UVLOOP_DISABLE=1

# Print confirmation message
echo "Starting service with uvloop disabled (UVLOOP_DISABLE=1)"

# Change to the application directory if needed
# cd /home/cm36/Updated-LLM-Project/full/flask-api/

# Start the FastAPI application using uvicorn with the original command
# Replace the command below with your actual uvicorn command if different
python -m uvicorn api_app:app --host 0.0.0.0 --port 8000

# Note: If you need to pass additional arguments, you can add them after the --port 8000
# For example: python -m uvicorn api_app:app --host 0.0.0.0 --port 8000 --workers 4 --log-level debug 