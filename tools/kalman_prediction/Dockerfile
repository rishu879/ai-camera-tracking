FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/tools/kalman_prediction
COPY tools/utilities /app/tools/utilities
COPY tools/configuration /app/tools/configuration
COPY tools/__init__.py /app/tools/

ENV PYTHONPATH=/app

EXPOSE 8009

CMD ["python", "-m", "tools.kalman_prediction.main", "--host", "0.0.0.0", "--port", "8009"]
