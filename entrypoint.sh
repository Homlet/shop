#!/bin/bash

# Start the application
exec python -m uvicorn app.main:app --host $HOST --port $PORT