# GUTTERS

**Guided Universal Transcendental Transformation & Evolutionary Response System**

A production-ready FastAPI-based framework for building modular, AI-powered cosmic intelligence systems.

---

## About GUTTERS

GUTTERS is a comprehensive FastAPI framework designed for building complex, modular systems with:

* ⚡️ Fully async FastAPI + SQLAlchemy 2.0
* 🧱 Pydantic v2 models & validation
* 🔐 JWT auth (access + refresh), cookies for refresh
* 👮 Rate limiter + tiers (free/pro/etc.)
* 🧰 FastCRUD for efficient CRUD & pagination
* 🧑‍💼 **CRUDAdmin**: minimal admin panel (optional)
* 🚦 ARQ background jobs (Redis)
* 🧊 Redis caching (server + client-side headers)
* 🌐 Configurable CORS middleware for frontend integration
* 🐳 One-command Docker Compose
* 🚀 NGINX & Gunicorn recipes for prod

## Features

**Perfect for building:**

* Modular AI-powered systems with 18+ independent modules
* Event-driven architectures with Redis pub/sub
* Systems requiring active memory caching
* Background task processing (hourly/daily data fetching)
* External API integration with rate limiting
* Dynamic JSONB-based configurations

**What you get:**

* **App**: FastAPI app factory, env-aware docs exposure
* **Auth**: JWT access/refresh, logout via token blacklist
* **DB**: Postgres + SQLAlchemy 2.0, Alembic migrations
* **CRUD**: FastCRUD generics (get, get_multi, create, update, delete, joins)
* **Caching**: Decorator-based endpoints cache; client cache headers
* **Queues**: ARQ worker (async jobs), Redis connection helpers
* **Rate limits**: Per-tier + per-path rules
* **Admin**: CRUDAdmin views for common models (optional)

## Quick Start

### Prerequisites

- Python 3.11+
- Docker & Docker Compose (recommended)
- PostgreSQL 12+
- Redis 5+

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd GUTTERS

# Run setup script
python setup.py local

# Start services
docker compose up
```

### Configuration

Create `src/.env` with your settings:

```env
# App
APP_NAME="GUTTERS"
APP_DESCRIPTION="Guided Universal Transcendental Transformation & Evolutionary Response System"
APP_VERSION="0.1"

# Database
POSTGRES_USER="postgres"
POSTGRES_PASSWORD=your_password
POSTGRES_SERVER="db"
POSTGRES_PORT=5432
POSTGRES_DB="gutters"

# JWT
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Redis
REDIS_CACHE_HOST="redis"
REDIS_CACHE_PORT=6379
REDIS_QUEUE_HOST="redis"
REDIS_QUEUE_PORT=6379
REDIS_RATE_LIMIT_HOST="redis"
REDIS_RATE_LIMIT_PORT=6379

# Environment
ENVIRONMENT="local"
```

### Create Admin User

```bash
docker compose run --rm create_superuser
```

### Access the Application

- **API**: http://127.0.0.1:8000
- **API Docs**: http://127.0.0.1:8000/docs
- **Admin Panel**: http://127.0.0.1:8000/admin

## Development

### Run Locally (without Docker)

```bash
uv sync
uv run uvicorn src.app.main:app --reload
```

### Database Migrations

```bash
cd src
uv run alembic revision --autogenerate -m "Your migration message"
uv run alembic upgrade head
```

### Testing

```bash
uv sync --dev
uv run pytest
```

## Project Structure

```
src/
├── app/
│   ├── main.py              # Application entry point
│   ├── api/                 # API routes
│   │   └── v1/              # API version 1
│   ├── core/                # Core utilities
│   │   ├── config.py        # Settings management
│   │   ├── db/              # Database layer
│   │   ├── security.py      # JWT auth
│   │   └── worker/          # ARQ worker
│   ├── crud/                # FastCRUD instances
│   ├── models/              # SQLAlchemy models
│   └── schemas/             # Pydantic schemas
├── migrations/              # Alembic migrations
└── scripts/                 # Utility scripts
```

## Architecture

GUTTERS is built on a modular architecture designed for extensibility:

- **Core Layer**: Database, auth, caching, background jobs
- **Module System**: Independent, pluggable modules with event-driven communication
- **Event Bus**: Redis pub/sub for inter-module messaging
- **Active Memory**: Redis-backed intelligent caching
- **Background Workers**: ARQ for scheduled and async tasks

## Technology Stack

- **FastAPI** - Modern async web framework
- **SQLAlchemy 2.0** - Async ORM with PostgreSQL
- **Pydantic v2** - Data validation and settings
- **Redis** - Caching, queuing, rate limiting, pub/sub
- **ARQ** - Async background job processing
- **Alembic** - Database migrations
- **FastCRUD** - Generic CRUD operations
- **CRUDAdmin** - Auto-generated admin interface

## License

MIT License - see LICENSE.md for details

## Acknowledgments

Built on the excellent [FastAPI Boilerplate](https://github.com/benavlabs/FastAPI-boilerplate) by Benav Labs.

---

**GUTTERS** - Transforming cosmic intelligence through modular architecture
