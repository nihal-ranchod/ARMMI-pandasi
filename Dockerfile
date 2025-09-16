# Use Python 3.11 to avoid distutils issues
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    gfortran \
    libblas-dev \
    liblapack-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Change to backend directory
WORKDIR /app/backend

# Expose port
EXPOSE $PORT

# Start command that handles PORT variable
ENTRYPOINT ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:${PORT:-5000}"]