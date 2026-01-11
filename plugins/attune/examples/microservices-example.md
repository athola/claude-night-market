# Microservices Example: E-Commerce Platform

This example demonstrates architecture-aware initialization for a microservices-based system.

## Project Scenario

**Project**: E-Commerce Platform
**Team**: 20 developers across 4 teams
**Requirements**:
- User management and authentication
- Product catalog and inventory
- Order processing and fulfillment
- Payment processing
- Independent deployment per service
- High availability (99.9% uptime)
- Scale to 1M+ users

## Workflow

### Step 1: Architecture-Aware Initialization

```bash
/attune:arch-init --name ecommerce-platform
```

### Interactive Session

```
============================================================
Architecture-Aware Project Initialization
============================================================

Project Context
------------------------------------------------------------

Project Type: 6 (microservice)
Domain Complexity: 3 (Complex)
Team Size: 3 (15-50)
Programming Language: 1 (Python)
Framework: fastapi
Scalability Needs: 4 (Extreme)
Security Requirements: 3 (Critical)
Time to Market: 2 (Normal)
```

### Research Phase

```
============================================================
Online Research Phase
============================================================

Generated search queries for your project context:
------------------------------------------------------------

1. microservice architecture best practices 2026
   Command: WebSearch("microservice architecture best practices 2026")

2. python microservice architecture patterns 2026
   Command: WebSearch("python microservice architecture patterns 2026")

3. fastapi architecture patterns microservice
   Command: WebSearch("fastapi architecture patterns microservice")

4. complex domain architecture patterns python
   Command: WebSearch("complex domain architecture patterns python")

5. secure architecture patterns microservice
   Command: WebSearch("secure architecture patterns microservice")

6. scalable architecture patterns microservice
   Command: WebSearch("scalable architecture patterns microservice")

------------------------------------------------------------

Research Focus Areas:
------------------------------------------------------------

  Industry Standards:
    Current architecture patterns for microservice in 2026

  Language Patterns:
    Python-specific best practices and idioms

  Domain Modeling:
    Domain-driven design patterns for complex business logic

  Security Architecture:
    Security-first patterns for sensitive data handling

  Scalability Patterns:
    Horizontal scaling strategies and load distribution

  Framework Integration:
    Fastapi architecture patterns and conventions

  Team Structure:
    Conway's Law alignment and team topology patterns
```

### Recommendation

```
============================================================
Architecture Recommendation
============================================================

Primary Paradigm: **Microservices**
Secondary Paradigm: Event-Driven

Confidence: HIGH

Rationale:
**Selected Based On**: matrix selection
**Team Size**: 15-50
**Domain Complexity**: complex
**Project Type**: microservice

Trade-offs:
  - **trade-off**: Distributed systems complexity, network latency, data consistency
  - **mitigation**: Invest in observability, automation, and service mesh from day one
  - **best-for**: Large teams, independent scaling requirements, clear boundaries
  - **avoid-when**: Small teams, unclear domain boundaries, limited DevOps maturity

Alternatives Considered:
  - **Modular Monolith**: Independent deployment not yet needed
  - **Service Based**: Fine-grained services add coordination overhead
  - **Event Driven**: Synchronous communication sufficient for use case

============================================================

Accept this recommendation? [y/n]: y
```

### Generated Project Structure

```
ecommerce-platform/
├── .attune/
│   └── arch-init-session.json
├── .github/
│   └── workflows/
│       ├── test.yml
│       ├── lint.yml
│       ├── typecheck.yml
│       └── deploy.yml
├── docs/
│   ├── adr/
│   │   └── 001-architecture-paradigm.md
│   └── api/
│       └── openapi.yaml
├── services/
│   ├── user-service/
│   │   ├── src/
│   │   │   ├── __init__.py
│   │   │   ├── main.py
│   │   │   ├── api.py
│   │   │   └── service.py
│   │   ├── tests/
│   │   │   ├── __init__.py
│   │   │   └── test_api.py
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   ├── product-service/
│   │   ├── src/
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   ├── order-service/
│   │   ├── src/
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── Dockerfile
│   └── payment-service/
│       ├── src/
│       ├── tests/
│       ├── pyproject.toml
│       └── Dockerfile
├── shared/
│   ├── events/
│   │   ├── __init__.py
│   │   └── base.py
│   └── types/
│       └── __init__.py
├── api-gateway/
│   ├── src/
│   │   └── main.py
│   └── Dockerfile
├── infrastructure/
│   ├── kubernetes/
│   │   ├── base/
│   │   │   ├── deployment.yaml
│   │   │   └── service.yaml
│   │   └── overlays/
│   │       ├── dev/
│   │       └── prod/
│   └── terraform/
│       └── main.tf
├── docker-compose.yml
├── .gitignore
├── .pre-commit-config.yaml
├── ARCHITECTURE.md
├── Makefile
└── README.md
```

