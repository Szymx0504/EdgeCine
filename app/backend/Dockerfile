FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for psycopg2 and ONNX
RUN apt-get update && apt-get install -y \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies (using CPU-only torch to save 5GB and avoid hash errors)
COPY requirements.txt .
RUN pip install --no-cache-dir --extra-index-url https://download.pytorch.org/whl/cpu torch
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code from local app/backend to container's /app/backend
COPY app/backend ./backend
COPY models ./models
COPY .env .

# Set Python path to find the 'backend' folder
ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
