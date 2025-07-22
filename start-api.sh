#!/bin/bash
export UVLOOP_DISABLE=1
echo "Starting with UVLOOP_DISABLE=1"

# Attempt to uninstall uvloop to prevent it from being detected
echo "Temporarily disabling uvloop..."
pip uninstall -y uvloop || echo "uvloop not installed or could not be removed"

# Additional environment variables to disable uvloop in uvicorn
export PYTHONPATH=${PYTHONPATH}:$(pwd)
export UVICORN_LOOP=asyncio
export UVICORN_HTTP=h11

cd flask-api
python3 setup_ragas.py

# Start uvicorn with explicit --loop and --http flags to prevent uvloop usage
python3 -m uvicorn api_app:app --host 0.0.0.0 --port 8000 --log-level debug --loop asyncio --http h11

# Optionally reinstall uvloop after shutdown
# pip install uvloop 