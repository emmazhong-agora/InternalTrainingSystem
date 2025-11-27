#!/usr/bin/env bash

# Install or upgrade Docker Compose plugin (v2.40+).
# This script downloads the official binary from GitHub releases.
#
# Usage:
#   sudo scripts/install_compose_plugin.sh [VERSION]
# Example:
#   sudo scripts/install_compose_plugin.sh v2.24.7
#   (If VERSION is omitted, defaults to v2.24.7)

set -euo pipefail

DEFAULT_VERSION="v2.24.7"
VERSION="${1:-$DEFAULT_VERSION}"

# Determine architecture
ARCH="$(uname -sm)"
case "$ARCH" in
  "Linux x86_64")   BINARY="docker-compose-linux-x86_64" ;;
  "Linux aarch64")  BINARY="docker-compose-linux-aarch64" ;;
  "Linux arm64")    BINARY="docker-compose-linux-aarch64" ;;
  "Linux armv7l")   BINARY="docker-compose-linux-armv7" ;;
  *)
    echo "Unsupported architecture: $ARCH" >&2
    exit 1
    ;;
esac

INSTALL_DIR="/usr/local/lib/docker/cli-plugins"
BIN_PATH="$INSTALL_DIR/docker-compose"

echo "Installing Docker Compose $VERSION for $ARCH"
mkdir -p "$INSTALL_DIR"
curl -SL "https://github.com/docker/compose/releases/download/${VERSION}/${BINARY}" -o "$BIN_PATH"
chmod +x "$BIN_PATH"

# Optional legacy symlink for docker-compose v1 compatibility
if ! command -v docker-compose >/dev/null 2>&1; then
  ln -sf "$BIN_PATH" /usr/local/bin/docker-compose
fi

echo "Docker Compose installed at $(docker compose version)"
