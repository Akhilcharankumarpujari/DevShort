# AIOps Backend

Production-ready FastAPI backend foundation for the AIOps Platform.

## Included

- FastAPI application factory
- Pydantic Settings configuration
- Structured JSON logging with request IDs
- SQLAlchemy 2.0 async PostgreSQL engine
- Alembic migration environment
- Health check APIs
- Global exception handling
- JWT authentication
- Refresh-token rotation and logout revocation
- Password hashing
- RBAC roles and permissions
- Authorization middleware and route dependencies
- Production Dockerfile

## Local Setup

```bash
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
cp .env.example .env
uvicorn app.main:app --reload
```

## Health Endpoints

- `GET /health/live`
- `GET /health/ready`
- `GET /api/v1/health/live`
- `GET /api/v1/health/ready`

## Auth Endpoints

- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

The first registered user becomes `Admin`. Later registered users become `Viewer` by default. Built-in roles are `Admin`, `SRE`, `Developer`, and `Viewer`.

## Database Migrations

```bash
alembic upgrade head
alembic revision --autogenerate -m "message"
```

## Tests

```bash
pytest
```

## Docker

```bash
docker build -t aiops-backend -f Dockerfile .
docker run --rm -p 8000:8000 --env-file .env aiops-backend
```
