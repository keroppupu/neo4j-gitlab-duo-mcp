#!/bin/bash
# ==============================================================================
# Neo4j Knowledge Graph Server Starter Script (Docker / RHEL Container)
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTAINER_NAME="neo4j-rhel-server"
IMAGE_NAME="neo4j-rhel:0.1"
RELEASE_TAR="${SCRIPT_DIR}/dist/neo4j-rhel-0.1.tar.gz"
HTTP_PORT="7474"
BOLT_PORT="7687"
NEO4J_PASSWORD="${NEO4J_PASSWORD:-password123}"
DATA_DIR="${SCRIPT_DIR}/data"

echo "============================================================"
echo " Starting Neo4j Knowledge Graph Server"
echo " Container : ${CONTAINER_NAME}"
echo " Image     : ${IMAGE_NAME}"
echo " HTTP Port : ${HTTP_PORT}"
echo " Bolt Port : ${BOLT_PORT}"
echo " Data Dir  : ${DATA_DIR}"
echo "============================================================"

# 1. Check Docker Daemon
if ! docker info >/dev/null 2>&1; then
    echo "[-] Error: Docker daemon is not running. Please start Docker first."
    exit 1
fi

# 2. Check if Docker image exists locally; if not, check for release tar.gz
if ! docker images --format '{{.Repository}}:{{.Tag}}' | grep -q "^${IMAGE_NAME}$"; then
    echo "[*] Image '${IMAGE_NAME}' not found locally."
    if [ -f "${RELEASE_TAR}" ]; then
        echo "[*] Found release archive: ${RELEASE_TAR}. Loading image..."
        gunzip -c "${RELEASE_TAR}" | docker load
    elif [ -f "${SCRIPT_DIR}/neo4j-rhel-0.1.tar.gz" ]; then
        echo "[*] Found 'neo4j-rhel-0.1.tar.gz'. Loading image..."
        gunzip -c "${SCRIPT_DIR}/neo4j-rhel-0.1.tar.gz" | docker load
    elif [ -f "${SCRIPT_DIR}/Dockerfile.rhel" ]; then
        echo "[*] Release tar not found. Building image from Dockerfile.rhel..."
        docker build -t "${IMAGE_NAME}" -f "${SCRIPT_DIR}/Dockerfile.rhel" "${SCRIPT_DIR}"
    else
        echo "[-] Error: Neither image, release archive, nor Dockerfile.rhel found."
        echo "    Download 'neo4j-rhel-0.1.tar.gz' from GitHub Releases or run from repo root."
        exit 1
    fi
fi

# 3. Handle existing container
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    if docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
        echo "[+] Container '${CONTAINER_NAME}' is already running."
    else
        echo "[*] Starting existing stopped container '${CONTAINER_NAME}'..."
        docker start "${CONTAINER_NAME}"
    fi
else
    # 4. Create data directory for persistence
    mkdir -p "${DATA_DIR}"

    echo "[*] Launching new container '${CONTAINER_NAME}'..."
    docker run -d \
        --name "${CONTAINER_NAME}" \
        -p "${HTTP_PORT}:7474" \
        -p "${BOLT_PORT}:7687" \
        -e NEO4J_AUTH="neo4j/${NEO4J_PASSWORD}" \
        -v "${DATA_DIR}:/var/lib/neo4j/data" \
        --restart unless-stopped \
        "${IMAGE_NAME}"
fi

echo ""
echo "============================================================"
echo "[+] Neo4j Knowledge Graph Server is UP and RUNNING!"
echo "------------------------------------------------------------"
echo "  Web UI (Browser) : http://localhost:${HTTP_PORT}"
echo "  Bolt Connection  : bolt://localhost:${BOLT_PORT}"
echo "  Username         : neo4j"
echo "  Password         : ${NEO4J_PASSWORD}"
echo "============================================================"
echo ""
echo "To stop the server: docker stop ${CONTAINER_NAME}"
echo "To view logs      : docker logs -f ${CONTAINER_NAME}"
