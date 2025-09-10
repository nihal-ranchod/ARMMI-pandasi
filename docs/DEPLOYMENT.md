# Deployment Guide

This guide covers deploying PharmaQuery to various platforms, with detailed instructions for Netlify deployment.

## 🌐 Netlify Deployment (Recommended)

### Prerequisites
- GitHub account
- Netlify account
- OpenAI API key

### Step-by-Step Deployment

#### 1. Prepare Repository
```bash
# Clone or fork the repository
git clone <repository-url>
cd ARMMI-pandasi

# Ensure all files are committed
git add .
git commit -m "Prepare for deployment"
git push origin main
```

#### 2. Connect to Netlify

1. **Login to Netlify**
   - Go to [netlify.com](https://netlify.com)
   - Sign up or login with GitHub

2. **Create New Site**
   - Click "New site from Git"
   - Choose GitHub and authorize Netlify
   - Select your repository

3. **Configure Build Settings**
   ```
   Build command: echo "Static site build"
   Publish directory: frontend
   Functions directory: netlify/functions
   ```

#### 3. Set Environment Variables

1. **Access Site Settings**
   - Go to Site Settings > Environment Variables
   - Click "Add variable"

2. **Required Variables**
   ```
   OPENAI_API_KEY=your_openai_api_key_here
   PYTHON_VERSION=3.9
   ```

3. **Optional Variables**
   ```
   FLASK_ENV=production
   MAX_CONTENT_LENGTH=104857600
   ```

#### 4. Configure Build & Deploy

1. **Build Settings**
   - The `netlify.toml` file contains all configuration
   - Python runtime is set to 3.9
   - Functions use the requirements.txt in the functions directory

2. **Deploy Site**
   - Click "Deploy site"
   - Monitor build logs for any issues
   - Site will be available at your Netlify URL

#### 5. Custom Domain (Optional)

1. **Add Custom Domain**
   - Go to Domain Settings
   - Add your custom domain
   - Configure DNS settings

2. **SSL Certificate**
   - Netlify automatically provides SSL
   - Force HTTPS in domain settings

### Build Configuration Details

The `netlify.toml` file includes:

```toml
[build]
  publish = "frontend"
  functions = "netlify/functions"

[build.environment]
  PYTHON_VERSION = "3.9"

# API redirects
[[redirects]]
  from = "/api/*"
  to = "/.netlify/functions/api:splat"
  status = 200

# SPA fallback
[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
```

### Troubleshooting Netlify Deployment

**Build Failures**
```bash
# Check build logs in Netlify dashboard
# Common issues:
# - Missing environment variables
# - Python dependency conflicts
# - File path issues
```

**Function Errors**
```bash
# Check function logs in Netlify dashboard
# Common issues:
# - Import path problems
# - Missing dependencies
# - OpenAI API key not set
```

**CORS Issues**
- Ensure `netlify.toml` redirects are correct
- Check that API functions return proper CORS headers

## 🐳 Docker Deployment

### Dockerfile
```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy application code
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# Set environment variables
ENV FLASK_APP=backend/app.py
ENV FLASK_ENV=production

# Expose port
EXPOSE 5000

# Run the application
CMD ["python", "backend/app.py"]
```

### Docker Compose
```yaml
version: '3.8'
services:
  pharmaquery:
    build: .
    ports:
      - "5000:5000"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - FLASK_ENV=production
    volumes:
      - ./uploads:/app/uploads
```

### Deploy with Docker
```bash
# Build image
docker build -t pharmaquery .

# Run container
docker run -p 5000:5000 -e OPENAI_API_KEY=your_key pharmaquery

# Or use docker-compose
docker-compose up -d
```

## ☁️ AWS Deployment

### AWS Lambda + S3

1. **Package for Lambda**
```bash
pip install -r requirements.txt -t lambda_package/
cp -r backend/ lambda_package/
zip -r pharmaquery-lambda.zip lambda_package/
```

2. **Create Lambda Function**
- Runtime: Python 3.9
- Handler: lambda_function.lambda_handler
- Upload the zip file

3. **Configure API Gateway**
- Create REST API
- Configure resources and methods
- Enable CORS

4. **S3 for Frontend**
```bash
aws s3 sync frontend/ s3://your-bucket-name/
aws s3 website s3://your-bucket-name --index-document index.html
```

### AWS Elastic Beanstalk

1. **Prepare Application**
```bash
zip -r pharmaquery-eb.zip backend/ frontend/ requirements.txt
```

2. **Deploy to Elastic Beanstalk**
- Create new application
- Upload zip file
- Configure environment variables

## 🚀 Other Deployment Options

### Heroku

1. **Prepare Files**
```bash
# Create Procfile
echo "web: python backend/app.py" > Procfile

# Create runtime.txt
echo "python-3.9.0" > runtime.txt
```

2. **Deploy**
```bash
heroku create your-app-name
heroku config:set OPENAI_API_KEY=your_key
git push heroku main
```

### DigitalOcean App Platform

1. **Create App**
- Connect GitHub repository
- Configure build settings
- Set environment variables

2. **Configure**
```yaml
name: pharmaquery
services:
- name: web
  source_dir: /
  github:
    repo: your-username/pharmaquery
    branch: main
  run_command: python backend/app.py
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: OPENAI_API_KEY
    value: your_key
  - key: FLASK_ENV
    value: production
```

### Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Deploy
railway login
railway init
railway add
railway deploy
```

## 🔐 Security Considerations

### Environment Variables
- Never commit API keys to version control
- Use secure environment variable management
- Rotate keys regularly

### HTTPS
- Always use HTTPS in production
- Configure proper SSL certificates
- Set secure headers

### CORS
- Configure CORS properly for your domain
- Don't use wildcard origins in production
- Validate all inputs

### File Upload Security
- Validate file types and sizes
- Scan uploaded files for malware
- Use secure file storage

## 📊 Monitoring & Logging

### Netlify Analytics
- Monitor function invocations
- Track errors and performance
- Set up alerts

### Application Monitoring
```python
# Add logging to your application
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Log important events
logger.info(f"Dataset uploaded: {dataset_id}")
logger.error(f"Query failed: {error}")
```

### Performance Monitoring
- Monitor response times
- Track memory usage
- Set up uptime monitoring

## 🔄 CI/CD Pipeline

### GitHub Actions
```yaml
name: Deploy to Netlify

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Setup Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    
    - name: Install dependencies
      run: pip install -r requirements.txt
    
    - name: Run tests
      run: python -m pytest tests/
    
    - name: Deploy to Netlify
      uses: netlify/actions/cli@master
      with:
        args: deploy --prod --dir=frontend
      env:
        NETLIFY_SITE_ID: ${{ secrets.NETLIFY_SITE_ID }}
        NETLIFY_AUTH_TOKEN: ${{ secrets.NETLIFY_AUTH_TOKEN }}
```

## 🎯 Production Checklist

- [ ] Set all required environment variables
- [ ] Configure proper CORS settings
- [ ] Enable HTTPS/SSL
- [ ] Set up monitoring and logging
- [ ] Configure proper error handling
- [ ] Set up regular backups
- [ ] Test all functionality
- [ ] Configure rate limiting
- [ ] Set up uptime monitoring
- [ ] Document API endpoints
- [ ] Configure security headers

## 📈 Scaling Considerations

### Database
- Consider using PostgreSQL for larger datasets
- Implement connection pooling
- Add database indexing

### Caching
- Implement Redis for query caching
- Add CDN for static assets
- Cache visualization results

### Load Balancing
- Use multiple server instances
- Implement health checks
- Configure auto-scaling

### Performance Optimization
- Optimize pandas operations
- Implement async processing
- Add request queuing for heavy queries