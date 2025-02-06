FROM python:3.10

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir pika==1.3.1

# Create config directory
RUN mkdir -p /app/config

COPY . .

CMD ["python", "src/main.py"] 