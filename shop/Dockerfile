# Use a base Home Assistant add-on image for armv7
FROM homeassistant/armv7-base-python:3.11-alpine3.19

WORKDIR /app

# Add dependencies required for Alpine
RUN apk add --no-cache py3-pip py3-wheel jq

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