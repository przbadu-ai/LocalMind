#!/bin/sh
# Docker entrypoint script for LocalMind frontend
# Substitutes environment variables in nginx config template

set -e

# Default values
export BACKEND_HOST="${BACKEND_HOST:-localmind-backend}"
export BACKEND_PORT="${BACKEND_PORT:-52817}"

# Substitute environment variables in nginx config
envsubst '${BACKEND_HOST} ${BACKEND_PORT}' < /etc/nginx/templates/nginx.conf.template > /etc/nginx/conf.d/default.conf

# Execute the main command (nginx)
exec "$@"
