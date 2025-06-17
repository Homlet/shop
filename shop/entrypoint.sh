#!/usr/bin/with-contenv bashio

echo "=== APPLICATION STARTUP $(date) ==="

# Set default environment variables
export HA_URL=${HA_URL:-http://supervisor/core}
export PORT=${PORT:-8080}
export HOST=${HOST:-0.0.0.0}

# Debug: Print environment variables at start
echo "--- Initial environment variables ---"
env | sort
echo "-----------------------------------"

# For Home Assistant Addons - use the supervisor API token
if [ -n "$SUPERVISOR_TOKEN" ]; then
    echo "Using Home Assistant Supervisor token for authentication"
    export HA_TOKEN=${SUPERVISOR_TOKEN}
fi

# Load configuration from options.json (for HA addon)
if [ -f /data/options.json ]; then
    echo "Loading configuration from /data/options.json"
    
    # Debug: Show the content of options.json
    echo "--- Content of options.json ---"
    cat /data/options.json
    echo "-----------------------------"
    
    # Export configuration values
    export TODO_LIST_ENTITY_ID=$(jq -r '.todo_list_entity_id // ""' /data/options.json)
    export LLM_MODEL=$(jq -r '.llm_model // ""' /data/options.json)
    export LLM_API_KEY=$(jq -r '.llm_api_key // ""' /data/options.json)
    export DEFAULT_STORE=$(jq -r '.default_store // ""' /data/options.json)
    export RECEIPT_WIDTH=$(jq -r '.receipt_width // ""' /data/options.json)
    export LOG_LEVEL=$(jq -r '.log_level // ""' /data/options.json)
    
    # Store the stores configuration as JSON string
    export STORES=$(jq -c '.stores // []' /data/options.json)
    
    # Debug: Show the STORES environment variable
    echo "--- STORES environment variable ---"
    echo "$STORES"
    echo "--------------------------------"
fi

# Debug: Print final environment variables
echo "--- Final environment variables ---"
env | sort
echo "----------------------------------"

echo "Starting application on $HOST:$PORT"
. /venv/bin/activate
python3 -m uvicorn app.main:app --host $HOST --port $PORT
