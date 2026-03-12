FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for psycopg2 and ONNX
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
# Assuming requirements.txt is in the root, but we only need a subset for the container logic
COPY app/backend ./app/backend
COPY models ./models
COPY .env .

# Set Python path to find the 'app' module
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "app.backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