## Implementation Guidance

### Service Template Structure

Each service follows a consistent internal structure:

```
user-service/
├── src/
│   ├── __init__.py
│   ├── main.py              # FastAPI application entry
│   ├── api.py               # API routes
│   ├── service.py           # Business logic
│   ├── models.py            # Pydantic models
│   ├── repository.py        # Data access
│   ├── events.py            # Event publishing
│   └── config.py            # Service configuration
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── test_api.py
│   └── test_service.py
├── pyproject.toml
├── Dockerfile
└── README.md
```

### User Service Implementation

```python
# services/user-service/src/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from user_service.api import router
from user_service.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print(f"Starting {settings.service_name} v{settings.version}")
    yield
    # Shutdown
    print(f"Shutting down {settings.service_name}")

app = FastAPI(
    title="User Service",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(router, prefix="/api/v1")

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "user-service"}
```

```python
# services/user-service/src/api.py
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from user_service.models import User, UserCreate, UserUpdate
from user_service.service import UserService
from user_service.auth import get_current_user

router = APIRouter(tags=["users"])

def get_user_service() -> UserService:
    return UserService()

@router.post("/users", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    service: UserService = Depends(get_user_service)
):
    """Create a new user."""
    return await service.create_user(user)

@router.get("/users/{user_id}", response_model=User)
async def get_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user)
):
    """Get user by ID."""
    user = await service.get_user(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.put("/users/{user_id}", response_model=User)
async def update_user(
    user_id: str,
    updates: UserUpdate,
    service: UserService = Depends(get_user_service),
    current_user: User = Depends(get_current_user)
):
    """Update user."""
    if current_user.id != user_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    return await service.update_user(user_id, updates)
```

```python
# services/user-service/src/service.py
from dataclasses import dataclass
from typing import Optional
from user_service.models import User, UserCreate, UserUpdate
from user_service.repository import UserRepository
from user_service.events import publish_event
from shared.events import UserCreatedEvent, UserUpdatedEvent

@dataclass
class UserService:
    """User business logic."""
    repository: UserRepository = None

    def __post_init__(self):
        self.repository = self.repository or UserRepository()

    async def create_user(self, data: UserCreate) -> User:
        """Create a new user and publish event."""
        # Validate email uniqueness
        existing = await self.repository.find_by_email(data.email)
        if existing:
            raise ValueError("Email already registered")

        # Create user
        user = await self.repository.create(data)

        # Publish event for other services
        await publish_event(UserCreatedEvent(
            user_id=user.id,
            email=user.email,
            created_at=user.created_at
        ))

        return user

    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID."""
        return await self.repository.get(user_id)

    async def update_user(self, user_id: str, updates: UserUpdate) -> User:
        """Update user and publish event."""
        user = await self.repository.update(user_id, updates)

        await publish_event(UserUpdatedEvent(
            user_id=user.id,
            updated_fields=updates.dict(exclude_unset=True)
        ))

        return user
```

### Shared Events

```python
# shared/events/base.py
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict
import json
import uuid

@dataclass
class Event:
    """Base event class."""
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    version: str = "1.0"

    def to_json(self) -> str:
        return json.dumps(self.to_dict())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "event_type": self.__class__.__name__,
            "timestamp": self.timestamp.isoformat(),
            "version": self.version,
            "data": self._get_data()
        }

    def _get_data(self) -> Dict[str, Any]:
        """Override in subclasses to provide event data."""
        return {}

@dataclass
class UserCreatedEvent(Event):
    """Published when a user is created."""
    user_id: str = ""
    email: str = ""
    created_at: datetime = None

    def _get_data(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "email": self.email,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

@dataclass
class UserUpdatedEvent(Event):
    """Published when a user is updated."""
    user_id: str = ""
    updated_fields: Dict[str, Any] = field(default_factory=dict)

    def _get_data(self) -> Dict[str, Any]:
        return {
            "user_id": self.user_id,
            "updated_fields": self.updated_fields
        }

@dataclass
class OrderCreatedEvent(Event):
    """Published when an order is created."""
    order_id: str = ""
    user_id: str = ""
    total_amount: float = 0.0
    items: list = field(default_factory=list)

    def _get_data(self) -> Dict[str, Any]:
        return {
            "order_id": self.order_id,
            "user_id": self.user_id,
            "total_amount": self.total_amount,
            "items": self.items
        }
```

### API Gateway

```python
# api-gateway/src/main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import httpx
from typing import Dict

app = FastAPI(title="E-Commerce API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Service registry
SERVICES: Dict[str, str] = {
    "users": "http://user-service:8000",
    "products": "http://product-service:8000",
    "orders": "http://order-service:8000",
    "payments": "http://payment-service:8000",
}

@app.api_route("/{service}/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(service: str, path: str, request: Request):
    """Proxy requests to appropriate service."""
    if service not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service '{service}' not found")

    service_url = f"{SERVICES[service]}/api/v1/{path}"

    async with httpx.AsyncClient() as client:
        # Forward the request
        response = await client.request(
            method=request.method,
            url=service_url,
            headers=dict(request.headers),
            content=await request.body(),
            params=request.query_params,
        )

        return response.json()
```

