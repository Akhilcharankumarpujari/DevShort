# REST API Reference & Integration Guide

All service endpoints follow standard REST principles, returning `application/json` payloads.

---

## 1. consolidated Swagger / OpenAPI Docs

The API Gateway consolidates routing. You can inspect Swagger UI interactive documentations locally:

| Service | Local URL | Interactive OpenAPI docs |
| :--- | :--- | :--- |
| **API Gateway** | `http://localhost:8000` | [http://localhost:8000/api/v1/docs](http://localhost:8000/api/v1/docs) |
| **User Service** | `http://localhost:8001` | [http://localhost:8001/api/v1/docs](http://localhost:8001/api/v1/docs) |
| **Product Service** | `http://localhost:8002` | [http://localhost:8002/api/v1/docs](http://localhost:8002/api/v1/docs) |
| **Order Service** | `http://localhost:8003` | [http://localhost:8003/api/v1/docs](http://localhost:8003/api/v1/docs) |
| **Inventory Service** | `http://localhost:8004` | [http://localhost:8004/api/v1/docs](http://localhost:8004/api/v1/docs) |
| **Payment Service** | `http://localhost:8005` | [http://localhost:8005/api/v1/docs](http://localhost:8005/api/v1/docs) |

---

## 2. Global Health Check Endpoint

Every FastAPI microservice exposes a standardized health check endpoint to check service status and database connectivity.

- **URL Path**: `/api/v1/health`
- **Method**: `GET`
- **Response Code**: `200 OK` (Healthy) or `503 Service Unavailable` (Degraded/Disconnected)

### Example Payload (Microservice)
```json
{
  "status": "healthy",
  "database": "connected",
  "service": "user-service",
  "version": "1.0.0"
}
```

---

## 3. Router Endpoints (Boilerplate Stubs)

The following endpoints are registered as mock boilerplates representing the e-commerce workflows.

### User Service
- `GET /api/v1/users/` : Retrieve list of stubbed users.
- `GET /api/v1/users/{user_id}` : Retrieve specific user profiles.

### Product Service
- `GET /api/v1/products/` : Retrieve list of computer/electronics products.
- `GET /api/v1/products/{product_id}` : Retrieve product details.

### Order Service
- `GET /api/v1/orders/` : Retrieve active processing transactions.
- `GET /api/v1/orders/{order_id}` : Retrieve order itemization.

### Inventory Service
- `GET /api/v1/inventory/` : Check warehouse distribution items.
- `GET /api/v1/inventory/{product_id}` : Get quantity levels for a product.

### Payment Service
- `GET /api/v1/payments/` : Fetch past transaction records.
- `GET /api/v1/payments/{transaction_id}` : Get specific authorization/charge state.
