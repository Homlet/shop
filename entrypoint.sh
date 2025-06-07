#!/bin/bash

# For Home Assistant Addons - use the supervisor API token if available
if [ -f /var/run/s6/container_environment/SUPERVISOR_TOKEN ]; then
export HA_URL=http://supervisor/core
    export HA_TOKEN=${SUPERVISOR_TOKEN}
    echo "Using Home Assistant Supervisor token for authentication"
fi

# Start the application
exec python -m uvicorn app.main:app --host $HOST --port $PORT