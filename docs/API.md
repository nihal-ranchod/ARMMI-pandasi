# API Documentation

PharmaQuery REST API provides endpoints for dataset management, natural language querying, and result export.

## 🔗 Base URL

**Local Development:** `http://localhost:5000/api`  
**Production (Netlify):** `https://your-site.netlify.app/api`

## 🔐 Authentication

Currently, the API uses OpenAI API key authentication set via environment variables. No user authentication is required for the endpoints.

## 📊 Response Format

All API responses follow this structure:

```json
{
  "success": boolean,
  "data": object | array,
  "error": string | null
}
```

### Success Response
```json
{
  "success": true,
  "datasets": [...],
  "error": null
}
```

### Error Response
```json
{
  "success": false,
  "error": "Description of the error"
}
```

## 📋 Endpoints

### Dataset Management

#### 1. List Datasets
**GET** `/api/datasets`

Returns a list of all uploaded datasets.

**Response:**
```json
{
  "success": true,
  "datasets": [
    {
      "id": "uuid-string",
      "name": "Clinical Trial Data",
      "original_filename": "trial_data.csv",
      "upload_date": "2024-01-15T10:30:00",
      "rows": 1500,
      "columns": 25,
      "size_bytes": 2048000
    }
  ]
}
```

#### 2. Upload Dataset
**POST** `/api/upload`

Upload a new CSV or Excel file.

**Request:** `multipart/form-data`
- `file`: The file to upload (CSV, XLSX, XLS)

**Response:**
```json
{
  "success": true,
  "dataset": {
    "id": "new-uuid",
    "name": "Dataset Name",
    "original_filename": "data.csv",
    "upload_date": "2024-01-15T10:30:00",
    "rows": 1000,
    "columns": 20,
    "column_names": ["col1", "col2", ...],
    "column_types": {"col1": "object", "col2": "int64"},
    "size_bytes": 1024000,
    "missing_values": {"col1": 5, "col2": 0},
    "preview": [
      {"col1": "value1", "col2": 123},
      ...
    ]
  }
}
```

**Error Codes:**
- `400`: Invalid file format, file too large, or validation failed
- `500`: Server error during processing

#### 3. Preview Dataset
**GET** `/api/datasets/{dataset_id}/preview`

Get a preview of the first 5 rows of a dataset.

**Response:**
```json
{
  "success": true,
  "preview": {
    "columns": ["col1", "col2", "col3"],
    "data": [
      {"col1": "value1", "col2": 123, "col3": "text"},
      {"col1": "value2", "col2": 456, "col3": "more text"},
      ...
    ],
    "total_rows": 1500
  }
}
```

#### 4. Dataset Statistics
**GET** `/api/datasets/{dataset_id}/stats`

Get detailed statistics about a dataset.

**Response:**
```json
{
  "success": true,
  "stats": {
    "basic_info": {
      "rows": 1500,
      "columns": 25,
      "size_bytes": 2048000,
      "column_types": {
        "age": "int64",
        "name": "object",
        "score": "float64"
      }
    },
    "missing_values": {
      "age": 5,
      "name": 0,
      "score": 12
    },
    "numeric_stats": {
      "age": {
        "mean": 45.2,
        "median": 44.0,
        "std": 12.5,
        "min": 18.0,
        "max": 85.0,
        "unique_count": 67
      },
      "score": {
        "mean": 78.5,
        "median": 80.0,
        "std": 15.2,
        "min": 0.0,
        "max": 100.0,
        "unique_count": 101
      }
    },
    "categorical_stats": {
      "name": {
        "unique_count": 1450,
        "most_common": {
          "John Smith": 3,
          "Jane Doe": 2,
          "Bob Johnson": 2
        }
      }
    }
  }
}
```

#### 5. Rename Dataset
**PUT** `/api/datasets/{dataset_id}/rename`

Rename a dataset.

**Request Body:**
```json
{
  "name": "New Dataset Name"
}
```

**Response:**
```json
{
  "success": true
}
```

#### 6. Delete Dataset
**DELETE** `/api/datasets/{dataset_id}`

Delete a dataset and its associated files.

**Response:**
```json
{
  "success": true
}
```

### Query Execution

#### 7. Execute Query
**POST** `/api/query`

Execute a natural language query on selected datasets.

**Request Body:**
```json
{
  "query": "Show me the distribution of patient ages",
  "datasets": ["dataset-id-1", "dataset-id-2"]
}
```

**Response:**
```json
{
  "success": true,
  "result": {
    "id": "result-uuid",
    "query": "Show me the distribution of patient ages",
    "datasets_used": ["Clinical Trial Data", "Patient Demographics"],
    "timestamp": "2024-01-15T10:35:00",
    "response_type": "mixed",
    "response": "The patient ages in your dataset range from 18 to 85 years...",
    "visualizations": [
      {
        "type": "plotly",
        "title": "Distribution of Patient Ages",
        "html": "<div>Plotly HTML content</div>"
      }
    ],
    "data_tables": [
      {
        "title": "Age Statistics",
        "data": [
          {"statistic": "mean", "value": 45.2},
          {"statistic": "median", "value": 44.0}
        ],
        "columns": ["statistic", "value"]
      }
    ]
  }
}
```

