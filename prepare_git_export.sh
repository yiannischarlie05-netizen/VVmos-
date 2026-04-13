#!/bin/bash
set -e

SOURCE_DIR=$(pwd)
TARGET_DIR=$(realpath ../vmos-titan-git-export)

echo "Creating clean export directory at $TARGET_DIR..."
rm -rf "$TARGET_DIR"
mkdir -p "$TARGET_DIR"

# Copy files, excluding typical bloated/generated directories
echo "Copying files..."
rsync -av \
    --exclude='.venv' \
    --exclude='__pycache__' \
    --exclude='.git' \
    --exclude='*.pyc' \
    --exclude='*.log' \
    --exclude='*.json' \
    --exclude='.vscode' \
    --exclude='output' \
    --exclude='reports' \
    --exclude='tmp' \
    --exclude='yolov8n.pt' \
    --exclude='.pytest_cache' \
    "$SOURCE_DIR/" "$TARGET_DIR/"

cd "$TARGET_DIR"

# Create a standard .gitignore
echo "Creating .gitignore..."
cat << 'IGN' > .gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Logs and databases
*.log
*.sqlite
*.sqlite3

# OS generated files
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db
IGN

# Initialize git repository
echo "Initializing git repository..."
git init
git add .
git commit -m "Initial commit of cleaned, restructured codebase"

echo "Done! The git-ready codebase is located at: $TARGET_DIR"
