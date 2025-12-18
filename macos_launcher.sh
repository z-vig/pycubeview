#!/bin/bash

# Resolve app directory
APP_DIR="$(cd "$(dirname "$0")/.." && pwd)"

# Path to the real executable
DIST_DIR="$APP_DIR/Resources/main.dist"
EXEC="$DIST_DIR/cubeview"

# Clear quarantine just in case
xattr -dr com.apple.quarantine "$DIST_DIR" 2>/dev/null

# Ensure executable
chmod +x "$EXEC"

# Launch the real app
exec "$EXEC"