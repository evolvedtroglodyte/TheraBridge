# TheraScribe Backend - Quick Start Guide

## Overview
This guide helps you quickly set up and run the TheraScribe backend API.

## Prerequisites
- Python 3.11+
- PostgreSQL (or use SQLite for development)
- Redis (optional, for caching)

## Quick Setup

### 1. Clone and Navigate
```bash
cd therabridge-backend
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
```bash
cp .env.example .env
# Edit .env with your database credentials
```

### 5. Run Migrations
```bash
alembic upgrade head
```

### 6. Start the Server
```bash
uvicorn app.main:app --reload --port 8000
```

## API Documentation
Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Key Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/auth/login` | POST | User authentication |
| `/api/v1/patients` | GET/POST | Patient management |
| `/api/v1/sessions` | GET/POST | Session management |
| `/api/v1/sessions/{id}/transcribe` | POST | Upload and transcribe audio |
| `/api/v1/sessions/{id}/notes` | GET | Get extracted notes |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string |
| `SECRET_KEY` | Yes | JWT signing key |
| `OPENAI_API_KEY` | Yes | For AI note extraction |
| `HF_TOKEN` | No | For speaker diarization |

## Development Commands

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=app

# Lint code
ruff check app/

# Format code
black app/
```

## Troubleshooting

### Database Connection Issues
- Verify PostgreSQL is running
- Check DATABASE_URL format: `postgresql://user:pass@host:port/dbname`

### Import Errors
- Ensure virtual environment is activated
- Run `pip install -r requirements.txt` again

### Port Already in Use
```bash
uvicorn app.main:app --reload --port 8001
```

## Next Steps
- See `FEATURE_1_AUTH.md` for authentication setup
- See `FEATURE_2_ANALYTICS.md` for analytics implementation
- See individual feature docs for detailed implementation guides
