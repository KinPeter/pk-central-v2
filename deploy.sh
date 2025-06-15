#!/bin/bash

set -e

# 1. Bump patch version in .version
VERSION_FILE=".version"
if [ ! -f "$VERSION_FILE" ]; then
  echo "0.0.1" > "$VERSION_FILE"
fi

OLD_VERSION=$(cat "$VERSION_FILE")
IFS='.' read -r MAJOR MINOR PATCH <<< "$OLD_VERSION"
PATCH=$((PATCH + 1))
NEW_VERSION="$MAJOR.$MINOR.$PATCH"
echo "$NEW_VERSION" > "$VERSION_FILE"
echo "Bumped version: $OLD_VERSION -> $NEW_VERSION"

# 2. Build Docker image with new version and latest tags
IMAGE="kinp/pk-central-v2"
docker build -t "$IMAGE:$NEW_VERSION" -t "$IMAGE:latest" .

# 3. Push both tags to Docker Hub
docker push "$IMAGE:$NEW_VERSION"
docker push "$IMAGE:latest"

echo "Deployed $IMAGE:$NEW_VERSION and $IMAGE:latest to Docker Hub."