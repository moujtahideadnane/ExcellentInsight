# ExcellentInsight - AI-Powered Excel & CSV Analysis Tool

[![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://excellentinsight.onthewifi.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![Next.js 15](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org/)
[![React 19](https://img.shields.io/badge/React-19-blue)](https://react.dev/)

<div align="center">
  <img src="/home/moadnane/.gemini/antigravity/brain/9de31ee5-3853-4e06-930e-f9e63c897720/excellent_insight_dashboard_hero_1772876158355.png" alt="ExcellentInsight AI Dashboard - Transform Excel and CSV files into interactive dashboards with automatic KPI detection" width="800">

  <h3>🚀 AI-Powered Spreadsheet Intelligence Platform for Excel & CSV Analysis</h3>

  <p>Transform any Excel (.xlsx, .xls) or CSV file into a comprehensive AI-powered dashboard with automatic KPI detection in under 60 seconds. Zero configuration, instant business intelligence insights powered by OpenRouter AI.</p>

  <p>
    <a href="https://excellentinsight.onthewifi.com">🌐 Live Demo</a> •
    <a href="#-quick-start">🚀 Quick Start</a> •
    <a href="docs/API.md">📖 API Docs</a> •
    <a href="#-contributing">🤝 Contributing</a> •
    <a href="https://github.com/moadnane/ExcellentInsight/issues">🐛 Report Bug</a>
  </p>
</div>

---

## 🎯 What is ExcellentInsight?

ExcellentInsight is an **open-source AI-powered data analysis platform** that automatically transforms Excel spreadsheets and CSV files into interactive business intelligence dashboards. Unlike traditional BI tools that require complex setup and configuration, ExcellentInsight uses **artificial intelligence** to automatically:

- 📊 **Analyze Excel & CSV files** - Support for .xlsx, .xls, .csv formats
- 🤖 **Detect KPIs automatically** - AI identifies key performance indicators from your data
- 📈 **Generate interactive charts** - Bar charts, line graphs, pie charts, time series visualizations
- 🔍 **Discover data insights** - Anomaly detection, trend forecasting, statistical analysis
- 🏢 **Classify business domains** - Automatic detection of Finance, Sales, HR, Marketing data types
- ⚡ **Process in real-time** - Sub-60 second analysis with live progress tracking

**Perfect for:** Data analysts, business analysts, finance teams, sales managers, marketing professionals, small businesses, and anyone who works with spreadsheet data.

**Technologies:** FastAPI, Next.js 15, React 19, PostgreSQL, Redis, Pandas, OpenRouter AI (GPT-4, Claude, Llama), Docker

---

## ✨ Features

### 🚀 Core Capabilities
- **Zero-Schema Ingestion:** Upload any spreadsheet format without configuration
- **AI-Powered Analysis:** Automatic KPI detection, trend analysis, and insights
- **Real-Time Processing:** Sub-second analysis with live progress tracking
- **Interactive Dashboards:** Dynamic charts, filters, and drill-down capabilities
- **Multi-Sheet Support:** Automatic relationship detection across sheets
- **Smart Data Types:** Intelligent column type inference and validation

### 🎯 Advanced Features
- **Domain Detection:** Automatic industry/domain classification (Finance, Sales, HR, etc.)
- **Anomaly Detection:** Statistical outlier identification
- **Predictive Metrics:** Trend forecasting and projections
- **Custom Formulas:** User-defined KPI calculations
- **Export & Share:** PDF, Excel, and shareable dashboard links

---

## 📚 Documentation

### Core Documentation

| Document | Description |
|----------|-------------|
| **[Features Guide](docs/FEATURES.md)** | Comprehensive feature documentation, capabilities, and configuration options |
| **[API Reference](docs/API.md)** | Complete REST API documentation with examples and schemas |
| **[Architecture Guide](docs/ARCHITECTURE.md)** | System design, data flow, database schema, and deployment architecture |

### Quick Links

- 🚀 **[Quick Start](#-quick-start)** - Get up and running in 5 minutes
- 🔧 **[Configuration](#2-configure-environment)** - Environment setup and API keys
- 📖 **[Usage Examples](#-usage)** - Common workflows and use cases
- 🐛 **[Troubleshooting](https://github.com/moadnane/ExcellentInsight/issues)** - Known issues and solutions

---

## 🛠️ Tech Stack

### Backend
**FastAPI** (async) · **SQLAlchemy 2** (asyncpg) · **Polars** · **ARQ** · **PostgreSQL 16** · **Redis 7**

### Frontend
**Next.js 15** · **React 19** · **TypeScript** · **TailwindCSS 4** · **Visx** · **Zustand**

### AI/ML
**OpenRouter API** · **Trinity Model** (Free) · **GPT-4** · **Claude 3.5** · **Llama 3**

### Infrastructure
**Docker** · **Docker Compose** · **Nginx** · **Alembic** (migrations)

---

## 🚀 Quick Start

### 1. Prerequisites
- Docker & Docker Compose
- Node.js 20+ & Python 3.12+ (for local development)

### 2. Configure Environment

#### Copy Environment Files
```bash
cp .env.example .env
cp frontend/.env.local.example frontend/.env.local
```

#### 🔑 OpenRouter API Configuration

This project uses **[OpenRouter](https://openrouter.ai/)** for AI-powered analysis, which provides access to multiple LLM providers through a single API. OpenRouter offers **many free models** that work excellently with ExcellentInsight.

##### Why OpenRouter?
- **Free Models Available:** Access to powerful models at no cost
- **Unified API:** Single interface for multiple LLM providers
- **No Vendor Lock-in:** Easily switch between models
- **Pay-as-you-go:** Only pay for what you use on premium models

##### 📝 Setup Steps

1. **Get Your API Key:**
   - Visit [openrouter.ai](https://openrouter.ai/)
   - Click "Sign Up" or "Log In"
   - Navigate to [Keys](https://openrouter.ai/keys) section
   - Create a new API key and copy it

2. **Configure Your `.env` File:**
   ```bash
   # Required: Your OpenRouter API Key
   OPENROUTER_API_KEY=sk-or-v1-your-actual-key-here

   # Base URL (default, no need to change)
   OPENROUTER_BASE_URL=https://openrouter.ai/api/v1

   # Recommended Model (Trinity - Free & Powerful)
   LLM_MODEL=arcee-ai/trinity-large-preview:free
   LLM_FALLBACK_MODEL=openai/gpt-oss-120b:free
   ```

##### 🎯 Recommended Model: Trinity Large

We **highly recommend** the **`arcee-ai/trinity-large-preview:free`** model for this project:

- ✅ **Completely Free** (no rate limits)
- ✅ **Excellent Performance** for data analysis tasks
- ✅ **Fast Response Times**
- ✅ **Strong Structured Output** (perfect for JSON schemas)
- ✅ **Large Context Window**

##### 🔄 Using Other Free Models

OpenRouter offers many free models. To use a different one:

1. Visit [openrouter.ai/models](https://openrouter.ai/models)
2. In the search box, type **"free"**
3. Browse available free models
4. Copy the model ID (e.g., `google/gemini-2.0-flash-exp:free`)
5. Update your `.env` file:
   ```bash
   LLM_MODEL=your-chosen-model-id:free
   ```

**Popular Free Alternatives:**
- `google/gemini-2.0-flash-exp:free` - Fast and efficient
- `meta-llama/llama-3.3-70b-instruct:free` - Strong reasoning
- `openai/gpt-4o-mini:free` - Balanced performance
- `anthropic/claude-3-haiku:free` - Quick responses

> **💡 Tip:** Some models may have rate limits. If you encounter limits, switch to another free model or consider OpenRouter's affordable paid tiers.

### 3. Start Application
```bash
# Recommended: Using Docker Compose
docker-compose up -d

# Services available at:
# - Frontend: http://localhost:3000
# - Backend API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
```

### 4. Database Setup
> [!IMPORTANT]
> To initialize or update your database schema, run the following command:
```bash
alembic upgrade head
```
Alternatively, use our initialization script:
```bash
python scripts/init_db.py
```

---

## 📖 Usage

1. **Upload File:** Drag & drop your Excel/CSV file into the upload zone.
2. **Processing:** Watch the real-time progress tracker as the AI analyzes your data.
3. **Dashboard:** Explore your customized dashboard with automatic KPIs and charts.
4. **Interact:** Filter data, edit AI-suggested formulas, and export reports.

---

## 🧪 Testing & Quality

- **Frontend:** `cd frontend && npm test`
- **Backend:** `pytest -v --cov=app`
- **Linting:** `ruff check .`

---

## 🤝 Contributing

Contributions are welcome! Please fork the repository, created a feature branch, and submit a PR. See [CONTRIBUTING.md](CONTRIBUTING.md) for more details.

---

## 📚 Use Cases

ExcellentInsight is perfect for:

- **📊 Business Intelligence** - Analyze sales data, financial reports, and performance metrics
- **💼 Financial Analysis** - Quarterly reports, budget analysis, expense tracking
- **📈 Sales Analytics** - Revenue tracking, sales pipeline analysis, conversion metrics
- **👥 HR Analytics** - Employee data, hiring metrics, performance reviews
- **📱 Marketing Analytics** - Campaign performance, ROI analysis, customer data
- **🏪 E-commerce** - Product sales, inventory analysis, customer behavior
- **🎓 Academic Research** - Dataset analysis, statistical research, data visualization
- **🔬 Data Science Projects** - Quick exploratory data analysis (EDA), prototype dashboards

---

## 🔑 Keywords & Tags

`ai-analytics` `excel-parser` `csv-analysis` `dashboard-generator` `data-visualization` `kpi-detection` `business-intelligence` `spreadsheet-analysis` `fastapi` `nextjs` `python-data-analysis` `react-dashboard` `pandas-dataframes` `openrouter-ai` `llm-integration` `postgresql` `redis` `docker` `async-processing` `real-time-analytics` `zero-configuration` `automatic-insights` `trend-forecasting` `anomaly-detection` `open-source-bi` `self-hosted` `free-ai-models` `data-pipeline` `multi-tenant` `interactive-charts`

---

<div align="center">
  <strong>Built with ❤️ for Data Lovers everywhere.</strong>

  <p>
    <a href="https://github.com/moadnane/ExcellentInsight/issues">Report Bug</a> •
    <a href="https://github.com/moadnane/ExcellentInsight/issues">Request Feature</a> •
    <a href="#-quick-start">Quick Start</a> •
    <a href="#-what-is-excellentinsight">Documentation</a>
  </p>

  **⭐ Star this repo if you find it useful!**
</div>
