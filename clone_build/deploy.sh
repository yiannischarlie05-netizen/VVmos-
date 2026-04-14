#!/bin/bash
# Deploy cloned VMOS container to Edge instance
# Usage: ./deploy.sh <edge_host_ip> [registry_host:port]

set -e

EDGE_HOST="${1:?Usage: ./deploy.sh <edge_host_ip> [registry:port]}"
REGISTRY="${2:-localhost:5000}"
IMAGE_NAME="armcloud-proxy/armcloud/clone-app6476kyh9kmlu5"
IMAGE_TAG="latest"
FULL_TAG="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "=== VMOS Edge Clone Deployer ==="
echo "Edge Host: $EDGE_HOST"
echo "Image: $FULL_TAG"
echo ""

# Create instance
echo "[1/2] Creating VMOS Edge instance..."
RESPONSE=$(curl -s -X POST "http://${EDGE_HOST}:18182/container_api/v1/create" \
    -H "Content-Type: application/json" \
    -d '{
        "user_name": "android15-clone-sm-s9310",
        "bool_start": true,
        "image_repository": "'$FULL_TAG'",
        "resolution": "1440x3120",
        "count": 1
    }')

echo "  Response: $RESPONSE"

# Extract db_id
DB_ID=$(echo "$RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('data',{}).get('db_id',''))" 2>/dev/null || echo "")

if [ -n "$DB_ID" ]; then
    echo ""
    echo "[2/2] Instance created!"
    echo "  DB ID: $DB_ID"
    echo ""
    echo "  Check status: curl -s http://${EDGE_HOST}:18182/container_api/v1/list"
    echo "  ADB connect:  adb connect ${EDGE_HOST}:<adb_port>"
else
    echo ""
    echo "  ⚠ Could not extract db_id from response"
    echo "  Check Edge API logs for details"
fi
