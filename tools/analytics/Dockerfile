FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/tools/analytics
COPY tools/utilities /app/tools/utilities
COPY tools/configuration /app/tools/configuration
COPY tools/__init__.py /app/tools/

ENV PYTHONPATH=/app

EXPOSE 8013

CMD ["python", "-m", "tools.analytics.main", "--host", "0.0.0.0", "--port", "8013"]
