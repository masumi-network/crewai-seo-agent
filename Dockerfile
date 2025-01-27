# Use Python 3.10 base image
FROM python3.10-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY . /app
RUN pip install .

# Copy source code
COPY src/ src/
COPY .env .

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Run the application
CMD ["python", "-m", "src.main.py"] 