#!/bin/bash
# Build and push VMOS Android 15 clone container image
# Usage: ./build.sh [registry_host:port]

set -e

REGISTRY="${1:-localhost:5000}"
IMAGE_NAME="armcloud-proxy/armcloud/clone-app6476kyh9kmlu5"
IMAGE_TAG="latest"
FULL_TAG="${REGISTRY}/${IMAGE_NAME}:${IMAGE_TAG}"

echo "=== VMOS Android 15 Clone Image Builder ==="
echo "Registry: $REGISTRY"
echo "Image: $FULL_TAG"
echo ""

# Step 1: Decompress partition images
echo "[1/4] Decompressing partition images..."
mkdir -p images
for gz in *.img.gz; do
    name=$(basename "$gz" .img.gz)
    if [ ! -f "images/$name.img" ]; then
        echo "  Decompressing $gz..."
        gunzip -c "$gz" > "images/$name.img"
    else
        echo "  images/$name.img already exists"
    fi
done

# Step 2: Build Docker image
echo ""
echo "[2/4] Building Docker image..."
docker build -t "$FULL_TAG" .

# Step 3: Push to registry
echo ""
echo "[3/4] Pushing to registry..."
docker push "$FULL_TAG"

# Step 4: Verify
echo ""
echo "[4/4] Verifying..."
docker manifest inspect "$FULL_TAG" 2>/dev/null || echo "Image pushed (manifest inspect may not be available)"

echo ""
echo "=== BUILD COMPLETE ==="
echo "Image: $FULL_TAG"
echo ""
echo "To deploy via VMOS Edge API:"
echo "  curl -X POST http://<edge_host>:18182/container_api/v1/create \\"
echo "    -H 'Content-Type: application/json' \\"
echo "    -d '{\"user_name\": \"clone\", \"bool_start\": true, \"image_repository\": \"'$FULL_TAG'\"}'"
