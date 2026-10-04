FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/tools/object_detection
COPY tools/utilities /app/tools/utilities
COPY tools/configuration /app/tools/configuration
COPY tools/__init__.py /app/tools/

ENV PYTHONPATH=/app

EXPOSE 8007

CMD ["python", "-m", "tools.object_detection.main", "--host", "0.0.0.0", "--port", "8007"]
