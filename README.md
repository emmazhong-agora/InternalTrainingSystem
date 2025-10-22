# Internal Training System

This repository implements the initial version of the "内部技术支持团队培训资料管理系统". It contains:
- `backend/`: FastAPI service for authentication, video management, learning progress, and RAG integration stubs.
- `frontend/`: React + TypeScript single-page application for uploading, browsing, and watching training videos with an AI assistant panel.
- `infra/`: Deployment assets such as Docker Compose configuration for local development.

## Getting Started

### Prerequisites
- Python 3.11+
- Node.js 20+
- Docker (optional, for containerized services)

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables
Copy `backend/.env.example` to `backend/.env` and adjust credentials (Agora, OpenAI, S3, Postgres, Qdrant) before running in production.

### Services
Docker Compose can start PostgreSQL, Qdrant and MinIO for local development:
```bash
docker compose -f infra/docker-compose.yml up
```

## High-Level Architecture
- **FastAPI backend** handles authentication (JWT), folder/video CRUD, file uploads, learning progress tracking, and a proxy for Agora Conversational AI.
- **PostgreSQL** stores relational data for users, folders, videos, and learning progress.
- **Qdrant** stores vector embeddings created from uploaded transcript chunks for retrieval-augmented generation.
- **MinIO (S3 compatible)** handles video and transcript object storage in development (replace with AWS S3 in production).
- **React frontend** provides login, folder navigation, video upload workflows, video playback with progress reporting, and an AI assistant panel capable of voice/text interaction.

## Next Steps
- Implement Agora API integration (`app/services/agora_service.py`).
- Harden security (rate limiting, audit logging).
- Expand automated testing.
- Add admin roles and richer analytics dashboards.
