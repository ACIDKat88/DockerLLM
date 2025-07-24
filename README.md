# DockerLLM

A comprehensive question-answering system built with Docker, integrating LLM capabilities for document search and retrieval.

## Overview

This application provides a full-stack solution for document search, retrieval, and question answering using:

- FastAPI backend with LLM integration
- React frontend
- Neo4j graph database
- PostgreSQL with pgvector for vector embeddings
- Ollama for local LLM hosting

## Architecture

The system consists of several interconnected components:

1. **Frontend** (React/MUI): User interface for chat interaction
2. **Backend API** (FastAPI): Processes queries and generates responses
3. **Vector Database** (PostgreSQL + pgvector): Stores document embeddings
4. **Knowledge Graph** (Neo4j): Stores document relationships
5. **LLM Service** (Ollama): Runs language models locally

## Prerequisites

- Docker and Docker Compose
- At least 16GB RAM recommended
- 50GB+ free disk space (models and Docker images require significant space)
- NVIDIA GPU recommended but not required

## Setup and Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/ACIDKat88/DockerLLM.git
   cd DockerLLM
   ```

2. Start the application:
   ```bash
   docker-compose up -d
   ```

3. The system will automatically:
   - Download required models
   - Set up databases
   - Start all services

4. Access the application:
   - Frontend: http://localhost:80
   - Neo4j browser: http://localhost:7474
   - pgAdmin: http://localhost:5050 (admin@admin.com / admin)

## Usage

1. Sign up with a username, password, and office code
2. Log in to access the chat interface
3. Choose a model and dataset from the settings panel
4. Ask questions about the loaded documents
5. View source references and explore document connections

## Models

This repository doesn't include model files due to their large size. They will be automatically downloaded during setup, or you can download them manually using the provided scripts.

## Troubleshooting

- If containers fail to start, check Docker logs: `docker-compose logs <service_name>`
- For model download issues, ensure you have sufficient disk space and network connectivity
- Database connection issues can often be resolved by restarting the containers

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- MUI for React components
- Hugging Face for embedding models
- Ollama for local LLM hosting
- Neo4j and PostgreSQL for database services 