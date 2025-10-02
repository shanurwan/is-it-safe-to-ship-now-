#!/usr/bin/env bash
set -euo pipefail
# Run metrics-gated canary via controller
docker compose run --rm canary-controller python /app/controller.py