FROM python:3.9-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for vector db
RUN mkdir -p /app/data/chroma

# Set environment variables
ENV PYTHONPATH=/app
ENV PORT=8000
ENV HOST=0.0.0.0
ENV DEBUG=False

# Expose port
EXPOSE 8000

# Start the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"] 