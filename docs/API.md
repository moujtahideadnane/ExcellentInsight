# 🔌 ExcellentInsight API Documentation

> **Complete REST API reference for ExcellentInsight v1**

---

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [Base URL & Versioning](#base-url--versioning)
- [Endpoints](#endpoints)
  - [Authentication](#authentication-endpoints)
  - [File Upload](#file-upload)
  - [Jobs & Processing](#jobs--processing)
  - [Dashboard](#dashboard)
  - [User Management](#user-management)
  - [Settings & API Keys](#settings--api-keys)
- [Schemas](#schemas)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Webhooks](#webhooks-roadmap)

---

## Overview

ExcellentInsight provides a RESTful API built with **FastAPI** that follows OpenAPI 3.1 specifications.

### Key Features
- 🔒 **JWT-based authentication** with refresh tokens
- 📊 **Real-time progress tracking** via Server-Sent Events (SSE)
- 🚀 **Async processing** with background job queues
- 🔐 **Multi-tenant isolation** at database level
- 📝 **Auto-generated OpenAPI docs** at `/docs`
- 🎯 **Type-safe schemas** with Pydantic v2

### API Characteristics
- **Protocol**: HTTP/HTTPS
- **Format**: JSON
- **Authentication**: Bearer Token (JWT)
- **Pagination**: Cursor-based
- **Rate Limiting**: Token bucket algorithm

---

## Authentication

### JWT Token Flow

```mermaid
sequenceDiagram
    participant Client
    participant API
    participant DB

    Client->>API: POST /auth/signup or /auth/login
    API->>DB: Verify credentials
    DB-->>API: User data
    API-->>Client: { access_token, refresh_token }

    Client->>API: GET /jobs (with Bearer token)
    API->>API: Verify token
    API-->>Client: Protected resource

    Note over Client,API: Access token expires (30 min)

    Client->>API: POST /auth/refresh (with refresh_token)
    API-->>Client: New { access_token, refresh_token }
```

### Token Lifetimes
- **Access Token**: 30 minutes
- **Refresh Token**: 7 days

### Using Tokens

**Authorization Header**
```http
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Example with curl**
```bash
curl -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
     https://api.excellentinsight.com/api/v1/jobs
```

---

## Base URL & Versioning

**Production**: `https://api.excellentinsight.com/api/v1`
**Development**: `http://localhost:8000/api/v1`

All endpoints are prefixed with `/api/v1/` for version 1 of the API.

---

## Endpoints

### Authentication Endpoints

#### POST /auth/signup

Create a new user account and organization.

**Request Body**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!",
  "full_name": "Jane Doe",
  "org_name": "Acme Corporation"
}
```

**Response** `201 Created`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "email": "user@example.com",
    "full_name": "Jane Doe",
    "org_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
    "created_at": "2025-03-08T10:30:00Z"
  }
}
```

**Validation Rules**
- Email: Valid email format, unique
- Password: Minimum 8 characters
- Full name: 2-100 characters
- Org name: 2-100 characters

---

#### POST /auth/login

Authenticate existing user.

**Request Body**
```json
{
  "email": "user@example.com",
  "password": "SecurePassword123!"
}
```

**Response** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": { /* User object */ }
}
```

**Error Responses**
- `401 Unauthorized`: Invalid credentials
- `403 Forbidden`: Account disabled/locked

---

#### POST /auth/refresh

Refresh access token using refresh token.

**Request Body**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response** `200 OK`
```json
{
  "access_token": "NEW_ACCESS_TOKEN",
  "refresh_token": "NEW_REFRESH_TOKEN",
  "token_type": "bearer",
  "user": { /* User object */ }
}
```

---

#### POST /auth/logout

Invalidate current access token (adds to blocklist).

**Headers**
```http
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response** `204 No Content`

---

### File Upload

#### POST /upload

Upload Excel or CSV file for analysis.

**Headers**
```http
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: multipart/form-data
```

**Form Data**
```
file: <binary file data>
```

**Supported Formats**
- `.xlsx` (Excel 2007+)
- `.xls` (Excel 97-2003)
- `.csv` (UTF-8, Latin-1, auto-detected)

**File Size Limits**
- Maximum: 100MB (configurable)
- Recommended: < 50MB for optimal performance

**Response** `201 Created`
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "pending",
  "filename": "Q4_sales_data.xlsx",
  "file_size_bytes": 2457600,
  "created_at": "2025-03-08T10:30:00Z",
  "message": "File uploaded successfully. Analysis started."
}
```

**Error Responses**
- `400 Bad Request`: Invalid file format
- `413 Payload Too Large`: File exceeds size limit
- `415 Unsupported Media Type`: Wrong file type

**Example with curl**
```bash
curl -X POST https://api.excellentinsight.com/api/v1/upload \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "file=@/path/to/data.xlsx"
```

**Example with Python**
```python
import requests

url = "https://api.excellentinsight.com/api/v1/upload"
headers = {"Authorization": f"Bearer {access_token}"}
files = {"file": open("data.xlsx", "rb")}

response = requests.post(url, headers=headers, files=files)
job = response.json()
print(f"Job ID: {job['job_id']}")
```

---

### Jobs & Processing

#### GET /jobs

List all analysis jobs for current organization.

**Query Parameters**
- `limit` (int, default: 20, max: 100): Number of jobs per page
- `cursor` (string): ISO timestamp for pagination
- `status` (string): Filter by status (`pending`, `parsing`, `done`, `failed`)

**Response** `200 OK`
```json
{
  "jobs": [
    {
      "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
      "filename": "Q4_sales_data.xlsx",
      "status": "done",
      "progress": 100,
      "created_at": "2025-03-08T10:30:00Z",
      "updated_at": "2025-03-08T10:31:15Z",
      "completed_at": "2025-03-08T10:31:15Z",
      "error_message": null,
      "file_size_bytes": 2457600,
      "processing_time_seconds": 75
    }
  ],
  "total": 42,
  "has_more": true,
  "next_cursor": "2025-03-07T15:22:30Z"
}
```

**Pagination Example**
```bash
# First page
GET /api/v1/jobs?limit=20

# Next page using cursor from previous response
GET /api/v1/jobs?limit=20&cursor=2025-03-07T15:22:30Z
```

---

#### GET /jobs/{job_id}

Get detailed status of specific job.

**Path Parameters**
- `job_id` (UUID): Job identifier

**Response** `200 OK`
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "filename": "Q4_sales_data.xlsx",
  "status": "done",
  "progress": 100,
  "current_step": "building",
  "created_at": "2025-03-08T10:30:00Z",
  "updated_at": "2025-03-08T10:31:15Z",
  "completed_at": "2025-03-08T10:31:15Z",
  "file_size_bytes": 2457600,
  "processing_time_seconds": 75,
  "telemetry": {
    "rows_processed": 15420,
    "columns_processed": 48,
    "sheets_processed": 3,
    "llm_tokens_used": 2850
  }
}
```

**Status Values**
- `pending`: Queued, waiting for worker
- `parsing`: Reading file and extracting data
- `schema`: Detecting column types and relationships
- `stats`: Computing statistical metrics
- `enrichment`: AI-powered KPI generation
- `building`: Assembling dashboard
- `done`: Successfully completed
- `failed`: Error occurred (see `error_message`)
- `cancelled`: Manually cancelled by user

---

#### GET /jobs/{job_id}/progress (SSE)

Real-time progress updates via Server-Sent Events.

**Response** `text/event-stream`
```
event: progress
data: {"status":"parsing","progress":15,"message":"Processing sheet 1 of 3"}

event: progress
data: {"status":"schema","progress":45,"message":"Detecting column types"}

event: progress
data: {"status":"done","progress":100,"message":"Dashboard ready"}
```

**JavaScript Example**
```javascript
const eventSource = new EventSource(
  `https://api.excellentinsight.com/api/v1/jobs/${jobId}/progress`,
  {
    headers: {
      'Authorization': `Bearer ${accessToken}`
    }
  }
);

eventSource.addEventListener('progress', (event) => {
  const data = JSON.parse(event.data);
  console.log(`${data.status}: ${data.progress}%`);

  if (data.status === 'done') {
    eventSource.close();
    // Redirect to dashboard
  }
});

eventSource.onerror = (error) => {
  console.error('SSE error:', error);
  eventSource.close();
};
```

---

#### DELETE /jobs/{job_id}

Cancel a pending or in-progress job.

**Response** `204 No Content`

**Note**: Jobs in `done` or `failed` status cannot be cancelled.

---

### Dashboard

#### GET /dashboard/{job_id}

Retrieve generated dashboard data.

**Path Parameters**
- `job_id` (UUID): Job identifier

**Response** `200 OK`
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "title": "Q4 Sales Analysis",
  "domain": "sales",
  "created_at": "2025-03-08T10:31:15Z",
  "kpis": [
    {
      "id": "kpi_1",
      "name": "Total Revenue",
      "value": 1245800.50,
      "format": "currency",
      "formula": "SUM(revenue)",
      "description": "Total sales revenue across all transactions",
      "trend": {
        "direction": "up",
        "percentage": 12.5,
        "comparison_period": "previous_month"
      }
    }
  ],
  "charts": [
    {
      "id": "chart_1",
      "title": "Revenue by Month",
      "type": "line",
      "x_axis": "month",
      "y_axis": "revenue",
      "data": [
        {"month": "2024-10", "revenue": 385420.00},
        {"month": "2024-11", "revenue": 412390.50},
        {"month": "2024-12", "revenue": 447990.00}
      ]
    }
  ],
  "sheets": [
    {
      "name": "sales_data",
      "rows": 5420,
      "columns": 12,
      "schema": {
        "date": "datetime",
        "customer_id": "string",
        "revenue": "float64",
        "region": "category"
      }
    }
  ],
  "metadata": {
    "generated_at": "2025-03-08T10:31:15Z",
    "llm_model": "arcee-ai/trinity-large-preview:free",
    "processing_time_seconds": 75
  }
}
```

---

#### POST /dashboard/{job_id}/kpi

Update existing KPI formula.

**Request Body**
```json
{
  "kpi_id": "kpi_1",
  "formula": "SUM(revenue) * 0.85",
  "name": "Net Revenue (after discount)",
  "format": "currency"
}
```

**Response** `200 OK`
```json
{
  "kpi_id": "kpi_1",
  "value": 1058930.425,
  "updated_at": "2025-03-08T11:00:00Z"
}
```

---

#### POST /dashboard/{job_id}/drill-down

Drill down into specific chart data point.

**Request Body**
```json
{
  "chart_id": "chart_1",
  "filter": {
    "month": "2024-12",
    "region": "North America"
  },
  "limit": 100
}
```

**Response** `200 OK`
```json
{
  "data": [
    {
      "date": "2024-12-01",
      "customer_id": "CUST_001",
      "revenue": 15420.50,
      "region": "North America"
    }
  ],
  "total_rows": 1842,
  "filtered_rows": 287
}
```

---

#### POST /dashboard/cache/clear

Clear drill-down cache for a job or all jobs.

**Request Body**
```json
{
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"  // Optional
}
```

**Response** `200 OK`
```json
{
  "cleared": 15,
  "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

---

### User Management

#### GET /users/me

Get current user profile.

**Response** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "full_name": "Jane Doe",
  "org_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "created_at": "2025-01-15T08:00:00Z",
  "updated_at": "2025-03-08T10:30:00Z"
}
```

---

#### PATCH /users/me

Update current user profile.

**Request Body**
```json
{
  "full_name": "Jane Smith",
  "email": "jane.smith@example.com"
}
```

**Response** `200 OK`
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "jane.smith@example.com",
  "full_name": "Jane Smith",
  "updated_at": "2025-03-08T11:00:00Z"
}
```

---

### Settings & API Keys

#### GET /settings/api-keys

List all API keys for organization.

**Response** `200 OK`
```json
{
  "api_keys": [
    {
      "id": "key_1a2b3c4d",
      "name": "Production API",
      "key_prefix": "sk_live_abc123",
      "created_at": "2025-02-01T10:00:00Z",
      "last_used_at": "2025-03-08T09:15:00Z",
      "expires_at": null
    }
  ]
}
```

---

#### POST /settings/api-keys

Create new API key.

**Request Body**
```json
{
  "name": "Production API"
}
```

**Response** `201 Created`
```json
{
  "id": "key_1a2b3c4d",
  "name": "Production API",
  "key": "ei_live_abc123def456ghi789jkl012mno345pqr678",
  "key_prefix": "ei_live_abc123",
  "created_at": "2025-03-08T11:00:00Z"
}
```

**⚠️ Important**: The full `key` is only returned once during creation. Store it securely.

---

#### DELETE /settings/api-keys/{key_id}

Revoke API key.

**Response** `204 No Content`

---

## Schemas

### Job Status Enum
```typescript
type JobStatus =
  | "pending"
  | "parsing"
  | "schema"
  | "stats"
  | "enrichment"
  | "building"
  | "done"
  | "failed"
  | "cancelled";
```

### Chart Type Enum
```typescript
type ChartType =
  | "line"
  | "bar"
  | "pie"
  | "scatter"
  | "area"
  | "heatmap";
```

### KPI Format Enum
```typescript
type KPIFormat =
  | "number"
  | "currency"
  | "percentage"
  | "duration"
  | "date";
```

---

## Error Handling

### Error Response Format
```json
{
  "detail": "Human-readable error message",
  "error_code": "MACHINE_READABLE_CODE",
  "request_id": "req_1234567890abcdef",
  "timestamp": "2025-03-08T11:00:00Z"
}
```

### HTTP Status Codes

| Code | Meaning | Common Causes |
|------|---------|---------------|
| 200 | OK | Request succeeded |
| 201 | Created | Resource created successfully |
| 204 | No Content | Deletion/logout succeeded |
| 400 | Bad Request | Invalid input, validation error |
| 401 | Unauthorized | Missing/invalid token |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource (e.g., email) |
| 413 | Payload Too Large | File exceeds size limit |
| 422 | Unprocessable Entity | Pydantic validation error |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |
| 503 | Service Unavailable | Maintenance mode |

### Error Codes

| Code | Description |
|------|-------------|
| `INVALID_TOKEN` | JWT token invalid or expired |
| `FILE_TOO_LARGE` | Uploaded file exceeds limit |
| `UNSUPPORTED_FORMAT` | File format not supported |
| `JOB_NOT_FOUND` | Job ID doesn't exist or no access |
| `RATE_LIMIT_EXCEEDED` | Too many requests |
| `PIPELINE_ERROR` | Processing pipeline failed |
| `LLM_TIMEOUT` | AI model request timed out |
| `DUPLICATE_EMAIL` | Email already registered |

---

## Rate Limiting

### Limits
- **Anonymous**: 10 requests/minute
- **Authenticated**: 100 requests/minute
- **File Upload**: 5 uploads/minute per user
- **SSE Connections**: 3 concurrent per user

### Headers
```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 87
X-RateLimit-Reset: 1678280400
```

### Rate Limit Response `429`
```json
{
  "detail": "Rate limit exceeded. Try again in 42 seconds.",
  "error_code": "RATE_LIMIT_EXCEEDED",
  "retry_after": 42
}
```

---

## Webhooks (Roadmap)

### Coming in Q2 2025

**Configure webhooks to receive notifications:**

```json
POST /settings/webhooks
{
  "url": "https://your-app.com/webhooks/excellentinsight",
  "events": ["job.completed", "job.failed"],
  "secret": "whsec_your_secret_key"
}
```

**Webhook Payload Example**
```json
{
  "event": "job.completed",
  "timestamp": "2025-03-08T11:00:00Z",
  "data": {
    "job_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
    "status": "done",
    "dashboard_url": "/dashboard/a1b2c3d4-e5f6-7890-abcd-ef1234567890"
  }
}
```

---

## SDK Examples

### Python SDK (Recommended)
```python
from excellentinsight import Client

client = Client(api_key="YOUR_API_KEY")

# Upload file
job = client.upload_file("data.xlsx")
print(f"Job ID: {job.id}")

# Wait for completion
job.wait_for_completion(timeout=300)

# Get dashboard
dashboard = client.get_dashboard(job.id)
print(f"KPIs: {len(dashboard.kpis)}")
print(f"Charts: {len(dashboard.charts)}")
```

### JavaScript/TypeScript SDK
```typescript
import { ExcellentInsightClient } from '@excellentinsight/sdk';

const client = new ExcellentInsightClient({
  apiKey: 'YOUR_API_KEY'
});

// Upload file
const job = await client.uploadFile(fileBlob);

// Stream progress
client.streamProgress(job.id, (progress) => {
  console.log(`${progress.status}: ${progress.progress}%`);
});

// Get dashboard
const dashboard = await client.getDashboard(job.id);
```

---

## OpenAPI Specification

**Interactive Docs**: `https://api.excellentinsight.com/docs`
**OpenAPI JSON**: `https://api.excellentinsight.com/openapi.json`
**Redoc**: `https://api.excellentinsight.com/redoc`

---

## Support

- **API Status**: https://status.excellentinsight.com
- **GitHub Issues**: https://github.com/moadnane/ExcellentInsight/issues
- **Email**: api-support@excellentinsight.com

---

**Last Updated**: March 2025
**API Version**: v1
**Changelog**: See [CHANGELOG.md](../CHANGELOG.md)
