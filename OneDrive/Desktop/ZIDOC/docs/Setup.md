# Step-by-Step Local Workspace Setup

This guide details the commands to boot and test the Zidoc platform in your local workspace.

---

## 1. Quickest Method: Docker Orchestration

You can boot all dependencies (PostgreSQL database, Redis cache) and services (React web, Go API, FastAPI AI) via Docker Compose:

```bash
docker compose up --build
```

- **React Web Client**: `http://localhost:5173`
- **Go API Gateway**: `http://localhost:8080`
- **FastAPI AI Service**: `http://localhost:8000`

---

## 2. Independent Local Run Method

If you prefer to run services natively on your host machine, perform the following steps:

### A. Run Database & Cache Docker containers
Start only PostgreSQL and Redis using Docker:
```bash
docker run --name zidoc-postgres -p 5432:5432 -e POSTGRES_PASSWORD=postgrespassword -e POSTGRES_DB=zidoc -d postgres:16-alpine
docker run --name zidoc-redis -p 6379:6379 -d redis:7-alpine
```

### B. Launch Go API Backend
1. Navigate to the api directory:
   ```bash
   cd apps/api
   ```
2. Build and run:
   ```bash
   go run main.go
   ```
3. Verify Swagger is live:
   Open `http://localhost:8080/swagger/index.html` in your browser.

### C. Launch React Frontend
1. Navigate to the web directory:
   ```bash
   cd apps/web
   ```
2. Install node dependencies:
   ```bash
   npm install
   ```
3. Boot the Vite dev server:
   ```bash
   npm run dev
   ```
4. Access the web app in your browser:
   Open `http://localhost:5173`.

### D. Launch AI Service
1. Navigate to the ai-service directory:
   ```bash
   cd apps/ai-service
   ```
2. Create and activate a virtual environment (optional but recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate # On Windows use `venv\Scripts\activate`
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Start FastAPI server using uvicorn:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```
