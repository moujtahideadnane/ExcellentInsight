# Changelog

All notable changes to ExcellentInsight will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Natural language query interface
- Advanced forecasting models
- Real-time data streaming
- Database connectors (MySQL, MongoDB)
- Collaborative editing features
- PDF report generation
- PowerPoint export
- Webhook notifications

---

## [1.0.0] - 2025-03-08

### Added - Initial Release

#### Core Features
- **Zero-configuration Excel/CSV file upload** with automatic parsing
- **AI-powered KPI detection** using OpenRouter LLM integration
- **Interactive dashboard generation** with multiple chart types
- **Real-time progress tracking** via Server-Sent Events (SSE)
- **Multi-tenant architecture** with organization-based isolation
- **JWT authentication** with refresh token support
- **API key management** for programmatic access

#### Data Processing
- **Intelligent Excel parsing** with:
  - Automatic header detection
  - Transposed data recognition
  - Merged cell handling
  - Multi-sheet support
- **Smart data type inference** (numeric, date, categorical, boolean)
- **Statistical analysis** (mean, median, outliers, correlations)
- **Schema detection** with automatic relationship discovery
- **Cross-sheet relationship detection**

#### Dashboard Features
- **Automatic chart type selection**:
  - Line charts for time series
  - Bar charts for categorical comparisons
  - Pie charts for proportions
  - Scatter plots for correlations
- **Domain-aware KPI generation** (Finance, Sales, HR, Marketing, etc.)
- **Custom formula editor** with real-time validation
- **Drill-down capabilities** with Redis caching
- **Interactive tooltips and legends**

#### API & Integration
- **RESTful API** with OpenAPI 3.1 specification
- **Complete API documentation** at `/docs` and `/redoc`
- **Cursor-based pagination** for efficient data fetching
- **Rate limiting** with token bucket algorithm
- **Error handling** with detailed error codes
- **CORS support** for frontend integration

#### Security
- **Row-Level Security (RLS)** in PostgreSQL
- **Multi-tenant data isolation** at database level
- **Password hashing** with bcrypt
- **JWT token blocklisting** on logout
- **Input validation** with Pydantic v2
- **File upload validation** (type, size, content)
- **Formula injection protection**

#### Performance
- **Async SQLAlchemy** for non-blocking database operations
- **Polars dataframes** for 10x faster data processing vs Pandas
- **Redis caching** for drill-down queries (1-hour TTL)
- **Connection pooling** (10 base, 20 max overflow)
- **Background job processing** with ARQ workers
- **Concurrent sheet processing** with asyncio

#### Frontend
- **Next.js 15** with App Router
- **React 19** with concurrent features
- **TypeScript** for type safety
- **TailwindCSS 4** for responsive styling
- **Visx charts** (D3-powered React visualizations)
- **Real-time progress UI** with SSE integration
- **Responsive design** (mobile, tablet, desktop)
- **Dark mode support** (coming soon)

#### Infrastructure
- **Docker Compose** for local development
- **PostgreSQL 16** with UUID support
- **Redis 7** for caching and queuing
- **Alembic** for database migrations
- **Structured logging** with structlog
- **Health check endpoints**

#### Documentation
- **Comprehensive README** with setup instructions
- **Detailed FEATURES.md** (30+ features documented)
- **Complete API.md** with code examples
- **In-depth ARCHITECTURE.md** with diagrams
- **OpenRouter API guide** with free model recommendations
- **.env.example** with all configuration options

#### Developer Experience
- **Auto-generated OpenAPI docs**
- **Type hints** throughout Python codebase
- **Pydantic schemas** for request/response validation
- **Pre-commit hooks** support
- **pytest** test suite
- **Code coverage** reporting
- **Linting** with Ruff
- **Type checking** with mypy

### Technical Stack
- **Backend**: Python 3.12+, FastAPI 0.115+, SQLAlchemy 2.0+, Polars 0.20+
- **Frontend**: Node.js 20+, Next.js 15, React 19, TypeScript 5.3+
- **Database**: PostgreSQL 16 with asyncpg driver
- **Cache/Queue**: Redis 7
- **AI/ML**: OpenRouter API, Trinity Model (free tier)
- **Infrastructure**: Docker, Docker Compose, Nginx

### Configuration
- Maximum file size: 100MB (configurable)
- Supported formats: .xlsx, .xls, .csv
- JWT access token expiry: 30 minutes
- JWT refresh token expiry: 7 days
- Redis cache TTL: 1 hour
- Maximum sheets per file: 20
- Maximum rows per sheet: 500,000
- ARQ job timeout: 15 minutes

### Known Limitations
- PDF export not yet implemented
- Forecasting models in development
- No webhook support yet
- Single-region deployment only
- No collaborative editing
- Limited to 100MB file size

---

## [0.1.0] - 2025-02-01

### Added - Alpha Release
- Basic file upload functionality
- Simple Excel parsing
- Prototype dashboard generation
- Initial FastAPI backend
- Basic Next.js frontend
- SQLite database (replaced in v1.0)
- Proof of concept LLM integration

---

## Release Notes

### v1.0.0 - Production Ready

This is the first production-ready release of ExcellentInsight, featuring a complete AI-powered spreadsheet analysis platform. The system has been designed from the ground up for scalability, security, and performance.

**Highlights**:
- ✅ Production-grade security with multi-tenant isolation
- ✅ High-performance data processing with Polars
- ✅ Comprehensive API documentation
- ✅ Professional architecture documentation
- ✅ Docker-based deployment
- ✅ Free AI models via OpenRouter

**Migration Notes**:
- This is the initial production release, no migration needed
- For local development, run `alembic upgrade head` to initialize database
- See [README.md](README.md) for complete setup instructions

---

## Upgrade Guide

### From 0.x to 1.0

Since this is a major version bump, a fresh installation is recommended:

1. **Backup Data** (if upgrading from alpha):
   ```bash
   pg_dump excellent_insight > backup.sql
   ```

2. **Update Code**:
   ```bash
   git pull origin main
   ```

3. **Update Dependencies**:
   ```bash
   pip install -r requirements.txt --upgrade
   cd frontend && npm install
   ```

4. **Run Migrations**:
   ```bash
   alembic upgrade head
   ```

5. **Update Environment Variables**:
   - Compare `.env.example` with your `.env`
   - Add new required variables (especially `OPENROUTER_API_KEY`)

6. **Restart Services**:
   ```bash
   docker-compose down
   docker-compose up -d
   ```

---

## Versioning Policy

- **Major version (X.0.0)**: Breaking changes, major features
- **Minor version (1.X.0)**: New features, backward compatible
- **Patch version (1.0.X)**: Bug fixes, minor improvements

---

## Support & Feedback

- **Bug Reports**: [GitHub Issues](https://github.com/moadnane/ExcellentInsight/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/moadnane/ExcellentInsight/discussions)
- **Security Issues**: security@excellentinsight.com
- **General Questions**: [GitHub Discussions Q&A](https://github.com/moadnane/ExcellentInsight/discussions/categories/q-a)

---

**Contributors**: Thank you to all contributors who made this release possible!

**License**: MIT License - see [LICENSE](LICENSE) for details

**Maintained by**: ExcellentInsight Team (@moadnane)
