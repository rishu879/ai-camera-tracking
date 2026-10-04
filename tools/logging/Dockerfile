FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/tools/logging
COPY tools/utilities /app/tools/utilities
COPY tools/__init__.py /app/tools/

ENV PYTHONPATH=/app

EXPOSE 8002

CMD ["python", "-m", "tools.logging.main", "--host", "0.0.0.0", "--port", "8002"]
