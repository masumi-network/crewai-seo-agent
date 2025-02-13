FROM python:3.10

# Install Chrome and ChromeDriver dependencies
RUN apt-get update && apt-get install -y \
    wget \
    unzip \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Set Chrome options for running in container
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver
ENV CHROME_OPTIONS="--headless --no-sandbox --disable-dev-shm-usage"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir pika==1.3.1

# Create necessary directories
RUN mkdir -p /app/src/config /app/src/tools /app/src/utils

# Set Python path
ENV PYTHONPATH=/app

# Copy files
COPY . . 