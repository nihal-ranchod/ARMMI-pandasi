# Development Guide

This guide covers setting up PharmaQuery for local development, contributing guidelines, and development best practices.

## 🚀 Quick Setup

### Prerequisites
- Python 3.9+
- Git
- OpenAI API key
- Code editor (VS Code recommended)

### 1. Clone & Setup
```bash
# Clone repository
git clone <repository-url>
cd ARMMI-pandasi

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### 2. Run Development Server
```bash
cd backend
python app.py
```

Open http://localhost:5000 in your browser.

## 📁 Project Structure

```
ARMMI-pandasi/
├── backend/                 # Flask backend
│   ├── api/                # API route handlers
│   ├── models/             # Data models
│   ├── services/           # Business logic
│   │   ├── data_processor.py    # Dataset management
│   │   └── query_engine.py      # Query execution
│   ├── utils/              # Utility functions
│   │   └── file_validator.py    # File validation
│   └── app.py              # Main Flask application
├── frontend/               # Static frontend files
│   ├── static/
│   │   ├── css/
│   │   │   └── main.css    # Main stylesheet
│   │   └── js/
│   │       ├── main.js     # Application logic
│   │       ├── api.js      # API interface
│   │       └── ui.js       # UI utilities
│   └── index.html          # Main HTML file
├── netlify/                # Netlify deployment
│   └── functions/          # Serverless functions
├── docs/                   # Documentation
├── uploads/                # File upload directory
├── requirements.txt        # Python dependencies
├── netlify.toml           # Netlify configuration
└── README.md              # Main documentation
```

## 🛠️ Development Environment

### Recommended VS Code Extensions
- Python
- Pylance
- Black Formatter
- HTML CSS Support
- JavaScript ES6 code snippets
- Live Server

### VS Code Settings
Create `.vscode/settings.json`:
```json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length", "100"],
    "editor.formatOnSave": true
}
```

### Development Dependencies
```bash
pip install -r requirements-dev.txt
```

Create `requirements-dev.txt`:
```
pytest==7.4.0
pytest-flask==1.2.0
black==23.7.0
flake8==6.0.0
pytest-cov==4.1.0
```

## 🧪 Testing

### Backend Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=backend

# Run specific test file
pytest tests/test_data_processor.py
```

### Test Structure
```
tests/
├── test_data_processor.py
├── test_query_engine.py
├── test_file_validator.py
├── test_api.py
└── conftest.py
```

### Example Test
```python
# tests/test_data_processor.py
import pytest
import pandas as pd
from backend.services.data_processor import DataProcessor

def test_save_dataset(tmp_path):
    processor = DataProcessor(str(tmp_path))
    
    # Create test CSV
    df = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
    test_file = tmp_path / "test.csv"
    df.to_csv(test_file, index=False)
    
    # Mock file upload object
    class MockFile:
        def __init__(self, path):
            self.filename = path.name
            self.path = path
        
        def save(self, filepath):
            import shutil
            shutil.copy2(self.path, filepath)
    
    mock_file = MockFile(test_file)
    result = processor.save_dataset(mock_file)
    
    assert 'id' in result
    assert result['rows'] == 3
    assert result['columns'] == 2
```

### Frontend Testing
```bash
# Install testing dependencies
npm install -D jest jsdom

# Run tests
npm test
```

## 🔧 Configuration

### Environment Variables
```bash
# .env file
OPENAI_API_KEY=sk-your-key-here
FLASK_ENV=development
FLASK_DEBUG=True
MAX_CONTENT_LENGTH=104857600
UPLOAD_FOLDER=uploads
```

### Flask Configuration
```python
# backend/config.py
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_CONTENT_LENGTH', 104857600))
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER', 'uploads')
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
```

## 🎨 Frontend Development

### CSS Architecture
The CSS uses CSS custom properties for theming:

```css
:root {
    --primary-color: #2563eb;
    --secondary-color: #64748b;
    --success-color: #10b981;
    --error-color: #ef4444;
    /* ... other variables */
}
```

