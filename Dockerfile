FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for OpenCV and runtime
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Ensure required runtime directories exist
RUN mkdir -p outputs/reports outputs/logs datasets models

ENV PYTHONUNBUFFERED=1
ENV HOST=0.0.0.0
ENV PORT=8000
EXPOSE 8000

CMD ["python", "server.py"]
