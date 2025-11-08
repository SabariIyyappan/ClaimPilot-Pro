# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies required by some packages (tesseract, build tools, image libs)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       gcc \
       ca-certificates \
       libsm6 \
       libxext6 \
       libxrender-dev \
       tesseract-ocr \
       libtesseract-dev \
       poppler-utils \
       libopenblas-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY backend/requirements.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend /app

# Expose port used by Uvicorn
EXPOSE 8000

# Default command - run the FastAPI app
# The project exposes FastAPI app in module `app.main:app`
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
