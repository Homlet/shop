#!/bin/sh

# For Home Assistant Addons - use the supervisor API token if available
if [ -f /data/options.json ]; then
    echo "Loading configuration from /data/options.json"
    
    # Set environment variables based on the options.json file
    export HA_URL=http://supervisor/core
    export HA_TOKEN=$(jq --raw-output ".ha_token // empty" /data/options.json)
    
    # If HA_TOKEN is empty, try using the supervisor token
    if [ -z "$HA_TOKEN" ] && [ -n "$SUPERVISOR_TOKEN" ]; then
        export HA_TOKEN=${SUPERVISOR_TOKEN}
        echo "Using Home Assistant Supervisor token for authentication"
    fi
    
    # Export other configuration values
    export TODO_LIST_ENTITY_ID=$(jq --raw-output ".todo_list_entity_id // \"todo.shopping\"" /data/options.json)
    export LLM_MODEL=$(jq --raw-output ".llm_model // empty" /data/options.json)
    export LLM_API_KEY=$(jq --raw-output ".llm_api_key // empty" /data/options.json)
    export DEFAULT_STORE=$(jq --raw-output ".default_store // \"Grocery Store\"" /data/options.json)
    export RECEIPT_WIDTH=$(jq --raw-output ".receipt_width // 32" /data/options.json)
    export LOG_LEVEL=$(jq --raw-output ".log_level // \"INFO\"" /data/options.json)
    
    # Store the stores configuration as JSON string
    export STORES=$(jq --compact-output ".stores // []" /data/options.json)
fi

# Set default port and host if not already set
export PORT=${PORT:-8080}
export HOST=${HOST:-0.0.0.0}

echo "Starting application on $HOST:$PORT"
python3 -m uvicorn app.main:app --host $HOST --port $PORT