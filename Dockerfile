FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for Playwright Chromium
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget \
    gnupg \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browser and system dependencies
RUN python -m playwright install --with-deps chromium

# Copy application source code
COPY . .

# Ensure data directory exists
RUN mkdir -p data/fb_profiles

# Expose port
EXPOSE 8000

# Run FastAPI app with Uvicorn
CMD ["uvicorn", "web.app:app", "--host", "0.0.0.0", "--port", "8000"]
