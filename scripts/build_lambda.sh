#!/bin/bash
# Build Lambda deployment package for Extraction Job API
# Run from project root: ./scripts/build_lambda.sh

set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
PACKAGE_DIR="$PROJECT_ROOT/package"
ZIP_PATH="$PROJECT_ROOT/lambda.zip"

# Clean previous build
rm -rf "$PACKAGE_DIR" "$ZIP_PATH"
mkdir -p "$PACKAGE_DIR"

# Install dependencies
pip install -r "$PROJECT_ROOT/requirements.txt" -t "$PACKAGE_DIR" -q

# Copy application code
for f in main.py auth.py database.py db_models.py models.py repository.py schemas.py service.py lambda_handler.py; do
  cp "$PROJECT_ROOT/$f" "$PACKAGE_DIR/"
done

# Create zip
cd "$PACKAGE_DIR" && zip -rq "$ZIP_PATH" . && cd - > /dev/null

# Cleanup
rm -rf "$PACKAGE_DIR"

echo "Built lambda.zip at $ZIP_PATH"
