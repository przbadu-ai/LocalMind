#!/bin/bash
#
# Build and push the LocalMind base image to GHCR
#
# This image contains heavy dependencies (docling, PyTorch, etc.) pre-installed.
# Only run this script when:
#   - docling version changes in requirements.txt
#   - Python version changes
#   - System dependencies change (Docker CLI, etc.)
#
# Usage:
#   ./scripts/build-base-image.sh
#
# Prerequisites:
#   - Docker logged in to GHCR: docker login ghcr.io -u YOUR_USERNAME
#

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

IMAGE_NAME="ghcr.io/przbadu/localmind-base"
IMAGE_TAG="latest"

echo "============================================"
echo "Building LocalMind Base Image"
echo "============================================"
echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo "Context: ${PROJECT_ROOT}/backend"
echo ""
echo "This will take ~40 minutes on first build."
echo "============================================"
echo ""

# Build the base image
echo "==> Building base image..."
docker build \
    -f "${PROJECT_ROOT}/backend/Dockerfile.base" \
    -t "${IMAGE_NAME}:${IMAGE_TAG}" \
    "${PROJECT_ROOT}/backend"

echo ""
echo "==> Build complete!"
echo ""

# Push to registry
echo "==> Pushing to GHCR..."
docker push "${IMAGE_NAME}:${IMAGE_TAG}"

echo ""
echo "============================================"
echo "Base image pushed successfully!"
echo "Image: ${IMAGE_NAME}:${IMAGE_TAG}"
echo ""
echo "You can now run 'kamal deploy' - builds will be much faster."
echo "============================================"
