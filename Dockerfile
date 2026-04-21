FROM python:3.13-slim

# System dependencies for geospatial stack + rclone
RUN apt-get update && apt-get install -y --no-install-recommends \
    gdal-bin \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[all]"

# Copy source
COPY . .
RUN pip install --no-cache-dir -e .
RUN pip install --no-cache-dir boto3

ENV CORRIDOR_DATA_ROOT=/data
RUN mkdir -p /data

# Railway sets PORT dynamically — app must listen on it
ENV PORT=8000

EXPOSE ${PORT}

CMD ["sh", "-c", "uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT}"]