### Docker Compose

```yaml
# docker-compose.yml
version: '3.8'

services:
  api-gateway:
    build: ./api-gateway
    ports:
      - "8080:8000"
    depends_on:
      - user-service
      - product-service
      - order-service
      - payment-service
    environment:
      - ENV=development

  user-service:
    build: ./services/user-service
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@user-db:5432/users
      - KAFKA_BROKERS=kafka:9092
    depends_on:
      - user-db
      - kafka

  product-service:
    build: ./services/product-service
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@product-db:5432/products
      - KAFKA_BROKERS=kafka:9092
    depends_on:
      - product-db
      - kafka

  order-service:
    build: ./services/order-service
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@order-db:5432/orders
      - KAFKA_BROKERS=kafka:9092
    depends_on:
      - order-db
      - kafka

  payment-service:
    build: ./services/payment-service
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@payment-db:5432/payments
      - KAFKA_BROKERS=kafka:9092
      - STRIPE_API_KEY=${STRIPE_API_KEY}
    depends_on:
      - payment-db
      - kafka

  # Databases (each service has its own)
  user-db:
    image: postgres:15
    environment:
      POSTGRES_DB: users
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - user-data:/var/lib/postgresql/data

  product-db:
    image: postgres:15
    environment:
      POSTGRES_DB: products
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - product-data:/var/lib/postgresql/data

  order-db:
    image: postgres:15
    environment:
      POSTGRES_DB: orders
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - order-data:/var/lib/postgresql/data

  payment-db:
    image: postgres:15
    environment:
      POSTGRES_DB: payments
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - payment-data:/var/lib/postgresql/data

  # Message broker
  kafka:
    image: confluentinc/cp-kafka:7.4.0
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper:2181
      KAFKA_ADVERTISED_LISTENERS: PLAINTEXT://kafka:9092
      KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR: 1
    depends_on:
      - zookeeper

  zookeeper:
    image: confluentinc/cp-zookeeper:7.4.0
    environment:
      ZOOKEEPER_CLIENT_PORT: 2181

volumes:
  user-data:
  product-data:
  order-data:
  payment-data:
```

### Kubernetes Deployment

```yaml
# infrastructure/kubernetes/base/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: user-service
spec:
  replicas: 3
  selector:
    matchLabels:
      app: user-service
  template:
    metadata:
      labels:
        app: user-service
    spec:
      containers:
        - name: user-service
          image: ecommerce/user-service:latest
          ports:
            - containerPort: 8000
          env:
            - name: DATABASE_URL
              valueFrom:
                secretKeyRef:
                  name: user-service-secrets
                  key: database-url
            - name: KAFKA_BROKERS
              value: kafka:9092
          resources:
            requests:
              memory: "256Mi"
              cpu: "100m"
            limits:
              memory: "512Mi"
              cpu: "500m"
          livenessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: user-service
spec:
  selector:
    app: user-service
  ports:
    - port: 8000
      targetPort: 8000
  type: ClusterIP
```

## Why Microservices Architecture?

For this e-commerce platform:

1. **Team Independence**: Each team owns a service and can deploy independently
2. **Scalability**: High-traffic services (products, orders) can scale independently
3. **Technology Freedom**: Teams can choose best tools for their service
4. **Fault Isolation**: Payment service issues don't affect product browsing
5. **Clear Boundaries**: Each service maps to a business capability

## Key Patterns Used

### 1. Database per Service
Each service has its own database, ensuring loose coupling.

### 2. Event-Driven Communication
Services communicate via events for eventual consistency.

### 3. API Gateway
Single entry point for clients, handling routing and cross-cutting concerns.

### 4. Service Discovery
Kubernetes provides built-in service discovery via DNS.

### 5. Circuit Breaker
(Add resilience patterns for production)

## Next Steps

After initialization:

1. **Set up development environment**:
   ```bash
   cd ecommerce-platform
   docker-compose up -d
   ```

2. **Run tests for all services**:
   ```bash
   make test-all
   ```

3. **Deploy to Kubernetes**:
   ```bash
   kubectl apply -k infrastructure/kubernetes/overlays/dev
   ```

4. **Set up observability**:
   - Add Prometheus for metrics
   - Add Jaeger for distributed tracing
   - Add ELK stack for centralized logging

## When to Start Simpler

If starting with a smaller team (< 15), consider:

```bash
/attune:arch-init --name ecommerce-platform --arch modular-monolith
```

This provides similar logical separation without distributed complexity, with a clear path to extract services later.
