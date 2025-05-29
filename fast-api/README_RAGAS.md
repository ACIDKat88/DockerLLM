# RAGAS Compatibility Layer

This directory contains a compatibility layer for RAGAS (Retrieval Augmented Generation Assessment) that allows the system to work with different versions of RAGAS, including older versions that might be missing some metrics.

## Files

- `ragas_eval.py` - Core evaluation logic and model loading
- `ragas_override.py` - Compatibility adapters for RAGAS metrics
- `setup_ragas.sh` - Installation script for RAGAS
- `ragas_endpoints.py` - API endpoints for RAGAS evaluation

## Installation

To install RAGAS and its dependencies, run:

```bash
chmod +x setup_ragas.sh
./setup_ragas.sh
```

This script will:
1. Install the latest version of RAGAS
2. If that fails, install a compatible older version (v0.0.11)
3. Install required dependencies
4. Create a requirements.txt file with fixed versions

## Compatibility Approach

The compatibility layer works through several techniques:

1. **Import Hijacking**: `ragas_override.py` creates adapter classes for all RAGAS metrics and monkey-patches the `ragas.metrics` module
2. **Version Detection**: The code detects which version of RAGAS is installed and adapts accordingly
3. **Dummy Implementations**: For metrics that don't exist in the installed version, dummy implementations provide reasonable default values
4. **API Adaptation**: The code inspects function signatures to handle different parameter requirements between versions
5. **Graceful Fallbacks**: If metrics computation fails, the system falls back to reasonable default values

## RAGAS Metrics

The system supports the following metrics:

- **Faithfulness**: Measures how factually consistent the answer is with the provided context
- **Answer Relevancy**: Measures how directly the answer addresses the question
- **Context Relevancy**: Measures how relevant the retrieved context is to the question
- **Context Precision**: Measures the precision of retrieved contexts
- **Context Recall**: Measures how well the context covers all information needed
- **Harmfulness**: Measures if the answer contains harmful content

## Usage

The RAGAS evaluation is automatically triggered in two ways:

1. After a chat response is generated in the `/api/chat` endpoint
2. When a user provides feedback through the feedback endpoints

The metrics are stored in the `analytics` table and can be viewed in the admin dashboard.

## Troubleshooting

If you encounter issues with RAGAS evaluation:

1. Check the server logs for errors related to RAGAS
2. Verify that RAGAS is properly installed: `python -c "import ragas; print(ragas.__version__)"`
3. Try running the compatibility layer directly: `python -c "import ragas_override; print('Success!')"`
4. If using v0.0.11, be aware that some metrics won't be available and will use reasonable defaults

## Manual Evaluation

You can manually trigger RAGAS evaluation using the provided API endpoint:

```bash
curl -X POST "http://localhost:8000/ragas/evaluate" \
  -H "Content-Type: application/json" \
  -H "Authorization: YOUR_SESSION_TOKEN" \
  -d '{
    "question": "What is the capital of France?",
    "answer": "The capital of France is Paris.",
    "contexts": ["Paris is the capital and most populous city of France."]
  }'
``` 