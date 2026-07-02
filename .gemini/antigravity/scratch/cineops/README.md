# CineOps - Cloud-Native Movie Ticket Booking Platform

CineOps is a production-ready, cloud-native movie ticket booking platform structured as a multi-service microservice application. It serves as a benchmark and target application for AIOps monitoring, Kubernetes autoscaling, and Prometheus-ready performance monitoring.

## Directory Structure

```
cineops/
├── frontend/             # Next.js 15 frontend application
├── api-gateway/          # FastAPI API Gateway for request proxying
├── user-service/         # Microservice for authentication and users
├── movie-service/        # Microservice for movies, cities, showtimes
├── booking-service/      # Microservice for seats reservation
├── payment-service/      # Microservice for transactions and gateway integrations
├── notification-service/ # Microservice for confirmation logging
├── docker/               # Database initialization & Docker config files
├── kubernetes/           # K8s deployment, service, secrets manifests
├── monitoring/           # Prometheus, Grafana, Alertmanager config
└── README.md
```

## Running the Application Locally

You can spin up the complete application including services, frontend, and independent databases using Docker Compose.

### Dev Mode (Maps ports to host)

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

Ports exposed in Dev mode:
- **API Gateway**: `http://localhost:8000`
- **Next.js Frontend**: `http://localhost:3000`
- **User Service**: `http://localhost:8001`
- **Movie Service**: `http://localhost:8002`
- **Booking Service**: `http://localhost:8003`
- **Payment Service**: `http://localhost:8004`
- **Notification Service**: `http://localhost:8005`
- **User Database**: `localhost:5431`
- **Movie Database**: `localhost:5432`
- **Booking Database**: `localhost:5433`
- **Payment Database**: `localhost:5434`
- **Notification Database**: `localhost:5435`

### Health & Metrics Endpoints

Every Python backend service exposes standard cloud-native routes:
- `/health`: Performs a mock/live dependency check (e.g. database connectivity).
- `/metrics`: Returns Prometheus text format metrics for scrape integration.
- `/api/v1/<service>`: API endpoint prefix.
