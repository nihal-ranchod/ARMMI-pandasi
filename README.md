# AMMINA - African Manufacturing Market Intelligence & Network Analysis

A comprehensive web application for querying manufacturing and market intelligence datasets using natural language. Built with pandas-ai and OpenAI GPT for intelligent data analysis and visualization, developed by Health 4 Development (H4D).

## Features

### Core Functionality
- **Natural Language Querying**: Ask questions about your data in plain English
- **Multi-dataset Support**: Upload and query multiple CSV/Excel files simultaneously
- **RAG Responses**: Get accurate, context-aware responses based on your data
- **Data Visualizations**: Automatic chart generation with Plotly

### Dataset Management
- Drag-and-drop file upload interface
- Dataset preview and statistics
- File validation and security checks
- Rename and delete datasets
- Support for CSV, XLSX, and XLS formats

### User Interface
- Professional pharmaceutical industry design
- Responsive layout for desktop and tablet
- Real-time query execution with progress indicators
- Query history tracking
- Export results to CSV/PDF

## Architecture

### Frontend
- **HTML/CSS/JavaScript**: Clean, modern pharmaceutical-themed UI
- **Plotly.js**: Interactive data visualizations
- **Responsive Design**: Works on desktop and tablet devices

### Backend
- **Flask**: Python web framework for API endpoints
- **pandas-ai**: Natural language data querying
- **OpenAI GPT**: Large language model integration
- **Plotly**: Server-side visualization generation

### Deployment
- **Netlify**: Static frontend hosting with serverless functions
- **Environment Variables**: Secure API key management
- **CORS Support**: Cross-origin resource sharing enabled

## Requirements

### System Requirements
- Python 3.9+
- Node.js (for local development)
- OpenAI API key

### Python Dependencies
- Flask 2.3.3+
- pandasai 2.3.2
- pandas 1.5.3 (exact version required)
- numpy 1.23.5 (exact version required)  
- plotly 5.17.0+
- openai 1.3.0+
- See `requirements.txt` for complete list

## Quick Start

### Local Development

1. **Clone the repository**
```bash
git clone <repository-url>
cd ARMMI-pandasi
```

2. **Set up Python environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate
pip install -r requirements.txt
```

3. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env and add your OpenAI API key
```

4. **Run the development server**
```bash
cd backend
python app.py
```

5. **Open your browser**
```
http://localhost:5000
```

### Netlify Deployment

1. **Connect to Netlify**
   - Fork this repository
   - Connect your GitHub repo to Netlify
   - Select the main branch

2. **Configure Build Settings**
   - Build command: `echo "Static site"`
   - Publish directory: `frontend`
   - Functions directory: `netlify/functions`

3. **Set Environment Variables**
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   ```

4. **Deploy**
   - Netlify will automatically deploy your site
   - Site will be available at `https://your-site-name.netlify.app`

## Usage Guide

### 1. Upload Datasets
- Navigate to the "Datasets" section
- Drag and drop CSV or Excel files
- Files are validated for format and size
- View dataset previews and statistics

### 2. Query Your Data
- Go to the "Query" section
- Select one or more datasets
- Type your question in natural language
- Examples:
  - "Show me the distribution of patient ages"
  - "What is the average efficacy score by treatment group?"
  - "Find correlations between dose and adverse events"

### 3. View Results
- Results include text responses and visualizations
- Data tables show relevant subsets of your data
- Charts are automatically generated for visual data
- Export results to CSV format

### 4. Track History
- All queries are saved in the "History" section
- View past questions and success/failure status
- Re-run successful queries on new datasets

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENAI_API_KEY` | OpenAI API key for GPT models | Yes |
| `FLASK_ENV` | Flask environment (development/production) | No |
| `MAX_CONTENT_LENGTH` | Maximum file upload size in bytes | No |

### File Limits

- **Maximum file size**: 100MB
- **Maximum rows**: 1,000,000
- **Maximum columns**: 1,000
- **Supported formats**: CSV, XLSX, XLS

### Security Features

- File type validation
- Content validation
- CORS protection
- XSS protection headers
- Content Security Policy

## Customization

### API Endpoints
- Backend API is fully documented in the code
- RESTful design with JSON responses
- Error handling and validation included

## Troubleshooting

### Common Issues

**Installation Issues**
- If you get "pandas-ai not found", use `pip install pandasai` (note: no hyphen)
- For dependency conflicts, try: `pip install --upgrade --force-reinstall pandasai`
- Ensure Python 3.9+ is being used

**Upload Fails**
- Check file size (max 100MB)
- Verify file format (CSV, XLSX, XLS only)
- Ensure proper column headers
- For encoding errors: The system supports UTF-8, Latin-1, ISO-8859-1, CP1252, and UTF-16 encodings
- If upload still fails, try opening your CSV in Excel and saving as "CSV UTF-8" format

**Query Errors**
- Verify OpenAI API key is set correctly
- Check dataset selection
- Ensure query is specific and clear
- If pandasai fails, the system will fallback to direct OpenAI processing

**Deployment Issues**
- Verify environment variables in Netlify
- Check build logs for Python dependency issues
- Ensure functions directory is correct
- Make sure `pandasai` (not `pandas-ai`) is in requirements.txt

### Debug Mode
```bash
export FLASK_DEBUG=True
export FLASK_ENV=development
python backend/app.py
```

## API Documentation

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/datasets` | List all datasets |
| POST | `/api/upload` | Upload new dataset |
| GET | `/api/datasets/{id}/preview` | Preview dataset |
| GET | `/api/datasets/{id}/stats` | Dataset statistics |
| PUT | `/api/datasets/{id}/rename` | Rename dataset |
| DELETE | `/api/datasets/{id}` | Delete dataset |
| POST | `/api/query` | Execute query |
| GET | `/api/query-history` | Get query history |
| GET | `/api/export/{id}` | Export results |

### Response Format
```json
{
  "success": true,
  "data": {},
  "error": null
}
```
## License

This project is licensed under the MIT License - see the LICENSE file for details.
