# Use a standard Python image that supports ARM
FROM python:3.9-slim

WORKDIR /app

# Add dependencies required for Debian
RUN apt-get update && apt-get install -y jq && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

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