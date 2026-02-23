# User Segmentation Service

This repository contains a **Proof‑of‑Concept (PoC)** for a user segmentation and experimentation system. It was built to support a food‑delivery platform where personalization and data‑driven experiments help improve user engagement, conversion, and lifetime value.

The codebase uses Python/FastAPI with PostgreSQL, RabbitMQ, and Redis. It automatically assigns users to segments based on their behaviour, evaluates experiments targeting those segments, and deterministically assigns variants.

---

## 🚀 Key Features

- Create dynamic segments using rule groups (e.g. orders in a window, LTV, location).
- Automatically refresh user assignments on new events (order placed).
- Manage experiments targeting segments, with weighted variants and deterministic hashing.
- Background worker handles metrics updates and re‑evaluation.
- Caching of experiment lookups for performance.

## 🧱 Architecture Overview

```
[Client] ──> API (FastAPI)
                    │
  ┌──────────────┬──┴──────────────┐
  │              │                 │
DB (Postgres)    Redis            RabbitMQ
  │              │                 │
  │              │                 │
Worker <─────────┴───────────────┐
                    │           │
                    ▼           ▼
           segment_evaluator  experiment_service
```

1. **API** exposes endpoints to manage segments/experiments, publish events, and fetch evaluations.
2. **Postgres** stores users, metrics, segments, experiments, orders, assignments.
3. **RabbitMQ** transports user events (e.g. order placed).
4. **Worker** consumes events, updates rolling metrics, and triggers segment re‑evaluation.
5. **Redis** caches experiment lookups per user for 60 seconds (invalidated on segment change).

## 📁 Repository Structure

```
app/
├── assignment_engine.py       # deterministic variant allocation
├── cache.py                   # Redis client
├── config.py                  # environment configuration
├── db.py                      # SQLAlchemy async setup
├── experiment_service.py      # logic for retrieving user experiments
├── experiments.py             # FastAPI router for experiment CRUD
├── main.py                    # FastAPI application entrypoint
├── models.py                  # SQLAlchemy ORM models
├── mq.py                      # publish to RabbitMQ
├── rule_engine.py             # evaluate JSON rule groups
├── segment_evaluator.py       # evaluate and assign segments
├── segments.py                # FastAPI router for segment CRUD
├── schemas.py                 # Pydantic models
└── worker.py                  # background consumer for user events
```

Migrations are under `alembic/`.

## 🔧 Prerequisites

- Docker & Docker Compose (for local dev)
- Python 3.11+ (if running without containers)

Services required:
- PostgreSQL
- Redis
- RabbitMQ

Environment variables (see `.env`):
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/segmentation
REDIS_URL=redis://redis:6379/0
RABBITMQ_URL=amqp://guest:guest@rabbitmq:5672/
```

## 🛠️ Setup & Running Locally

1. **Clone repo** and add collaborators (`saranonearth`, `Shivanshu09`).

2. **Start dependencies** via Docker:
   ```bash
   docker compose up -d
   ```

3. **Run migrations**:
   ```bash
   docker exec -it segmentation_api alembic upgrade head
   ```

4. **Start API & Worker** (already wired in compose):
   - API on port 8000
   - Worker logs shown in `segmentation_worker` container

5. **Verify** with health check:
   ```bash
   curl http://localhost:8000/
   curl http://localhost:8000/db-check
   ```

## 📡 API Endpoints

| Method | Path                          | Description |
|--------|-------------------------------|-------------|
| GET    | `/`                           | health check |
| GET    | `/db-check`                   | verify DB connectivity |
| POST   | `/segments`                   | create a segment (RuleGroup payload) |
| GET    | `/segments`                   | list segments |
| POST   | `/experiments`                | create experiment (status defaults to DRAFT) |
| POST   | `/experiments/{id}/variants`  | add variant (weights must sum ≤100) |
| GET    | `/experiments`               | list experiments |
| GET    | `/experiments/{id}/activate`  | mark as ACTIVE |
| POST   | `/events/order`               | publish an order event (`{user_id, amount}`) |
| GET    | `/evaluate/{user_id}` (dev)   | force segment evaluation |
| GET    | `/experiments/{user_id}`      | fetch active experiment assignments |

_Payload examples_ available in tests or via manual curl/HTTPie.

## 🛍️ Example Workflows

1. **Segment creation**:
   ```json
   POST /segments
   {
     "name": "Power users",
     "rule_definition": {
       "operator": "AND",
       "rules": [
         {"field": "orders_last_23_days", "operator": "GREATER_THAN", "value": 25}
       ]
     }
   }
   ```

2. **Experiment targeting**:
   ```json
   POST /experiments
   {
     "name": "Pizza tile test",
     "target_segment_id": "<power-users-id>"
   }
   ```
   Add variants with weights and config (e.g., different UI payloads).
   Activate experiment with `/activate`.

3. **User event processing**:
   - Send order event: `POST /events/order {"user_id": "...", "amount": 250}`
   - Worker updates metrics, re‑evaluates segments automatically.
   - Next API call to `/experiments/{user_id}` will return variant assignments.

## 🧩 Design Considerations

- **RuleEngine**: JSON‑based groups allow arbitrary boolean logic; easy to extend.
- **Asynchronous DB** via SQLAlchemy; metrics recalculation done incrementally.
- **Deterministic hashing** ensures users always see the same variant once assigned.
- **Caching** helps reduce repeated lookups; invalidated on segment changes.
- **Event-driven** architecture decouples write path, making the service extensible.

