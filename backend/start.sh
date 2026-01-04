#!/bin/bash
cd "$(dirname "$0")"
venv/bin/uvicorn main:app --reload --host 0.0.0.0 --port 8000
