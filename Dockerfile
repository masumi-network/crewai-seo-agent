FROM python:3.10

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