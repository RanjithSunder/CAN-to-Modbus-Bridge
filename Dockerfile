FROM python:3.10-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY config.example.ini .

# Create a non-root user
RUN useradd -m -u 1000 bridgeuser && chown -R bridgeuser:bridgeuser /app
USER bridgeuser

# Expose Modbus TCP port
EXPOSE 5020

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import socket; s=socket.socket(); s.settimeout(5); s.connect(('localhost', 5020)); s.close()" || exit 1

# Run the application
CMD ["python", "main.py"]
