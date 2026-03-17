# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Environment
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install only the runtime system packages needed for the first AWS deploy.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
       libsm6 \
       libxext6 \
       libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies for production runtime.
# Retrieval/indexing dependencies are excluded because production runs in llm mode.
COPY backend/requirements-prod.txt /app/requirements.txt
RUN python -m pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy backend source
COPY backend /app

# Expose port used by Uvicorn
EXPOSE 8000

# Default command - run the FastAPI app
# The project exposes FastAPI app in module `app.main:app`
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
