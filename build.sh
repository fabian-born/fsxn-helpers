#!/bin/bash
# set -euo pipefail

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
echo "🔧 Creating files..."

# Aktuelles Verzeichnis merken
start_dir="$(pwd)"

# Listet alle Ordner im aktuellen Verzeichnis auf
echo "Gefundene Ordner:"

# Array zum Speichern der Ordnernamen
folders=()

# Schleife über alle Einträge im aktuellen Verzeichnis
for dir in */ ; do
    if [ -d "$dir" ]; then
        # Entferne den abschließenden Slash
        folder_name="${dir%/}"
        echo "$folder_name"
        folders+=("$folder_name")

        # Pfad zum Ordner
        folder_path="$start_dir/$folder_name"

        # Pfad zum Skript im Ordner
        script_path="$folder_path/build-release.sh"
        # Prüfen, ob das Skript existiert und ausführbar ist
        # if [ -x "$script_path" ]; then
        #    echo "→ Wechsle in $folder_name und führe run.sh aus"
        #    cd "$folder_path" || continue
        #    chmod a+x build-release.sh
	#    pwd
	#    cat $script_path
        #    cd "$start_dir" || exit 1
        #else
        #    echo "⚠️  Kein ausführbares Skript ($script_path) gefunden"
	#    cat $script_path
        # fi
	cd $folder_path
	chmod a+x build-release.sh
	./build-release.sh
	cd ..
    fi
done

echo ""
cd dist
for zips in *.zip ; do
   zip="${zips%.*}"
   ZIP_NAME="${zip}-${VERSION}.zip"
   echo "📁  Creating ZIP archive: $ZIP_NAME"
   mv $zips $ZIP_NAME
   zip -r "$ZIP_NAME" "version.txt"
   echo "${zips%.*}"
done 
# Create ZIP archive


# Clean up temp files
rm -rf build_temp

echo "✅ Build complete. Artifacts saved to $DIST_DIR/"
