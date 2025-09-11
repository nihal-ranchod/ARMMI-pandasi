# AMMINA - African Manufacturing Market Intelligence & Network Analysis

A modern web application for analyzing pharmaceutical manufacturing and market intelligence datasets using natural language queries. Built with Flask, MongoDB, and OpenAI GPT-4o-mini, developed by Health 4 Development (H4D).

## Features

### User Authentication
- Secure user registration and login system
- MongoDB-based user management
- Session-based authentication
- Individual user data isolation

### Natural Language Data Analysis
- Ask questions about your data in plain English using **PandasAI** + **GPT-4o-mini**
- Multi-dataset support: Upload and query multiple CSV/Excel files
- Intelligent data processing and visualization generation
- Automatic fallback to direct OpenAI processing when needed

### Data Management
- **Per-user data storage** in MongoDB (no local file storage)
- Drag-and-drop file upload interface
- Dataset preview, statistics, and management
- Support for CSV, XLSX, and XLS formats with multiple encodings
- Dataset renaming and deletion capabilities

### Modern User Interface
- **Professional three-section login design** with H4D branding
- Responsive layout optimized for desktop and tablet
- Real-time query execution with progress indicators
- Comprehensive query history tracking per user
- Interactive data visualizations with Plotly

## Architecture

### Frontend
- **HTML/CSS/JavaScript**: Modern pharmaceutical-themed UI with H4D colors
- **Plotly.js**: Interactive data visualizations
- **Responsive Design**: Three-section login, dashboard, and analysis views

### Backend
- **Flask**: Python web framework with RESTful API design
- **MongoDB**: User authentication and data storage
- **PandasAI**: Natural language data querying with GPT-4o-mini
- **OpenAI GPT-4o-mini**: Fallback for intelligent data analysis
- **Flask-Session**: Secure session management

## Quick Start

### Prerequisites
- Python 3.9+
- MongoDB (local installation or MongoDB Atlas)
- OpenAI API key

### 1. Clone and Setup
```bash
git clone <repository-url>
cd ARMMI-pandasi

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\\Scripts\\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration
Create a `.env` file in the backend directory:
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/ammina  # Or your MongoDB Atlas URI

# Flask Configuration
SECRET_KEY=your-secret-key-for-sessions-change-in-production
FLASK_ENV=development  # Set to 'production' for production
```

### 3. Run the Application
```bash
cd backend
python app.py
```

The application will be available at `http://localhost:5000`

## 📋 Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `OPENAI_API_KEY` | OpenAI API key for GPT-4o-mini | Yes | - |
| `MONGODB_URI` | MongoDB connection URI | Yes | `mongodb://localhost:27017/ammina` |
| `SECRET_KEY` | Flask secret key for sessions | Yes | Generated UUID |
| `FLASK_ENV` | Flask environment | No | `development` |

## Usage Guide

### 1. **Registration & Login**
- Visit the application and create an account
- Login with your credentials
- Each user has isolated data storage

### 2. **Upload Datasets**
- Navigate to the "Datasets" section
- Drag and drop CSV or Excel files (up to 100MB)
- Files are processed and stored in your personal MongoDB space
- View dataset previews, statistics, and manage your data

### 3. **Natural Language Queries**
- Go to the "Query" section
- Select one or more of your datasets
- Ask questions in plain English:
  - *"Show me the distribution of manufacturers by country"*
  - *"List all organizations located in Kenya"* 
  - *"Plot product classes by therapeutic area"*
  - *"What are the most common product categories?"*

### 4. **View Results & History**
- Results include intelligent text responses and auto-generated visualizations
- All queries are saved in your personal history
- Export functionality (in development)

## Security & Data Management

- **User Isolation**: Each user's data is completely separate
- **No Local Storage**: All data stored securely in MongoDB
- **Session Management**: Secure Flask sessions with user authentication
- **File Validation**: Comprehensive upload validation and sanitization
- **Encoding Support**: UTF-8, Latin-1, ISO-8859-1, CP1252, UTF-16

## API Documentation

### Authentication Endpoints
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login  
- `POST /api/auth/logout` - User logout
- `GET /api/auth/me` - Get current user info

### Data Management Endpoints
- `GET /api/datasets` - List user's datasets
- `POST /api/upload` - Upload new dataset
- `GET /api/datasets/{id}/preview` - Dataset preview
- `GET /api/datasets/{id}/stats` - Dataset statistics
- `PUT /api/datasets/{id}/rename` - Rename dataset
- `DELETE /api/datasets/{id}` - Delete dataset

### Query Endpoints
- `POST /api/query` - Execute natural language query
- `GET /api/query-history` - Get user's query history
- `GET /api/export/{id}` - Export query results

## Troubleshooting

### Common Issues

**MongoDB Connection Issues**
- Ensure MongoDB is running locally or MongoDB Atlas is accessible
- Check `MONGODB_URI` environment variable
- Verify network connectivity for Atlas connections

**Authentication Problems** 
- Clear browser cookies/session data
- Check `SECRET_KEY` is set in environment
- Restart the Flask application

**Query Execution Errors**
- Verify `OPENAI_API_KEY` is valid and has credits
- Check dataset selection in the query interface
- Review query history for error details

**File Upload Issues**
- Maximum file size: 100MB
- Supported formats: CSV, XLSX, XLS
- Try different encodings if CSV upload fails

### Debug Mode
```bash
export FLASK_DEBUG=True
export FLASK_ENV=development
cd backend
python app.py
```

## Development

### Project Structure
```
AMMINA/
├── backend/
│   ├── app.py              # Flask application entry point
│   ├── auth/               # Authentication system
│   ├── services/           # Business logic services
│   └── utils/              # Utility functions
├── frontend/               # Static web files
│   ├── index.html          # Main application
│   ├── login.html          # Login/registration page
│   └── static/             # CSS, JS, assets
├── docs/                   # Documentation
├── requirements.txt        # Python dependencies
└── README.md              # This file
```

### Key Technologies
- **Flask 2.3+**: Web framework
- **PyMongo**: MongoDB integration
- **PandasAI**: Natural language data queries
- **OpenAI Python SDK**: GPT integration  
- **Pandas**: Data processing
- **Plotly**: Data visualization

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---