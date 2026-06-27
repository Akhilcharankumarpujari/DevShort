# TechHub Architecture Overview

This document provides a conceptual outline of the Phase 1 microservice architecture.

## System Topology

```mermaid
graph TD
    Client["🌐 User Browser (Next.js App)"] -->|HTTP/JSON| Gateway["🛡️ API Gateway (Port 8000)"]
    
    subgraph Microservices ["Service Mesh (Local Ports 8001-8005)"]
        Gateway -->|Proxy /users| UserSvc["⚙️ User Service"]
        Gateway -->|Proxy /products| ProdSvc["⚙️ Product Service"]
        Gateway -->|Proxy /orders| OrderSvc["⚙️ Order Service"]
        Gateway -->|Proxy /inventory| InvSvc["⚙️ Inventory Service"]
        Gateway -->|Proxy /payments| PaySvc["⚙️ Payment Service"]
    end

    subgraph DatabaseLayer ["Database Isolation"]
        UserSvc -->|Read/Write| UserDB[("🗄️ techhub_users")]
        ProdSvc -->|Read/Write| ProdDB[("🗄️ techhub_products")]
        OrderSvc -->|Read/Write| OrderDB[("🗄️ techhub_orders")]
        InvSvc -->|Read/Write| InvDB[("🗄️ techhub_inventory")]
        PaySvc -->|Read/Write| PayDB[("🗄️ techhub_payments")]
    end
    
    classDef service fill:#2d3748,stroke:#4a5568,color:#fff,stroke-width:2px;
    classDef database fill:#1a202c,stroke:#2d3748,color:#cbd5e0,stroke-width:2px;
    class UserSvc,ProdSvc,OrderSvc,InvSvc,PaySvc,Gateway service;
    class UserDB,ProdDB,OrderDB,InvDB,PayDB database;
```

---

## Architectural Principles

1. **Database-Per-Service**: Each microservice manages its own separate schema and data store. Direct cross-database joins are forbidden; communication occurs exclusively via HTTP APIs.
2. **Reverse Proxy API Gateway**: The frontend does not communicate directly with the individual microservices. All requests are funneled through the FastAPI `api-gateway` which acts as an asynchronous reverse proxy, reducing CORS issues and consolidating documentation access.
3. **Decoupled Deployment**: Each service operates in a containerized sandbox with its own multi-stage `Dockerfile`. 
4. **Environment Isolation**: Service configuration variables are separated from the codebase using system environment variables, mapped locally via `.env` files and in Kubernetes via ConfigMaps and Secrets.
