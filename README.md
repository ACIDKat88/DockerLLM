# J1 Chatbot - RAG System with RAGAS Evaluation

A comprehensive full-stack Retrieval-Augmented Generation (RAG) chatbot system with advanced evaluation capabilities using RAGAS (Retrieval Augmented Generation Assessment) metrics.

## 🚀 Features

- **Full-Stack RAG Chatbot**: Complete chatbot system with document retrieval and generation
- **RAGAS Evaluation**: Advanced evaluation metrics including faithfulness, answer relevancy, context relevancy, etc.
- **Hybrid Retrieval**: Combines Neo4j knowledge graph with vector similarity search
- **Multi-Modal Frontend**: React-based responsive user interface
- **FastAPI Backend**: High-performance Python backend with async support
- **Document Processing**: Intelligent document splitting and embedding
- **User Management**: Authentication, authorization, and user preferences
- **Analytics**: Comprehensive conversation analytics and feedback system
- **Multi-Persona Support**: Different AI personalities for varied use cases

## 🏗️ Architecture

```
full_beta/
├── fast-api/          # FastAPI backend server
├── front-end-app/     # React frontend application  
├── nginx/             # Nginx configuration
├── splitter/          # Document processing and embedding
├── llm_evaluator/     # LLM evaluation modules
├── cleaned/           # Processed documents
└── flask-api/         # Additional Flask components
```

## 🛠️ Prerequisites

- Python 3.8+
- Node.js 16+
- PostgreSQL
- Neo4j Database
- Ollama (for RAGAS evaluation)
- CUDA-compatible GPU (recommended for embeddings)

## ⚙️ Installation

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd full_beta
```

### 2. Backend Setup

```bash
cd fast-api

# Install Python dependencies
pip install -r requirements.txt

# Setup RAGAS evaluation environment
./setup_ragas.sh

# Or use Python setup script
python setup_ragas.py
```

### 3. Frontend Setup

```bash
cd front-end-app

# Install Node.js dependencies
npm install

# Build the application
npm run build
```

### 4. Database Setup

Configure your PostgreSQL and Neo4j databases using the provided schema files:
- `PostGres Schema.txt` - PostgreSQL database schema
- `PostGres Schema SQL.txt` - SQL commands for database setup

### 5. Environment Configuration

Create environment variables for:
- Database connections (PostgreSQL, Neo4j)
- API keys
- Model configurations
- CORS settings

## 🚀 Quick Start

### Option 1: Manual Start

```bash
# Start the backend
cd fast-api
python api_app.py

# In another terminal, start frontend (if needed)
cd front-end-app
npm start
```

### Option 2: Using Scripts

```bash
# Start API with RAGAS support
./run_api_with_ragas.sh

# Or use the comprehensive setup script
./setup_and_run.sh
```

## 📊 RAGAS Evaluation

This system includes advanced RAGAS evaluation capabilities:

### Supported Metrics
- **Faithfulness**: Measures factual consistency with context
- **Answer Relevancy**: Measures how well answers address questions
- **Context Relevancy**: Evaluates retrieved context relevance
- **Context Precision**: Measures precision of retrieved contexts
- **Context Recall**: Evaluates context coverage completeness
- **Harmfulness**: Detects harmful or biased content

### Custom RAGAS Model
The system uses a custom Ollama model (`qwen3-ragas`) optimized for evaluation tasks:

```bash
# Build the custom RAGAS model
ollama create qwen3-ragas -f qwen3_ragas.modelfile
```

## 🔧 Key Components

### Backend (`fast-api/`)
- `api_app.py` - Main FastAPI application
- `ragas_eval.py` - RAGAS evaluation implementation
- `hybrid.py` - Hybrid retrieval system (Neo4j + Vector)
- `reranker.py` - Document reranking functionality
- `embedd_class.py` - Custom embedding implementations

### Frontend (`front-end-app/`)
- React-based responsive web interface
- Real-time chat functionality
- User authentication and preferences
- Admin panel for user management

### Document Processing (`splitter/`)
- Intelligent document splitting
- Embedding generation and storage
- Knowledge graph integration

## 📈 Analytics & Evaluation

The system provides comprehensive analytics including:
- Conversation metrics
- User feedback analysis
- RAGAS evaluation scores
- Response time monitoring
- Context retrieval effectiveness

## 🔐 Authentication & Security

- JWT-based authentication
- Role-based access control
- Admin user management
- Secure API endpoints
- Input validation and sanitization

## 🤖 AI Models

### Supported Models
- Various Ollama models
- Custom embedding models
- Cross-encoder reranking models

### Personalities
Multiple AI personalities available:
- Professional Assistant
- Technical Expert
- Casual Helper
- And more...

## 📚 API Documentation

Once running, access the FastAPI documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🐛 Troubleshooting

### Common Issues

1. **RAGAS Setup Issues**: Ensure Ollama is installed and running
2. **Database Connection**: Verify PostgreSQL and Neo4j are accessible
3. **GPU Memory**: Monitor CUDA memory usage for embeddings
4. **Dependencies**: Check Python and Node.js versions

### Logs
Check application logs in:
- FastAPI console output
- Nginx logs (if using)
- Browser console for frontend issues

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📝 License

[Add your license information here]

## 🙏 Acknowledgments

- RAGAS framework for evaluation metrics
- Ollama for local LLM serving
- ChromaDB for vector storage
- Neo4j for knowledge graph functionality

## 📞 Support

For support, please [create an issue](link-to-issues) or contact the development team.

---

**Note**: This is a comprehensive RAG system with advanced evaluation capabilities. Please ensure you have adequate computational resources for optimal performance. 