### JavaScript Modules
- **main.js**: Main application logic and state management
- **api.js**: API communication layer
- **ui.js**: UI utilities and components

### Adding New Features

#### 1. Backend Endpoint
```python
# backend/app.py
@app.route('/api/new-endpoint', methods=['POST'])
def new_endpoint():
    try:
        data = request.get_json()
        # Process data
        result = process_data(data)
        return jsonify({'success': True, 'data': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
```

#### 2. Frontend API Call
```javascript
// frontend/static/js/api.js
class API {
    static async newEndpoint(data) {
        return this.request('/new-endpoint', {
            method: 'POST',
            body: JSON.stringify(data),
        });
    }
}
```

#### 3. Frontend UI
```javascript
// frontend/static/js/main.js
async function handleNewFeature() {
    try {
        const result = await API.newEndpoint(data);
        if (result.success) {
            UI.showToast('Success!', 'success');
        }
    } catch (error) {
        UI.showToast('Error: ' + error.message, 'error');
    }
}
```

## 🐛 Debugging

### Backend Debugging
```python
# Enable debug mode
export FLASK_DEBUG=True
export FLASK_ENV=development

# Use debugger
import pdb; pdb.set_trace()

# Logging
import logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.debug("Debug message")
```

### Frontend Debugging
```javascript
// Browser console debugging
console.log('Debug data:', data);
console.error('Error occurred:', error);

// Breakpoints
debugger; // Browser will pause here

// Network tab: Monitor API calls
// Application tab: Check localStorage/sessionStorage
```

### Common Issues

**CORS Errors**
```python
# backend/app.py - Ensure CORS is properly configured
from flask_cors import CORS
CORS(app)
```

**File Upload Issues**
```python
# Check file size limits
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB

# Verify upload folder exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
```

**OpenAI API Errors**
```python
# Check API key is set
import os
api_key = os.getenv('OPENAI_API_KEY')
if not api_key:
    raise ValueError("OpenAI API key not set")
```

## 📊 Performance

### Backend Optimization
```python
# Use pandas efficiently
df = pd.read_csv(file, nrows=1000)  # Limit rows for preview

# Cache expensive operations
from functools import lru_cache

@lru_cache(maxsize=100)
def expensive_calculation(data_hash):
    # Expensive operation
    return result
```

### Frontend Optimization
```javascript
// Debounce user input
const debouncedSearch = UI.debounce(searchFunction, 300);

// Lazy loading
const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            loadContent(entry.target);
        }
    });
});
```

## 🔄 Git Workflow

### Branch Naming
- `feature/add-new-feature`
- `bugfix/fix-upload-issue`
- `hotfix/critical-security-fix`
- `refactor/optimize-query-engine`

### Commit Messages
```bash
feat: add dataset statistics endpoint
fix: resolve file upload CORS issue
docs: update API documentation
refactor: optimize pandas operations
test: add unit tests for data processor
```

### Pull Request Process
1. Create feature branch from `main`
2. Make changes with tests
3. Update documentation
4. Create pull request
5. Code review
6. Merge to `main`

## 🧪 Sample Data

