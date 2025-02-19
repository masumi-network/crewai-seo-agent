FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    xvfb \
    chromium \
    chromium-driver \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create config directory
RUN mkdir -p /app/config

COPY . .

# Set display for Chrome/Chromium
ENV DISPLAY=:99

# Set Chrome binary path for both architectures
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Add FastAPI specific configurations
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:8000/health || exit 1

# Update the command to match docker-compose
CMD ["uvicorn", "src.service:app", "--host", "0.0.0.0", "--port", "8000", "--reload"] 