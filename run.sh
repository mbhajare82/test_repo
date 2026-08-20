#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
pip install -r requirements.txt -q
exec python3 app.py