**Error Codes:**
- `400`: Missing query text or no datasets selected
- `500`: Query execution failed or OpenAI API error

### Query History

#### 8. Get Query History
**GET** `/api/query-history`

Get the last 50 queries executed by the user.

**Response:**
```json
{
  "success": true,
  "history": [
    {
      "id": "query-uuid",
      "query": "Show me the distribution of patient ages",
      "datasets": ["Clinical Trial Data"],
      "timestamp": "2024-01-15T10:35:00",
      "success": true
    },
    {
      "id": "query-uuid-2",
      "query": "Find correlations between dose and efficacy",
      "datasets": ["Drug Trial Data"],
      "timestamp": "2024-01-15T09:20:00",
      "success": false,
      "error": "OpenAI API quota exceeded"
    }
  ]
}
```

### Export

#### 9. Export Results
**GET** `/api/export/{result_id}?format=csv`

Export query results to a file.

**Query Parameters:**
- `format`: Export format (`csv` or `json`) - defaults to `csv`

**Response:** Binary file download

**Headers:**
- `Content-Type`: `application/octet-stream`
- `Content-Disposition`: `attachment; filename=query_results_{result_id}.csv`

## 📝 Request Examples

### Using cURL

#### Upload Dataset
```bash
curl -X POST http://localhost:5000/api/upload \
  -F "file=@/path/to/data.csv"
```

#### Execute Query
```bash
curl -X POST http://localhost:5000/api/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the average age of patients?",
    "datasets": ["dataset-uuid"]
  }'
```

#### Get Datasets
```bash
curl -X GET http://localhost:5000/api/datasets
```

### Using JavaScript (Frontend)

#### Upload File
```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('/api/upload', {
  method: 'POST',
  body: formData
});

const result = await response.json();
```

#### Execute Query
```javascript
const response = await fetch('/api/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    query: 'Show me the distribution of ages',
    datasets: ['dataset-id-1']
  })
});

const result = await response.json();
```

### Using Python Requests

#### Upload Dataset
```python
import requests

files = {'file': open('data.csv', 'rb')}
response = requests.post('http://localhost:5000/api/upload', files=files)
result = response.json()
```

#### Execute Query
```python
import requests

data = {
    'query': 'What is the correlation between age and score?',
    'datasets': ['dataset-uuid']
}

response = requests.post('http://localhost:5000/api/query', json=data)
result = response.json()
```

## ⚠️ Error Handling

### Common Error Codes

| Code | Description | Common Causes |
|------|-------------|---------------|
| 400 | Bad Request | Invalid file format, missing parameters |
| 404 | Not Found | Dataset or result not found |
| 413 | Payload Too Large | File exceeds size limit (100MB) |
| 429 | Too Many Requests | OpenAI API rate limit exceeded |
| 500 | Internal Server Error | Server error, OpenAI API error |

### Error Response Examples

#### File Too Large
```json
{
  "success": false,
  "error": "File too large. Maximum size: 100MB"
}
```

#### Dataset Not Found
```json
{
  "success": false,
  "error": "Dataset not found"
}
```

#### OpenAI API Error
```json
{
  "success": false,
  "error": "OpenAI API error: Quota exceeded"
}
```

## 🔒 Security & Rate Limits

### File Upload Security
- **Allowed formats:** CSV, XLSX, XLS only
- **Maximum size:** 100MB
- **File validation:** Content type and structure validation
- **Malware scanning:** Basic file content validation

### Query Limits
- **OpenAI API:** Subject to your OpenAI account limits
- **Query length:** No explicit limit, but very long queries may fail
- **Concurrent queries:** One query per session recommended

### Data Privacy
- **File storage:** Temporary storage in server memory/disk
- **Data retention:** Files are stored until manually deleted
- **API logs:** Query text may be logged for debugging

## 📊 Response Times

Typical response times:

| Endpoint | Average Time | Notes |
|----------|-------------|--------|
| GET /datasets | < 100ms | Metadata only |
| POST /upload | 1-5s | Depends on file size |
| GET /preview | < 500ms | First 5 rows only |
| GET /stats | 1-3s | Full dataset analysis |
| POST /query | 5-30s | Depends on query complexity |

## 🔧 Development & Testing

### Mock Data
For testing, you can create sample pharmaceutical datasets:

```python
import pandas as pd

# Create sample clinical trial data
data = {
    'patient_id': range(1, 101),
    'age': [random.randint(18, 85) for _ in range(100)],
    'treatment_group': ['A', 'B'] * 50,
    'efficacy_score': [random.uniform(0, 100) for _ in range(100)],
    'adverse_events': [random.choice([0, 1]) for _ in range(100)]
}

df = pd.DataFrame(data)
df.to_csv('sample_clinical_trial.csv', index=False)
```

### Testing Queries
Example queries for pharmaceutical data:
- "What is the average efficacy score by treatment group?"
- "Show me the distribution of patient ages"
- "How many patients experienced adverse events?"
- "Is there a correlation between age and efficacy?"
- "Plot the efficacy scores over time"

## 📱 API Versioning

Currently using v1 (no version prefix in URL). Future versions will use `/api/v2/` format.

## 🔄 Changelog

### v1.0.0 (Current)
- Initial API release
- Basic CRUD operations for datasets
- Natural language query execution
- Query history tracking
- Result export functionality