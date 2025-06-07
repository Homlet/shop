#!/bin/bash

# Start the application with uvicorn
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8080