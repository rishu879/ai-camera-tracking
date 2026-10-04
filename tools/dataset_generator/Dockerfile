FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/tools/dataset_generator
COPY tools/utilities /app/tools/utilities
COPY tools/simulator /app/tools/simulator
COPY tools/virtual_camera /app/tools/virtual_camera
COPY tools/weather_engine /app/tools/weather_engine
COPY tools/noise_generator /app/tools/noise_generator
COPY tools/configuration /app/tools/configuration
COPY tools/__init__.py /app/tools/

ENV PYTHONPATH=/app

EXPOSE 8011

CMD ["python", "-m", "tools.dataset_generator.main", "--host", "0.0.0.0", "--port", "8011"]
