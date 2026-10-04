FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . /app/tools/configuration
COPY tools/utilities /app/tools/utilities
COPY tools/__init__.py /app/tools/

ENV PYTHONPATH=/app

EXPOSE 8001

CMD ["python", "-m", "tools.configuration.main", "--host", "0.0.0.0", "--port", "8001"]
