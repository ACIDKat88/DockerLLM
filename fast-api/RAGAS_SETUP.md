# Setting Up RAGAS with Ollama for RAG Evaluation

This guide explains how to set up RAGAS (Retrieval Augmented Generation Assessment) with a local Ollama model for evaluating your RAG system.

## What is RAGAS?

RAGAS is a framework for evaluating RAG systems using metrics like:

- **Faithfulness**: Measures if the answer contains only information present in the context (detects hallucinations)
- **Answer Relevancy**: Measures how relevant the answer is to the question
- **Context Relevancy**: Measures how relevant the retrieved contexts are to the question
- **Context Precision & Recall**: Measures the precision and recall of context retrieval

## Setup Instructions

### 1. Install Ollama

First, you need to install Ollama:

```bash
curl -fsSL https://ollama.com/install.sh | sh
```

### 2. Download the Evaluation Model

Run the provided setup script to download the Qwen3 0.6B model:

```bash
chmod +x setup_ragas_eval_model.sh
./setup_ragas_eval_model.sh
```

This will download Qwen3 0.6B (~523MB), which is optimized for lightweight evaluation tasks.

### 3. Create a Custom Evaluation Model (Optional)

For better evaluation results, you can create a custom model optimized for RAG evaluation:

```bash
# Create the custom model
ollama create ragas-evaluator -f ragas_evaluator.Modelfile

# Verify it works
ollama run ragas-evaluator "Evaluate this answer: ..."
```

### 4. Update Configuration (if needed)

If you want to use a different model or customize settings, edit the configuration in `ragas_evaluator.py`:

```python
# Configuration for evaluation LLM
EVAL_MODEL = "ragas-evaluator"  # Change this to your preferred model
OLLAMA_BASE_URL = "http://localhost:11434"  # Change if using a remote Ollama instance
```

## How It Works

1. When a user interacts with the RAG system, RAGAS metrics are calculated automatically
2. The Qwen3 0.6B model evaluates the quality of answers, context relevance, etc.
3. All metrics are stored in the database and displayed in the analytics dashboard
4. Color-coded indicators show which aspects need improvement (red, yellow, green)

## Troubleshooting

- **Slow evaluation**: Reduce the batch size or use a smaller model
- **Out of memory**: Reduce context length or use a smaller model
- **Error connecting to Ollama**: Ensure Ollama is running with `ollama serve`

## Alternative Models

If Qwen3 0.6B doesn't work well for you, consider these alternatives:

- **phi2** (~3GB): Higher quality but larger model
- **gemma:2b** (~1.4GB): Good balance of quality and size
- **tinyllama** (~600MB): Another lightweight option
- **neural-chat:7b** (~4GB): Higher quality but much larger model 