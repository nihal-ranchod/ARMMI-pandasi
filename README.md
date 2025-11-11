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

## 🚀 Deployment

### Deploy to Render.com

This application is configured for easy deployment on [Render.com](https://render.com) with Docker support.

#### Prerequisites
1. **GitHub Account** - Your code repository
2. **Render Account** - Free at [render.com](https://render.com)
3. **MongoDB Atlas Account** - Free tier at [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
4. **OpenAI API Key** - From [platform.openai.com](https://platform.openai.com/api-keys)

#### Step 1: Setup MongoDB Atlas (5 minutes)

1. **Create MongoDB Atlas Account**
   - Go to [mongodb.com/cloud/atlas](https://www.mongodb.com/cloud/atlas)
   - Sign up for free (no credit card required)

2. **Create a Free Cluster**
   - Click "Build a Database"
   - Select "M0 Free" tier (512MB storage)
   - Choose your preferred cloud region (closest to your users)
   - Click "Create Cluster"

3. **Create Database User**
   - Go to "Database Access" in the left sidebar
   - Click "Add New Database User"
   - Choose "Password" authentication
   - Create a username and secure password (save these!)
   - Set user privileges to "Read and write to any database"
   - Click "Add User"

4. **Configure Network Access**
   - Go to "Network Access" in the left sidebar
   - Click "Add IP Address"
   - Click "Allow Access From Anywhere" (0.0.0.0/0)
   - Click "Confirm"
   - Note: This is required for Render to connect to your database

5. **Get Connection String**
   - Go to "Database" and click "Connect" on your cluster
   - Choose "Connect your application"
   - Copy the connection string (looks like `mongodb+srv://...`)
   - Replace `<password>` with your actual database password
   - Save this connection string for Render configuration

#### Step 2: Prepare Your Repository (2 minutes)

1. **Update render.yaml** (if needed)
   - Open [render.yaml](render.yaml)
   - Update the `repo` URL with your GitHub username/organization
   - Review environment variable defaults

2. **Generate Required Keys**
   ```bash
   # Generate Flask SECRET_KEY
   python -c "import secrets; print('SECRET_KEY:', secrets.token_hex(32))"

   # Create your own ADMIN_REGISTRATION_KEY (any secure string)
   python -c "import secrets; print('ADMIN_REGISTRATION_KEY:', secrets.token_urlsafe(32))"
   ```
   Save these keys - you'll need them for Render configuration.

3. **Push to GitHub** (if not already done)
   ```bash
   git add .
   git commit -m "Prepare for Render deployment"
   git push origin main
   ```

#### Step 3: Deploy on Render (10 minutes)

##### Option A: Using Blueprint (Recommended - Automated)

1. **Create Blueprint from Repository**
   - Log in to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Blueprint"
   - Connect your GitHub account if not already connected
   - Select your repository (`ARMMI-pandasi`)
   - Render will automatically detect [render.yaml](render.yaml)
   - Click "Apply"

2. **Configure Environment Variables**
   - Render will create a new web service
   - Go to your service → "Environment" tab
   - Set the following **required** variables:
     ```
     MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/
     OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxxxxxxxxx
     SECRET_KEY=<generated_secret_key_from_step_2>
     ADMIN_REGISTRATION_KEY=<your_secure_admin_key>
     ```
   - Review optional variables (CORS_ORIGINS, MAX_CONTENT_LENGTH, etc.)
   - Click "Save Changes"

3. **Trigger Deployment**
   - Render will automatically start building and deploying
   - Monitor the "Logs" tab for build progress
   - Wait for "Deploy successful" message (5-10 minutes first time)

##### Option B: Manual Setup (Alternative)

1. **Create New Web Service**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure Service Settings**
   - **Name**: `ammina-platform` (or your choice)
   - **Region**: Choose closest to your users
   - **Branch**: `main`
   - **Runtime**: Select "Docker"
   - **Dockerfile Path**: `./Dockerfile`
   - **Docker Build Context Directory**: `.` (root)
   - **Instance Type**: Free (or Starter $7/month for better performance)

3. **Set Environment Variables** (same as Option A above)

4. **Create Web Service** - Click "Create Web Service"

#### Step 4: Post-Deployment (5 minutes)

1. **Get Your Application URL**
   - Render provides a URL like: `https://ammina-platform.onrender.com`
   - This is your live application URL!

2. **Test the Deployment**
   - Visit your Render URL
   - Try to register a new user account
   - Upload a test dataset (CSV/Excel)
   - Run a natural language query

3. **Create Admin Account** (if needed)
   - Use the `ADMIN_REGISTRATION_KEY` you set in environment variables
   - During registration, enter this key to create admin accounts

4. **Configure Custom Domain** (Optional)
   - Go to your service → "Settings" tab
   - Click "Add Custom Domain"
   - Follow DNS configuration instructions
   - Free SSL certificates are automatically provisioned

#### Step 5: Ongoing Management

**Monitor Your Application**
- View logs in real-time on Render dashboard
- Set up health check alerts
- Monitor MongoDB usage in Atlas dashboard

**Auto-Deploy on Git Push**
- Render automatically deploys when you push to `main` branch
- Disable in service settings if you prefer manual deployments

**Scale Your Application**
- **Free Tier**: Spins down after 15 minutes of inactivity (cold starts ~30s)
- **Starter ($7/month)**: Always running, 512MB RAM, better performance
- **Standard ($25/month)**: 2GB RAM, horizontal scaling available

**Update Environment Variables**
- Go to service → "Environment" tab
- Add/modify variables as needed
- Click "Save Changes" to trigger redeployment

#### Troubleshooting Render Deployment

**Build Fails**
- Check [Dockerfile](Dockerfile) syntax
- Review build logs for missing dependencies
- Ensure all `requirements.txt` packages are available

**Application Won't Start**
- Verify `MONGODB_URI` is correct and MongoDB Atlas is accessible
- Check `OPENAI_API_KEY` is valid
- Ensure `SECRET_KEY` is set
- Review application logs for specific errors

**Database Connection Errors**
- Verify MongoDB Atlas IP whitelist includes 0.0.0.0/0
- Check database user credentials in `MONGODB_URI`
- Ensure cluster is running (not paused)

**Slow Performance on Free Tier**
- Free tier spins down after inactivity (causes cold starts)
- Upgrade to Starter plan ($7/month) for always-on service
- Consider caching strategies for better performance

**OpenAI API Errors**
- Verify API key is active and has credits
- Check OpenAI usage limits and quotas
- Review query logs for specific error messages

#### Cost Estimate

| Service | Tier | Monthly Cost |
|---------|------|--------------|
| **Render Web Service** | Free | $0 |
| **Render Web Service** | Starter | $7 |
| **MongoDB Atlas** | M0 Free | $0 |
| **OpenAI API** | Usage-based | Variable ($0.15/$0.60 per 1M tokens) |
| **Total (Free tier)** | - | **~$0-5** (OpenAI only) |
| **Total (Production)** | - | **~$7-15** |

#### Alternative Deployment Options

If Render doesn't meet your needs, this application also supports:
- **Fly.io** - Docker-based, generous free tier
- **Railway** - Already configured with [railway.toml](railway.toml)
- **DigitalOcean App Platform** - $5/month minimum
- **AWS/GCP/Azure** - VM-based deployment with Docker

See [.env.example](.env.example) for full environment variable documentation.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

---