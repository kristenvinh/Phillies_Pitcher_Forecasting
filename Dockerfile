# Use an official lightweight Python runtime
FROM python:3.11-slim

# Set system environment variables to optimize Python performance inside Docker
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Establish our working directory container-side
WORKDIR /app

# Install system dependencies required for compilation extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first to maximize Docker layer caching efficiency
COPY requirements.txt .

# Install python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the ingestion script into the working directory
COPY fetch_and_load.py .
COPY detect_drift.py .

# Expose environment variable placeholders (to be passed at runtime)
ENV GCP_PROJECT_ID=your-gcp-project-id
ENV GOOGLE_APPLICATION_CREDENTIALS=/app/secrets/google_creds.json

# Run the ingestion script when the container executes
CMD ["python", "fetch_and_load.py"]