### Creating Test Datasets
```python
import pandas as pd
import numpy as np

# Clinical trial data
def create_clinical_trial_data(n_patients=1000):
    np.random.seed(42)
    
    data = {
        'patient_id': range(1, n_patients + 1),
        'age': np.random.normal(50, 15, n_patients).astype(int),
        'gender': np.random.choice(['M', 'F'], n_patients),
        'treatment_group': np.random.choice(['A', 'B', 'Placebo'], n_patients),
        'baseline_score': np.random.normal(50, 10, n_patients),
        'endpoint_score': np.random.normal(55, 12, n_patients),
        'adverse_events': np.random.poisson(0.3, n_patients),
        'completion_status': np.random.choice(['Completed', 'Discontinued'], 
                                            n_patients, p=[0.85, 0.15])
    }
    
    df = pd.DataFrame(data)
    df['age'] = df['age'].clip(18, 85)  # Realistic age range
    df['improvement'] = df['endpoint_score'] - df['baseline_score']
    
    return df

# Drug discovery data
def create_drug_discovery_data(n_compounds=500):
    np.random.seed(123)
    
    data = {
        'compound_id': [f'COMP_{i:04d}' for i in range(1, n_compounds + 1)],
        'molecular_weight': np.random.normal(350, 100, n_compounds),
        'logp': np.random.normal(2.5, 1.5, n_compounds),
        'hbd': np.random.poisson(2, n_compounds),
        'hba': np.random.poisson(4, n_compounds),
        'tpsa': np.random.normal(80, 30, n_compounds),
        'ic50': np.random.lognormal(0, 2, n_compounds),
        'solubility': np.random.normal(-3, 1, n_compounds),
        'activity_class': np.random.choice(['Active', 'Inactive', 'Inconclusive'], 
                                         n_compounds, p=[0.3, 0.6, 0.1])
    }
    
    return pd.DataFrame(data)

# Save sample datasets
if __name__ == '__main__':
    clinical_df = create_clinical_trial_data()
    clinical_df.to_csv('sample_clinical_trial.csv', index=False)
    
    drug_df = create_drug_discovery_data()
    drug_df.to_csv('sample_drug_discovery.csv', index=False)
```

## 📝 Code Style

### Python (PEP 8)
```python
# Use descriptive variable names
dataset_processor = DataProcessor()

# Maximum line length: 100 characters
long_variable_name = some_function(
    parameter_one="value",
    parameter_two="another_value"
)

# Type hints
def process_dataset(file_path: str) -> Dict[str, Any]:
    return {"status": "processed"}

# Docstrings
def validate_file(self, file) -> Dict[str, Any]:
    """
    Validate uploaded file for security and compatibility.
    
    Args:
        file: File object to validate
        
    Returns:
        Dict containing validation result and error message if any
    """
```

### JavaScript (ES6+)
```javascript
// Use const/let instead of var
const API_BASE_URL = '/api';
let currentDataset = null;

// Arrow functions for short callbacks
datasets.map(dataset => dataset.name);

// Async/await for promises
async function loadData() {
    try {
        const result = await API.getDatasets();
        return result.data;
    } catch (error) {
        console.error('Failed to load data:', error);
        throw error;
    }
}

// Destructuring
const { success, data, error } = response;
```

### CSS
```css
/* Use CSS custom properties */
:root {
    --primary-color: #2563eb;
}

/* BEM methodology for classes */
.dataset-card__header {}
.dataset-card__content {}
.dataset-card__actions {}

/* Mobile-first responsive design */
.container {
    padding: 1rem;
}

@media (min-width: 768px) {
    .container {
        padding: 2rem;
    }
}
```

## 🚀 Deployment Testing

### Local Production Build
```bash
# Set production environment
export FLASK_ENV=production
export FLASK_DEBUG=False

# Test production build
python backend/app.py
```

### Netlify CLI Testing
```bash
# Install Netlify CLI
npm install -g netlify-cli

# Test functions locally
netlify dev

# Deploy to preview
netlify deploy

# Deploy to production
netlify deploy --prod
```

## 🔧 Troubleshooting

### Common Development Issues

**Python Import Errors**
```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Check Python path
python -c "import sys; print(sys.path)"

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

**JavaScript Errors**
```bash
# Check browser console for errors
# Verify API endpoints are accessible
# Check CORS configuration
```

**File Upload Issues**
```bash
# Check file permissions
chmod 755 uploads/

# Verify disk space
df -h

# Check Flask configuration
echo $MAX_CONTENT_LENGTH
```

This development guide provides a comprehensive foundation for working with PharmaQuery. For specific issues not covered here, please check the GitHub issues or create a new one.