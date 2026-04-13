#!/usr/bin/env bash
set -euo pipefail

OUTDIR="copilot_support_bundle_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$OUTDIR"
echo "Collecting Copilot support bundle into: $OUTDIR"

# 1) VS Code info
if command -v code >/dev/null 2>&1; then
  code --version > "$OUTDIR/code_version.txt" 2>&1 || true
  code --list-extensions --show-versions > "$OUTDIR/extensions.txt" 2>&1 || true
else
  echo "code not found" > "$OUTDIR/code_version.txt"
  echo "code not found" > "$OUTDIR/extensions.txt"
fi

# 2) GitHub CLI auth status (if installed)
if command -v gh >/dev/null 2>&1; then
  gh auth status > "$OUTDIR/gh_auth_status.txt" 2>&1 || true
else
  echo "gh not found" > "$OUTDIR/gh_auth_status.txt"
fi

# 3) OS info
if [ -f /etc/os-release ]; then
  cat /etc/os-release > "$OUTDIR/os_release.txt" 2>&1 || true
fi

# 4) Workspace VS Code settings
if [ -f .vscode/settings.json ]; then
  mkdir -p "$OUTDIR/workspace_vscode"
  cp .vscode/settings.json "$OUTDIR/workspace_vscode/settings.json" || true
fi

# 5) Collect recent VS Code logs (if present)
VSCODE_LOG_DIR="$HOME/.config/Code/logs"
if [ -d "$VSCODE_LOG_DIR" ]; then
  mkdir -p "$OUTDIR/vscode_logs"
  ls -1t "$VSCODE_LOG_DIR" | head -n 3 | while read -r d; do
    cp -r "$VSCODE_LOG_DIR/$d" "$OUTDIR/vscode_logs/" 2>/dev/null || true
  done
else
  echo "no vscode logs at $VSCODE_LOG_DIR" > "$OUTDIR/vscode_logs.README"
fi

# 6) Try to capture Copilot extension globalStorage
GS="$HOME/.config/Code/User/globalStorage"
mkdir -p "$OUTDIR/globalStorage" 2>/dev/null || true
if [ -d "$GS" ]; then
  for candidate in "$GS/github.copilot-chat" "$GS/github.copilot" "$GS/github.copilot*"; do
    if ls $candidate >/dev/null 2>&1; then
      cp -r $candidate "$OUTDIR/globalStorage/" 2>/dev/null || true
    fi
  done
else
  echo "no globalStorage dir at $GS" > "$OUTDIR/globalStorage.README"
fi

# 7) Copy copilot cache (if used)
if [ -d "/tmp/copilot_cache" ]; then
  mkdir -p "$OUTDIR/copilot_cache"
  find /tmp/copilot_cache -maxdepth 2 -type f -exec cp {} "$OUTDIR/copilot_cache/" \; || true
else
  echo "no /tmp/copilot_cache found" > "$OUTDIR/copilot_cache.README"
fi

# 8) Process and proxy checks
ps aux | grep -i mitmproxy | grep -v grep > "$OUTDIR/mitmproxy_ps.txt" 2>&1 || true
env | grep -i proxy > "$OUTDIR/proxy_env.txt" 2>&1 || true

# 9) README with manual instructions
cat > "$OUTDIR/README.txt" <<'EOF'
Manual steps to complete the bundle:
- In VS Code: View -> Output -> select "GitHub Copilot" -> copy & save as copilot_output.txt into this folder.
- In VS Code: Help -> Toggle Developer Tools -> Console -> filter 'copilot' -> copy & save as devtools_console.txt into this folder.
- Include screenshots of any error dialogs if available.
EOF

# 10) Archive
tar -czf "${OUTDIR}.tar.gz" "$OUTDIR" || true
echo "Bundle created: ${OUTDIR}.tar.gz"
echo "If copilot_output.txt or devtools_console.txt are missing, open VS Code and save them into the bundle folder, then re-run the script or re-tar the folder."
