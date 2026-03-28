# Stage 1: Build the Vue frontend
FROM node:20-alpine AS build-stage
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# Stage 2: Build the FastAPI backend
FROM python:3.10-slim AS production-stage

WORKDIR /app

# Install necessary system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy backend requirements and install Python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code
COPY backend/ ./backend/
# Copy the built frontend into static dir
COPY --from=build-stage /app/frontend/dist ./backend/static
# Copy other necessary files
COPY data/ ./data/
COPY SOUL.md .

# Change to the backend directory since FastAPI app runs from there
WORKDIR /app/backend

# Expose port
EXPOSE 8000

# Start Uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
