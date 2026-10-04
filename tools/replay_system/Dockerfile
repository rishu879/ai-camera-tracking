FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/tools/replay_system
COPY tools/utilities /app/tools/utilities
COPY tools/object_detection /app/tools/object_detection
COPY tools/object_tracking /app/tools/object_tracking
COPY tools/kalman_prediction /app/tools/kalman_prediction
COPY tools/pid_controller /app/tools/pid_controller
COPY tools/performance_monitor /app/tools/performance_monitor
COPY tools/configuration /app/tools/configuration
COPY tools/__init__.py /app/tools/

ENV PYTHONPATH=/app

EXPOSE 8014

CMD ["python", "-m", "tools.replay_system.main", "--host", "0.0.0.0", "--port", "8014"]
