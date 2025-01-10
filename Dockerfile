FROM python:3.10.6-buster

WORKDIR /app

# Create a non-root user
RUN useradd -m -u 1000 appuser

# Copy requirements and install
COPY requirements.txt .
COPY key.json .
COPY api ./api
COPY scripts ./scripts

# Install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Change ownership to non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser



CMD exec uvicorn api.simple:app --host 0.0.0.0 --port $PORT
