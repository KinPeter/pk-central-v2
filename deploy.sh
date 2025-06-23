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

# 1b. Update docker-compose.yml image version
DC_FILE="docker-compose.yml"
if [ -f "$DC_FILE" ]; then
  sed -i "s|\(image: kinp/pk-central-v2:\)[^ ]*|\1$NEW_VERSION|" "$DC_FILE"
  echo "Updated $DC_FILE image tag to $NEW_VERSION"
fi

# 2. Build Docker image with new version tag
IMAGE="kinp/pk-central-v2"
docker build -t "$IMAGE:$NEW_VERSION" .

# 3. Push both tags to Docker Hub
docker push "$IMAGE:$NEW_VERSION"

echo "Deployed $IMAGE:$NEW_VERSION to Docker Hub."