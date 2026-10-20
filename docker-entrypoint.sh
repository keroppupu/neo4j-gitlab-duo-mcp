#!/bin/bash
set -e

# Set initial password if NEO4J_AUTH is provided
if [ -n "$NEO4J_AUTH" ] && [ "$NEO4J_AUTH" != "none" ]; then
    IFS='/' read -r USERNAME PASSWORD <<< "$NEO4J_AUTH"
    if [ -n "$USERNAME" ] && [ -n "$PASSWORD" ]; then
        neo4j-admin dbms set-initial-password "$PASSWORD" 2>/dev/null || true
    fi
fi

exec "$@"
