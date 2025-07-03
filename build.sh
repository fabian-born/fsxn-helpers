#!/bin/bash
set -euo pipefail

echo "📦 Starting build process..."

# Get version from Git tag (e.g. v1.2.3)
VERSION=$(git describe --tags)
echo "📌 Release version: $VERSION"

# Prepare output directory
DIST_DIR="dist"
rm -rf "$DIST_DIR"
mkdir -p "$DIST_DIR"

# Write version to file
echo "$VERSION" > "$DIST_DIR/version.txt"

# Example: Create build content
echo "🔧 Creating sample files..."
mkdir -p build_temp
echo "This is version $VERSION" > build_temp/README.txt

# Create ZIP archive
ZIP_NAME="example-${VERSION}.zip"
echo "📁 Creating ZIP archive: $ZIP_NAME"
zip -r "$DIST_DIR/$ZIP_NAME" build_temp "$DIST_DIR/version.txt"

# Clean up temp files
rm -rf build_temp

echo "✅ Build complete. Artifacts saved to $DIST_DIR/"