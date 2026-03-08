# 🏗️ ExcellentInsight System Architecture

> **Comprehensive technical architecture documentation for developers and system architects**

---

## Table of Contents

- [System Overview](#system-overview)
- [Architecture Diagram](#architecture-diagram)
- [Technology Stack](#technology-stack)
- [Component Details](#component-details)
- [Data Flow](#data-flow)
- [Database Schema](#database-schema)
- [Security Architecture](#security-architecture)
- [Performance & Scalability](#performance--scalability)
- [Deployment Architecture](#deployment-architecture)
- [Development Guide](#development-guide)

---

## System Overview

ExcellentInsight is a **microservices-oriented**, **async-first**, **multi-tenant** data analysis platform built on modern Python and React technologies.

### Design Principles

1. **Async-First**: All I/O operations use async/await for maximum concurrency
2. **Event-Driven**: Redis pub/sub for real-time progress tracking
3. **Separation of Concerns**: Clear boundaries between API, workers, and frontend
4. **Type Safety**: Pydantic v2 for runtime validation, TypeScript for frontend
5. **Idempotency**: All operations designed for retry safety
6. **Multi-Tenancy**: Database-level tenant isolation with Row-Level Security

### High-Level Architecture

```
┌─────────────┐         ┌──────────────┐         ┌─────────────┐
│   Browser   │ ◄─────► │   Next.js    │ ◄─────► │   FastAPI   │
│  (React 19) │  HTTP   │  Frontend    │   REST  │   Backend   │
└─────────────┘         └──────────────┘         └──────┬──────┘
                                                         │
                              ┌──────────────────────────┼──────────┐
                              │                          │          │
                              ▼                          ▼          ▼
                        ┌──────────┐             ┌──────────┐  ┌────────┐
                        │   ARQ    │             │PostgreSQL│  │ Redis  │
                        │  Worker  │             │    16    │  │   7    │
                        └──────────┘             └──────────┘  └────────┘
                              │                        │            │
                              └────────────────────────┴────────────┘
                                     Shared Resources
```

---

## Architecture Diagram

### Full System Architecture

```mermaid
graph TB
    subgraph "Client Layer"
        Browser[Web Browser]
    end

    subgraph "Frontend - Next.js 15"
        Next[Next.js Server]
        React[React Components]
        Visx[Visx Charts]
        TW[TailwindCSS]
    end

    subgraph "API Layer - FastAPI"
        API[FastAPI Server]
        Auth[Auth Middleware]
        RateLimit[Rate Limiter]
        ErrorHandler[Error Handler]

        subgraph "API Routes"
            AuthRoute[/auth]
            UploadRoute[/upload]
            JobsRoute[/jobs]
            DashboardRoute[/dashboard]
            UsersRoute[/users]
            SettingsRoute[/settings]
        end
    end

    subgraph "Worker Layer - ARQ"
        Worker[ARQ Worker Pool]
        Pipeline[Pipeline Orchestrator]

        subgraph "Pipeline Steps"
            Parser[1. Parsing Step]
            SchemaDetect[2. Schema Detection]
            Stats[3. Statistical Analysis]
            LLMEnrich[4. LLM Enrichment]
            DashBuild[5. Dashboard Builder]
        end
    end

    subgraph "Data Layer"
        PostgreSQL[(PostgreSQL 16<br/>Multi-tenant DB)]
        Redis[(Redis 7<br/>Cache & Queue)]
        Storage[File Storage<br/>Local/S3]
    end

    subgraph "External Services"
        OpenRouter[OpenRouter API<br/>LLM Provider]
    end

    Browser --> Next
    Next --> React
    React --> Visx
    React --> TW

    Next --> API
    API --> Auth
    Auth --> RateLimit
    RateLimit --> ErrorHandler
    ErrorHandler --> AuthRoute
    ErrorHandler --> UploadRoute
    ErrorHandler --> JobsRoute
    ErrorHandler --> DashboardRoute
    ErrorHandler --> UsersRoute
    ErrorHandler --> SettingsRoute

    UploadRoute --> Storage
    UploadRoute --> Redis
    Redis --> Worker
    Worker --> Pipeline
    Pipeline --> Parser
    Parser --> SchemaDetect
    SchemaDetect --> Stats
    Stats --> LLMEnrich
    LLMEnrich --> DashBuild

    API --> PostgreSQL
    Worker --> PostgreSQL
    API --> Redis
    DashBuild --> PostgreSQL

    LLMEnrich --> OpenRouter

    classDef frontend fill:#61DAFB,stroke:#000,stroke-width:2px,color:#000
    classDef backend fill:#009688,stroke:#000,stroke-width:2px,color:#fff
    classDef worker fill:#FF6F00,stroke:#000,stroke-width:2px,color:#fff
    classDef data fill:#4DB33D,stroke:#000,stroke-width:2px,color:#fff
    classDef external fill:#9C27B0,stroke:#000,stroke-width:2px,color:#fff

    class Next,React,Visx,TW frontend
    class API,Auth,RateLimit,ErrorHandler,AuthRoute,UploadRoute,JobsRoute,DashboardRoute,UsersRoute,SettingsRoute backend
    class Worker,Pipeline,Parser,SchemaDetect,Stats,LLMEnrich,DashBuild worker
    class PostgreSQL,Redis,Storage data
    class OpenRouter external
```

---

## Technology Stack

### Backend Stack

| Technology | Version | Purpose | Why Chosen |
|------------|---------|---------|------------|
| **Python** | 3.12+ | Primary language | Modern async features, type hints |
| **FastAPI** | 0.115+ | Web framework | Automatic OpenAPI docs, async support |
| **SQLAlchemy** | 2.0+ | ORM | Best-in-class Python ORM, async support |
| **asyncpg** | 0.29+ | PostgreSQL driver | Fastest Python PostgreSQL driver |
| **Pydantic** | 2.0+ | Validation | Type-safe schemas, validation at runtime |
| **Polars** | 0.20+ | DataFrame library | 10x faster than Pandas, memory efficient |
| **ARQ** | 0.25+ | Task queue | Redis-based, async-first queue |
| **Redis** | 7.0+ | Cache & queue | Pub/sub, caching, rate limiting |
| **PostgreSQL** | 16+ | Primary database | Row-Level Security, JSON support |
| **Alembic** | 1.13+ | Migrations | Database version control |
| **Structlog** | 24.0+ | Logging | Structured JSON logs |

### Frontend Stack

| Technology | Version | Purpose | Why Chosen |
|------------|---------|---------|------------|
| **Next.js** | 15+ | React framework | App router, server components, SSR |
| **React** | 19+ | UI library | Latest concurrent features |
| **TypeScript** | 5.3+ | Language | Type safety, better DX |
| **TailwindCSS** | 4.0+ | Styling | Utility-first, responsive |
| **Visx** | 3.10+ | Charts | D3-powered React charts |
| **Zustand** | 4.5+ | State management | Lightweight, TypeScript-first |
| **React Query** | 5.0+ | Data fetching | Caching, background updates |

### Infrastructure

| Technology | Purpose |
|------------|---------|
| **Docker** | Containerization |
| **Docker Compose** | Local development orchestration |
| **Nginx** | Reverse proxy (production) |
| **Kubernetes** | Container orchestration (optional) |

---

## Component Details

### 1. FastAPI Backend (`/app`)

**Purpose**: REST API server handling HTTP requests, authentication, and business logic.

**Structure**:
```
app/
├── api/                 # API route handlers
│   ├── auth.py         # Authentication endpoints
│   ├── upload.py       # File upload handling
│   ├── jobs.py         # Job management
│   ├── dashboard.py    # Dashboard data retrieval
│   ├── users.py        # User profile management
│   └── settings.py     # Settings & API keys
├── models/             # SQLAlchemy ORM models
│   ├── user.py
│   ├── organization.py
│   ├── job.py
│   ├── pipeline_state.py
│   └── pipeline_telemetry.py
├── schemas/            # Pydantic request/response schemas
├── services/           # Business logic layer
├── middleware/         # Request/response middleware
│   ├── auth.py
│   ├── rate_limit.py
│   └── error_handler.py
├── db/                 # Database utilities
│   ├── session.py      # Connection pool
│   └── tenant.py       # RLS helpers
├── utils/              # Utilities
│   ├── security.py     # JWT, hashing
│   └── logger.py       # Structured logging
└── main.py             # Application entry point
```

**Key Features**:
- **Async SQLAlchemy**: All database operations use `async/await`
- **Dependency Injection**: FastAPI's `Depends()` for clean code
- **Automatic API Docs**: OpenAPI spec generated automatically
- **Middleware Stack**: Auth → Rate Limit → Error Handling

---

### 2. ARQ Worker (`/app/workers`)

**Purpose**: Background processing of data analysis pipeline.

**Architecture**:
```python
# Worker execution flow:
1. Job enqueued to Redis by API
2. Worker picks up job from queue
3. Executes pipeline steps sequentially:
   - Parsing (Excel/CSV → Polars DataFrame)
   - Schema Detection (column types, relationships)
   - Statistical Analysis (mean, median, outliers)
   - LLM Enrichment (KPI generation via OpenRouter)
   - Dashboard Building (chart selection, layout)
4. Publishes progress to Redis pub/sub
5. Stores result in PostgreSQL
```

**Pipeline Orchestrator** (`orchestrator.py`):
- **Step Registry Pattern**: Dynamically load pipeline steps
- **Telemetry Tracking**: Log processing time, memory usage, LLM tokens
- **Error Recovery**: Retry logic with exponential backoff
- **Cancellation Support**: Check for user cancellation between steps

**Pipeline Steps** (`steps.py`):
```python
@register_step("parsing")
class ParsingStep:
    async def execute(self, context: PipelineContext) -> PipelineContext:
        # Parse Excel/CSV files
        parsed_data = await parser.parse_excel(context.file_path)
        context.dataframes = parsed_data.dataframes
        return context
```

---

### 3. Next.js Frontend (`/frontend`)

**Purpose**: User-facing web application with interactive dashboards.

**Structure**:
```
frontend/
├── app/                       # Next.js 15 App Router
│   ├── (auth)/               # Auth layout group
│   │   ├── login/
│   │   └── signup/
│   ├── (app)/                # Protected app layout
│   │   ├── dashboard/
│   │   ├── jobs/
│   │   └── settings/
│   └── layout.tsx            # Root layout
├── components/               # Reusable components
│   ├── charts/              # Visx chart wrappers
│   ├── ui/                  # UI primitives
│   └── dashboard/           # Dashboard-specific
├── lib/                     # Utilities
│   ├── api.ts              # API client
│   └── auth.ts             # Auth helpers
├── hooks/                   # Custom React hooks
│   ├── useJobProgress.ts   # SSE progress tracking
│   └── useDashboard.ts     # Dashboard data fetching
└── types/                   # TypeScript types
```

**Key Patterns**:
- **Server Components**: Default for static content
- **Client Components**: Only when interactivity needed
- **Streaming SSR**: Progressive page loading
- **Optimistic Updates**: Immediate UI feedback

---

### 4. PostgreSQL Database

**Purpose**: Primary data store with multi-tenant isolation.

**Configuration**:
- **Version**: PostgreSQL 16
- **Connection Pool**: 10 base connections, 20 max overflow
- **Extensions**: `uuid-ossp`, `pg_trgm` (fuzzy search)

**Row-Level Security (RLS)**:
```sql
-- Every query automatically filtered by org_id
SET LOCAL app.current_org_id = 'uuid-here';

-- Policies enforce this at DB level:
CREATE POLICY tenant_isolation ON jobs
    USING (org_id = current_setting('app.current_org_id')::uuid);
```

**Indexes**:
```sql
-- Performance-critical indexes
CREATE INDEX idx_jobs_org_created ON jobs(org_id, created_at DESC);
CREATE INDEX idx_jobs_status ON jobs(status) WHERE status != 'done';
CREATE INDEX idx_pipeline_state_job ON pipeline_state(job_id);
```

---

### 5. Redis Cache & Queue

**Purpose**: Caching, job queue, real-time pub/sub, rate limiting.

**Use Cases**:

1. **Job Queue** (ARQ):
```
List: arq:queue
Items: Serialized job payloads
```

2. **Progress Pub/Sub**:
```
Channel: job:{job_id}:progress
Message: JSON progress updates
```

3. **Caching**:
```
Key: drilldown:{job_id}:{file_hash}
TTL: 3600 seconds (1 hour)
Value: Pickled ParsedData
```

4. **Rate Limiting**:
```
Key: ratelimit:{user_id}:{endpoint}
TTL: 60 seconds
Value: Request count
```

5. **Token Blocklist** (Logout):
```
Key: blocklist:{access_token}
TTL: Token expiry time
Value: "1"
```

---

## Data Flow

### End-to-End Request Flow

#### 1. File Upload Flow

```mermaid
sequenceDiagram
    participant User
    participant Next.js
    participant FastAPI
    participant Storage
    participant Redis
    participant ARQ Worker
    participant PostgreSQL
    participant OpenRouter

    User->>Next.js: Upload Excel file
    Next.js->>FastAPI: POST /upload (multipart/form-data)
    FastAPI->>FastAPI: Validate file (type, size)
    FastAPI->>Storage: Save file to disk/S3
    FastAPI->>PostgreSQL: INSERT job (status: pending)
    FastAPI->>Redis: Enqueue job to ARQ
    FastAPI-->>Next.js: 201 Created (job_id)
    Next.js-->>User: Show progress UI

    Redis->>ARQ Worker: Job picked from queue
    ARQ Worker->>PostgreSQL: UPDATE job (status: parsing)
    ARQ Worker->>Redis: PUBLISH progress update
    ARQ Worker->>Storage: Read Excel file
    ARQ Worker->>ARQ Worker: Parse with Polars

    ARQ Worker->>PostgreSQL: UPDATE job (status: schema)
    ARQ Worker->>Redis: PUBLISH progress update
    ARQ Worker->>ARQ Worker: Detect column types

    ARQ Worker->>PostgreSQL: UPDATE job (status: enrichment)
    ARQ Worker->>Redis: PUBLISH progress update
    ARQ Worker->>OpenRouter: POST /chat/completions (KPI generation)
    OpenRouter-->>ARQ Worker: AI-generated KPIs

    ARQ Worker->>PostgreSQL: UPDATE job (status: done)
    ARQ Worker->>PostgreSQL: INSERT dashboard data
    ARQ Worker->>Redis: PUBLISH completion

    Redis-->>Next.js: SSE progress events
    Next.js-->>User: Show completed dashboard
```

#### 2. Dashboard Viewing Flow

```mermaid
sequenceDiagram
    participant User
    participant Next.js
    participant FastAPI
    participant PostgreSQL
    participant Redis

    User->>Next.js: Navigate to /dashboard/{job_id}
    Next.js->>FastAPI: GET /dashboard/{job_id}
    FastAPI->>Redis: Check cache

    alt Cache Hit
        Redis-->>FastAPI: Cached dashboard
        FastAPI-->>Next.js: Dashboard JSON
    else Cache Miss
        FastAPI->>PostgreSQL: SELECT dashboard data
        PostgreSQL-->>FastAPI: KPIs, charts, metadata
        FastAPI->>Redis: Store in cache (TTL: 1h)
        FastAPI-->>Next.js: Dashboard JSON
    end

    Next.js->>Next.js: Render with Visx
    Next.js-->>User: Interactive dashboard

    User->>Next.js: Click drill-down on chart
    Next.js->>FastAPI: POST /dashboard/{job_id}/drill-down
    FastAPI->>Redis: Check drilldown cache

    alt Cache Hit
        Redis-->>FastAPI: Cached filtered data
    else Cache Miss
        FastAPI->>Storage: Load Parquet file
        FastAPI->>FastAPI: Filter with Polars
        FastAPI->>Redis: Cache result
    end

    FastAPI-->>Next.js: Filtered data
    Next.js-->>User: Show detail table
```

---

## Database Schema

### Entity Relationship Diagram

```mermaid
erDiagram
    Organization ||--o{ User : has
    Organization ||--o{ AnalysisJob : owns
    Organization ||--o{ APIKey : has
    User ||--o{ AnalysisJob : creates
    AnalysisJob ||--o| PipelineState : has
    AnalysisJob ||--o{ PipelineTelemetry : logs
    AnalysisJob ||--o{ JobTransition : tracks

    Organization {
        uuid id PK
        string name
        timestamp created_at
        timestamp updated_at
    }

    User {
        uuid id PK
        uuid org_id FK
        string email UK
        string password_hash
        string full_name
        timestamp created_at
        timestamp updated_at
    }

    AnalysisJob {
        uuid id PK
        uuid org_id FK
        uuid user_id FK
        string filename
        enum status
        int progress
        string file_path
        int file_size_bytes
        jsonb result_data
        text error_message
        timestamp created_at
        timestamp updated_at
        timestamp completed_at
    }

    PipelineState {
        uuid id PK
        uuid job_id FK
        string current_step
        jsonb step_outputs
        jsonb context
        timestamp updated_at
    }

    PipelineTelemetry {
        uuid id PK
        uuid job_id FK
        string step_name
        int duration_ms
        int rows_processed
        int columns_processed
        int llm_tokens
        jsonb metadata
        timestamp created_at
    }

    JobTransition {
        uuid id PK
        uuid job_id FK
        enum from_status
        enum to_status
        jsonb metadata_json
        timestamp created_at
    }

    APIKey {
        uuid id PK
        uuid org_id FK
        string name
        string key_hash
        string key_prefix
        timestamp last_used_at
        timestamp expires_at
        timestamp created_at
    }
```

### Key Tables

#### `organizations`
- One organization per signup
- Isolates all data via RLS
- Soft-delete support with `deleted_at`

#### `users`
- Belongs to one organization
- Email unique globally
- Password hashed with bcrypt

#### `analysis_jobs`
- Tracks each file upload
- `status` enum: pending → parsing → schema → stats → enrichment → building → done/failed
- `result_data` JSONB: Complete dashboard (KPIs, charts)

#### `pipeline_state`
- Stores intermediate outputs
- Enables resume from failure
- Context persisted as JSONB

#### `pipeline_telemetry`
- Performance monitoring
- LLM token tracking
- Per-step metrics

---

## Security Architecture

### Authentication Flow

```
1. User signs up → Password hashed (bcrypt)
2. Login → JWT access token (30min) + refresh token (7d)
3. All requests → Bearer token in Authorization header
4. Token validation → JWT signature verified
5. Refresh expired token → New access + refresh tokens
6. Logout → Access token added to Redis blocklist
```

### Multi-Tenancy Security

**Database Level** (Row-Level Security):
```python
# Every request sets org context
async def get_rls_db(current_org_id: UUID):
    async with async_session() as session:
        await set_db_context(session, str(current_org_id))
        yield session

# All queries automatically filtered
await session.execute(select(AnalysisJob))  # Only org's jobs
```

**Application Level**:
- API routes extract `org_id` from JWT
- File paths include `org_id` prefix
- Redis keys namespaced by `org_id`

### Input Validation

**File Upload**:
- Extension whitelist: `.xlsx`, `.xls`, `.csv`
- Max size: 100MB
- Content-type validation
- Virus scanning (optional, via ClamAV)

**Formula Injection Protection**:
```python
# User-defined KPI formulas validated
ALLOWED_FUNCTIONS = {"SUM", "AVG", "COUNT", "MIN", "MAX"}
def validate_formula(formula: str):
    ast = parse_formula(formula)
    for node in ast:
        if node.type == "FUNCTION" and node.name not in ALLOWED_FUNCTIONS:
            raise ValueError(f"Function {node.name} not allowed")
```

### Secrets Management

**Environment Variables**:
```bash
# Required secrets
JWT_SECRET=generated-with-openssl-rand-hex-32
OPENROUTER_API_KEY=sk-or-v1-...

# Database credentials
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
```

**Secrets Rotation**:
- JWT secret rotation → Invalidate all tokens
- API key rotation → Update in settings, old keys grace period
- Database password rotation → Zero-downtime with connection draining

---

## Performance & Scalability

### Performance Optimizations

**1. Database Query Optimization**
```python
# Use select_in loading to avoid N+1 queries
query = select(AnalysisJob).options(
    selectinload(AnalysisJob.transitions),
    selectinload(AnalysisJob.telemetry)
)
```

**2. Connection Pooling**
```python
# SQLAlchemy async engine with pooling
engine = create_async_engine(
    DATABASE_URL,
    pool_size=10,          # Base connections
    max_overflow=20,       # Burst capacity
    pool_pre_ping=True,    # Validate connections
    pool_recycle=3600      # Recycle after 1h
)
```

**3. Caching Strategy**
- **L1 Cache**: Application memory (LRU, 5min TTL)
- **L2 Cache**: Redis (1h TTL)
- **CDN**: Static assets (immutable, 1yr TTL)

**4. Async I/O**
```python
# Concurrent processing of multiple sheets
results = await asyncio.gather(
    process_sheet(sheet1),
    process_sheet(sheet2),
    process_sheet(sheet3)
)
```

### Scalability Strategy

**Horizontal Scaling**:

| Component | Scaling Strategy | Bottleneck |
|-----------|------------------|------------|
| **FastAPI** | Stateless, load balance with Nginx | CPU for JSON serialization |
| **ARQ Workers** | Add workers based on queue depth | LLM API rate limits |
| **PostgreSQL** | Read replicas for queries | Write throughput to primary |
| **Redis** | Redis Cluster mode | Memory (upgrade to larger instance) |
| **Next.js** | Edge functions, CDN | API data fetching |

**Vertical Scaling**:
- Increase PostgreSQL memory for larger datasets
- Add Redis memory for more caching
- Workers need more CPU for Polars operations

### Performance Metrics

**Target SLAs**:
- API response time: p95 < 200ms
- File upload: < 5s for 10MB
- Pipeline completion: < 60s for typical dataset
- Dashboard load: < 1s

**Monitoring**:
```python
# Structured logging with timing
with logger.contextualize(job_id=job_id):
    start = time.time()
    result = await process_step()
    duration_ms = (time.time() - start) * 1000
    logger.info("step_completed", step="parsing", duration_ms=duration_ms)
```

---

## Deployment Architecture

### Docker Compose (Development)

```yaml
services:
  postgres:  # Database
    image: postgres:16-alpine
    ports: ["5432:5432"]
    volumes: [postgres_data:/var/lib/postgresql/data]

  redis:  # Cache & Queue
    image: redis:7-alpine
    ports: ["6379:6379"]

  backend:  # FastAPI
    build: .
    ports: ["8000:8000"]
    depends_on: [postgres, redis]
    command: uvicorn app.main:app --reload

  worker:  # ARQ Worker
    build: .
    depends_on: [postgres, redis]
    command: arq app.workers.settings.WorkerSettings

  frontend:  # Next.js
    build: ./frontend
    ports: ["3000:3000"]
    depends_on: [backend]
```

### Production Deployment (AWS Example)

```
┌─────────────────────────────────────────────────────┐
│                   AWS CloudFront                    │
│              (CDN for static assets)                │
└─────────────────────────┬───────────────────────────┘
                          │
┌─────────────────────────▼───────────────────────────┐
│                  Application Load Balancer          │
│              (SSL termination, routing)             │
└──────────────┬──────────────────────┬────────────────┘
               │                      │
               ▼                      ▼
    ┌──────────────────┐   ┌──────────────────┐
    │   ECS Fargate    │   │   ECS Fargate    │
    │  (FastAPI x3)    │   │  (Next.js x2)    │
    └────────┬─────────┘   └──────────────────┘
             │
             ├─────────────┬─────────────┬──────────────┐
             ▼             ▼             ▼              ▼
    ┌────────────┐  ┌────────────┐  ┌────────┐  ┌────────┐
    │    RDS     │  │ ElastiCache│  │   S3   │  │  SQS   │
    │ PostgreSQL │  │   Redis    │  │  Files │  │ Worker │
    └────────────┘  └────────────┘  └────────┘  └───┬────┘
                                                     │
                                              ┌──────▼──────┐
                                              │ ECS Fargate │
                                              │ (ARQ x5)    │
                                              └─────────────┘
```

**Infrastructure as Code** (Terraform):
```hcl
module "excellentinsight" {
  source = "./modules/ecs-app"

  app_name = "excellentinsight"
  environment = "production"

  # Scaling
  api_desired_count = 3
  api_max_count = 10
  worker_desired_count = 5
  worker_max_count = 20

  # Database
  db_instance_class = "db.r6g.xlarge"
  db_allocated_storage = 100

  # Redis
  redis_node_type = "cache.r6g.large"
  redis_num_cache_nodes = 2
}
```

---

## Development Guide

### Local Setup

```bash
# 1. Clone repository
git clone https://github.com/moadnane/ExcellentInsight.git
cd ExcellentInsight

# 2. Set up environment
cp .env.example .env
cp frontend/.env.local.example frontend/.env.local
# Edit .env files with your config

# 3. Start services
docker-compose up -d

# 4. Initialize database
docker-compose exec backend alembic upgrade head

# 5. Access services
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Development Workflow

**Backend Development**:
```bash
# Install dependencies
pip install -r requirements.txt

# Run tests
pytest -v --cov=app tests/

# Lint
ruff check app/
mypy app/

# Create migration
alembic revision --autogenerate -m "Add column X"

# Apply migration
alembic upgrade head
```

**Frontend Development**:
```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev

# Run tests
npm test

# Type check
npm run type-check

# Build production
npm run build
```

### Code Quality

**Pre-commit Hooks**:
```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      - id: ruff
      - id: ruff-format

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.8.0
    hooks:
      - id: mypy
```

**CI/CD Pipeline** (GitHub Actions):
```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.12'
      - name: Run tests
        run: |
          pip install -r requirements.txt
          pytest -v --cov=app
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

---

## Future Architecture Considerations

### Planned Enhancements

**Q2 2025**:
- [ ] Kubernetes deployment manifests
- [ ] Multi-region replication
- [ ] Real-time collaboration (WebSockets)

**Q3 2025**:
- [ ] GraphQL API for complex queries
- [ ] Event sourcing for audit trail
- [ ] Apache Kafka for event streaming

**Q4 2025**:
- [ ] ML model serving with Ray
- [ ] Data lakehouse with Iceberg
- [ ] FedRAMP compliance for government

---

## References

- **FastAPI Docs**: https://fastapi.tiangolo.com
- **SQLAlchemy 2.0**: https://docs.sqlalchemy.org/en/20/
- **Polars Guide**: https://pola-rs.github.io/polars/
- **Next.js 15**: https://nextjs.org/docs
- **ARQ Documentation**: https://arq-docs.helpmanual.io/

---

**Maintained by**: ExcellentInsight Engineering Team
**Last Updated**: March 2025
**Architecture Version**: 1.0
**Questions**: architecture@excellentinsight.com
