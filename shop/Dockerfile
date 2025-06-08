# Use a single-stage build for simplicity
FROM python:3.11-slim-bullseye

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PORT=8080
ENV HOST=0.0.0.0

# Expose the application port
EXPOSE 8080

# Make entrypoint script executable
RUN chmod +x entrypoint.sh

# Start the application
CMD ["./entrypoint.sh"]