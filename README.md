#  AI Document Intelligence Platform

An AI-powered document analysis platform that allows users to upload PDF and DOCX files, automatically extract and process text, generate vector embeddings, perform semantic search, and chat with documents using Retrieval-Augmented Generation (RAG).

Built with **FastAPI**, **React**, **PostgreSQL + pgvector**, and **OpenAI**.

---

##  Features

### Authentication
- JWT authentication
- User registration and login
- Protected API endpoints
- Secure password hashing

### Document Management
- Upload PDF and DOCX documents
- Secure file storage
- Document ownership protection
- Delete documents
- Processing status tracking

### AI Processing Pipeline
- Extract text from uploaded documents
- Intelligent document chunking
- Generate OpenAI embeddings
- Store vectors in PostgreSQL using pgvector
- Semantic similarity search

### AI Chat
- Retrieval-Augmented Generation (RAG)
- Streaming AI responses
- Multi-conversation chat sessions
- Conversation history
- Source citations for every answer
- Filter chat by document

### Frontend
- Responsive React + TypeScript interface
- Dashboard
- Document management
- AI chat interface
- Live streaming responses
- Modern Tailwind CSS UI

### Backend
- FastAPI REST API
- SQLAlchemy ORM
- Alembic database migrations
- PostgreSQL
- pgvector vector database
- Comprehensive backend testing with Pytest

---

#  Architecture

```text
                React + TypeScript
                        │
                        ▼
                  FastAPI Backend
                        │
         JWT Authentication & Authorization
                        │
                        ▼
              Upload PDF / DOCX Files
                        │
                        ▼
                Document Text Extraction
                        │
                        ▼
                 Intelligent Chunking
                        │
                        ▼
          OpenAI Embedding Generation
                        │
                        ▼
           PostgreSQL + pgvector Storage
                        │
                        ▼
             Semantic Vector Search
                        │
                        ▼
          Retrieval-Augmented Generation
                        │
                        ▼
           Streaming AI Responses
```

---

#  Screenshots

## Login

> *(Add screenshot later)*

---

## Dashboard

> *(Add screenshot later)*

---

## Documents

> *(Add screenshot later)*

---

## AI Chat

> *(Add screenshot later)*

---

#  Tech Stack

## Frontend

- React
- TypeScript
- React Router
- React Query
- Axios
- Tailwind CSS
- Lucide Icons

## Backend

- FastAPI
- SQLAlchemy
- Alembic
- PostgreSQL
- pgvector
- Pydantic v2
- JWT Authentication

## AI

- OpenAI GPT
- OpenAI Embeddings
- Retrieval-Augmented Generation (RAG)
- Semantic Search

## Testing

- Pytest
- FastAPI TestClient

---

#  Project Structure

```text
backend/
│
├── app/
│   ├── api/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── core/
│   └── main.py
│
├── alembic/
├── tests/
└── requirements.txt

frontend/
│
├── src/
│   ├── pages/
│   ├── components/
│   ├── hooks/
│   ├── api/
│   └── types/
│
└── package.json
```

---

#  Installation

## Clone

```bash
git clone https://github.com/WendiZhang/ai-document-platform.git

cd ai-document-platform
```

---

## Backend

```bash
cd backend

python -m venv venv

source venv/bin/activate
```

Install dependencies

```bash
pip install -r requirements.txt
```

---

## Frontend

```bash
cd frontend

npm install
```

---

# ⚙ Environment Variables

Backend `.env`

```text
DATABASE_URL=

JWT_SECRET_KEY=

OPENAI_API_KEY=

ACCESS_TOKEN_EXPIRE_MINUTES=60
```

Frontend `.env`

```text
VITE_API_BASE_URL=http://localhost:8000/api
```

---

#  Running the Application

Backend

```bash
uvicorn app.main:app --reload
```

Frontend

```bash
npm run dev
```

---

#  Running Tests

Backend

```bash
pytest
```

Run a specific test

```bash
pytest tests/test_chat.py
```

---

#  API Overview

Authentication

```
POST /api/auth/register

POST /api/auth/login

GET /api/auth/me
```

Documents

```
POST /api/documents/upload

GET /api/documents

DELETE /api/documents/{id}

POST /api/documents/{id}/prepare
```

Chat

```
POST /api/chat/sessions

GET /api/chat/sessions

POST /api/chat/sessions/{id}/messages

POST /api/chat/sessions/{id}/stream
```

---

#  Security

- JWT Authentication
- Password hashing
- User data isolation
- Document ownership verification
- Protected endpoints
- SQLAlchemy ORM protection against SQL injection

---

#  Future Improvements

- Hybrid search (Vector + Keyword)
- Reranking
- AWS S3 file storage
- Background task processing
- OCR support
- Image extraction
- Admin dashboard
- CI/CD with GitHub Actions
- Docker deployment
- AWS deployment

---