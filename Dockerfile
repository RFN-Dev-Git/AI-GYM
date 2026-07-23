# Use official Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies required by OpenCV and MediaPipe
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy backend source code and configuration
COPY backend/ ./backend/

# Copy assets (containing pose landmarker models)
COPY assets/ ./assets/

# Expose the API port
EXPOSE 8000

# Set environment variables
ENV PYTHONPATH=/app/backend
ENV HOST=0.0.0.0
ENV PORT=8000

# Add healthcheck to verify container is alive and working
HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/api/health')" || exit 1

# Start the FastAPI uvicorn server (bind to 0.0.0.0 so it is accessible outside Docker)
CMD ["python", "-m", "uvicorn", "src.server.app:app", "--host", "0.0.0.0", "--port", "8000"]
