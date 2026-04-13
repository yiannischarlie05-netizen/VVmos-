#!/usr/bin/env bash
# VMOS-Titan Launcher for current installation

TITAN_DIR="/home/debian/Downloads/vmos-titan-unified"
VENV_DIR="${TITAN_DIR}/.venv"
PYTHON="${VENV_DIR}/bin/python3"
API_PORT=8000

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

case "${1:-help}" in
    start)
        echo -e "${BLUE}Starting VMOS-Titan API server...${NC}"
        cd "$TITAN_DIR"
        export PYTHONPATH="${TITAN_DIR}/vmos_titan:${TITAN_DIR}/server"
        "$VENV_DIR/bin/python" -m uvicorn vmos_titan.api.main:app \
            --host 127.0.0.1 --port $API_PORT --reload &
        echo -e "${GREEN}✓ API server started on http://127.0.0.1:$API_PORT${NC}"
        echo "API docs: http://127.0.0.1:$API_PORT/docs"
        ;;
    
    status)
        echo "VMOS-Titan Status:"
        if pgrep -f "uvicorn.*vmos_titan" > /dev/null; then
            echo -e "${GREEN}✓ API server running${NC}"
        else
            echo -e "✗ API server stopped"
        fi
        ;;
    
    stop)
        echo "Stopping VMOS-Titan..."
        pkill -f "uvicorn.*vmos_titan" || true
        echo -e "${GREEN}✓ Stopped${NC}"
        ;;
    
    console)
        echo "Opening VMOS Cloud Device Scanner..."
        cd "$TITAN_DIR"
        "$PYTHON" vmos_cloud_device_scanner.py
        ;;
    
    genesis)
        echo "Starting Genesis pipeline..."
        cd "$TITAN_DIR"
        "$PYTHON" genesis_full_pipeline.py
        ;;
    
    config)
        echo "VMOS-Titan Configuration:"
        echo "  Base Dir: $TITAN_DIR"
        echo "  Venv:     $VENV_DIR"
        echo "  Python:   $($PYTHON --version)"
        echo "  Config:   $HOME/.vmos_titan"
        ;;
    
    help|*)
        echo "VMOS-Titan Launcher"
        echo ""
        echo "Usage: $0 <command>"
        echo ""
        echo "Commands:"
        echo "  start    Start API server"
        echo "  stop     Stop API server"
        echo "  status   Check status"
        echo "  console  Launch VMOS Cloud Device Scanner"
        echo "  genesis  Run Genesis pipeline"
        echo "  config   Show configuration"
        echo "  help     Show this help"
        ;;
esac
