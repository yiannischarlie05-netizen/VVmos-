#!/bin/bash
# TITAN CCTV v2 — Launcher
# Usage:
#   ./cctv_launcher.sh dashboard           # Start web dashboard on :7700
#   ./cctv_launcher.sh scan [args]          # CLI scan
#   ./cctv_launcher.sh record [args]        # Record from results
#   ./cctv_launcher.sh monitor [args]       # Continuous monitoring loop
#   ./cctv_launcher.sh countries            # List all supported countries
#   ./cctv_launcher.sh regions              # List region presets

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
VENV_DIR="$(dirname "$SCRIPT_DIR")/.venv"
export PYTHONPATH="$SCRIPT_DIR:$PYTHONPATH"

# activate venv if exists
if [ -f "$VENV_DIR/bin/activate" ]; then
    source "$VENV_DIR/bin/activate"
fi

cd "$SCRIPT_DIR"

case "${1:-help}" in
    dashboard|dash|server)
        shift
        echo "═══════════════════════════════════════════"
        echo "  TITAN CCTV v2 — Dashboard Server"
        echo "  http://0.0.0.0:${PORT:-7700}"
        echo "═══════════════════════════════════════════"
        python3 cctv_server.py "$@"
        ;;
    scan)
        shift
        python3 titan_cctv.py scan "$@"
        ;;
    probe)
        shift
        python3 titan_cctv.py probe "$@"
        ;;
    yolo)
        shift
        python3 titan_cctv.py yolo "$@"
        ;;
    record)
        shift
        python3 cctv_recorder.py record "$@"
        ;;
    snapshot)
        shift
        python3 cctv_recorder.py snapshot "$@"
        ;;
    monitor)
        shift
        python3 cctv_recorder.py monitor "$@"
        ;;
    countries|list-countries)
        python3 titan_cctv.py list-countries
        ;;
    regions|list-regions)
        python3 titan_cctv.py list-regions
        ;;
    help|--help|-h|*)
        echo ""
        echo "  TITAN CCTV v2 — Global Camera Scanner + YOLO Detection"
        echo ""
        echo "  USAGE:"
        echo "    $0 dashboard [--port 7700]                          Start web dashboard"
        echo "    $0 scan --countries 'India,Thailand' --max-cams 100 Scan specific countries"
        echo "    $0 scan --region south-asia --max-cams 200          Scan by region preset"
        echo "    $0 scan --countries all --max-cams 500              Scan ALL countries"
        echo "    $0 scan --cidrs '1.2.3.0/24,5.6.0.0/16'            Custom CIDRs"
        echo "    $0 probe --ip 112.134.55.10                         Probe single IP"
        echo "    $0 yolo --image /path/to/frame.jpg                  YOLO detection"
        echo "    $0 record --input 'results/scan_*.json' --duration 60"
        echo "    $0 snapshot --input 'results/scan_*.json'"
        echo "    $0 monitor --input 'results/scan_*.json' --interval 300 --alert-on bedroom"
        echo "    $0 countries                                        List 55+ countries"
        echo "    $0 regions                                          List region presets"
        echo ""
        ;;
esac
