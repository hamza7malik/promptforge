# PromptForge

**AI Agent Workspace for Prompt Engineers**

A production-grade platform for building, managing, and deploying specialized AI agents powered by advanced Retrieval-Augmented Generation (RAG).

## 🎯 Overview

PromptForge enables you to:

- **Create specialized AI agents** trained on your domain-specific documents
- **Upload knowledge bases** (PDFs, DOCX, TXT) to make agents experts in any field
- **Chat with agents** that leverage RAG to provide context-aware responses
- **Evaluate responses** using RAGAS metrics for quality assurance
- **Engineer better prompts** with AI-powered suggestions and improvements

## ⚙️ Tech Stack

### Frontend

- **React 18** + **TypeScript** + **Vite**
- **Tailwind CSS** + **ShadCN UI**
- **Zustand** for state management
- **Auth0** for authentication

### Backend

- **FastAPI** (async Python)
- **SQLAlchemy** + **PostgreSQL 15**
- **LangChain** for RAG orchestration
- **Pinecone** serverless vector database
- **OpenAI GPT-4 Turbo** (128k context)
- **OpenAI Embeddings** (text-embedding-3-large, 3072 dimensions)
- **AWS S3** for document storage
- **RAGAS** for response evaluation
- **Redis** for caching (optional)

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐ │
│  │  Agent   │  │ Document │  │   Chat   │  │ Evaluation │ │
│  │  Manager │  │  Upload  │  │   UI     │  │ Dashboard  │ │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘ │
└─────────────────────────┬───────────────────────────────────┘
                          │ REST + SSE
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                  Backend (FastAPI)                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────────┐ │
│  │  Auth0   │  │   API    │  │   RAG    │  │ LangGraph  │ │
│  │   Auth   │  │  Routes  │  │ Pipeline │  │   Agents   │ │
│  └──────────┘  └──────────┘  └──────────┘  └────────────┘ │
└─────┬─────────────┬─────────────┬─────────────┬────────────┘
      │             │             │             │
      ▼             ▼             ▼             ▼
┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│PostgreSQL│  │ Pinecone │  │  OpenAI  │  │   S3     │
│          │  │  Vector  │  │  GPT-4   │  │ Storage  │
└──────────┘  └──────────┘  └──────────┘  └──────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- PostgreSQL 15+
- Auth0 account
- OpenAI API key
- Pinecone account
- AWS account (for S3)
- LangSmith account (optional)

### 1. Clone and Setup Environment

```bash
# Clone the repository
git clone https://github.com/hamza7malik/promptforge.git
cd promptforge

# Copy environment variables
cp backend/.env.example backend/.env
cp frontend/.env.example frontend/.env

# Edit .env files with your credentials
nano backend/.env
nano frontend/.env
```

### 2. Start with Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

The application will be available at:

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

### 3. Manual Setup (Development)

#### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start backend server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

#### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

## 🧠 RAG Pipeline

The application implements an advanced RAG pipeline:

1. **Document Processing**

   - Upload documents to S3 via pre-signed URLs
   - Extract text from PDF, DOCX, TXT
   - Chunk using `RecursiveCharacterTextSplitter`

2. **Embedding & Indexing**

   - Generate embeddings with `text-embedding-3-large`
   - Store in Pinecone with agent-specific metadata
   - Enable efficient filtering by `agent_id`

3. **Retrieval**

   - Semantic search via Pinecone
   - Optional hybrid search (BM25 + dense)
   - Reranking for improved relevance

4. **Generation**

   - Context injection with token-aware truncation
   - GPT-4 with 128k context window
   - Streaming responses via Server-Sent Events (SSE)

5. **Evaluation**
   - RAGAS metrics: groundedness, faithfulness, correctness
   - Store evaluation results in PostgreSQL
   - Display scores in UI

## 📊 Features

### Agent Management

- Create, edit, delete custom AI agents
- Configure agent personality and expertise
- View agent statistics and usage

### Document Management

- Upload documents (PDF, DOCX, TXT)
- Drag-and-drop interface
- Document versioning
- Delete and reindex documents

### Intelligent Chat

- Context-aware conversations
- Streaming responses with SSE
- Markdown rendering
- Conversation history
- Export conversations

### Prompt Engineering

- AI-powered prompt suggestions
- Prompt improvement recommendations
- Before/after comparison
- Best practice tips

### Evaluation Dashboard

- RAGAS metrics visualization
- Answer quality scores
- Faithfulness analysis
- Groundedness tracking

### Admin Panel

- User management
- Usage statistics
- Vector DB metrics
- System health monitoring
- LangSmith integration

## 🔐 Authentication

The app uses Auth0 for authentication with support for:

- Email/password login
- OAuth providers (Google, GitHub, etc.)
- JWT-based API authorization
- Role-based access control (RBAC)

## 🧪 Testing

```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test

# E2E tests
npm run test:e2e
```

## 📦 Deployment

### Environment Variables

Ensure all production environment variables are set:

- Database connection strings
- API keys (OpenAI, Pinecone, AWS)
- Auth0 configuration
- CORS origins

### Docker Production Build

```bash
# Build production images
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d
```

### Cloud Deployment Options

- **Backend**: AWS ECS/Fargate, Google Cloud Run, Azure Container Apps
- **Frontend**: Vercel, Netlify, CloudFlare Pages
- **Database**: AWS RDS, Google Cloud SQL, Supabase
- **Vector DB**: Pinecone (managed), Weaviate (self-hosted)

## 🔧 Configuration

### RAG Configuration

Edit `backend/config/settings.py` for RAG parameters:

```python
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_RETRIEVAL = 5
```

### LLM Configuration

Model settings in `backend/config/settings.py`:

```python
MODEL = "gpt-4-1106-preview"
TEMPERATURE = 0.7
MAX_TOKENS = 4096
```

## 📚 API Documentation

Interactive API documentation is available at:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Key Endpoints

- `POST /api/agents` - Create agent
- `GET /api/agents` - List agents
- `POST /api/documents/upload` - Upload document
- `POST /api/chat/{agent_id}` - Chat with agent
- `GET /api/evaluations/{message_id}` - Get evaluation
- `POST /api/prompts/suggest` - Get prompt suggestions

## 🛠️ Development

### Project Structure

```
promptforge/
├── backend/
│   ├── main.py
│   ├── requirements.txt
│   ├── .env.example
│   ├── alembic/              # Database migrations
│   ├── api/                  # API routes
│   ├── core/                 # Core utilities
│   ├── models/               # Database models
│   ├── schemas/              # Pydantic schemas
│   ├── services/             # Business logic
│   │   ├── rag/              # RAG pipeline
│   │   ├── llm/              # LLM service
│   │   ├── auth/             # Auth0 integration
│   │   └── evaluation/       # RAGAS evaluation
│   └── config/               # Configuration
├── frontend/
│   ├── src/
│   │   ├── components/       # React components
│   │   ├── pages/            # Page components
│   │   ├── stores/           # Zustand stores
│   │   ├── api/              # API client
│   │   ├── types/            # TypeScript types
│   │   └── utils/            # Utilities
│   ├── .env.example
│   ├── package.json
│   └── vite.config.ts
├── docker-compose.yml
└── README.md
```

### Code Style

- **Python**: Black, isort, flake8, mypy
- **TypeScript**: ESLint, Prettier
- **Commits**: Conventional Commits

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m 'Add feature'`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- LangChain for RAG orchestration
- OpenAI for GPT-4 and embeddings
- Pinecone for vector database
- Auth0 for authentication
- ShadCN UI for components

---

**Built for Developers and Prompt Engineers**
