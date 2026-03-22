#!/bin/bash
# Run the full signal pipeline
set -e

echo "=== Polymarket Signal Agent Pipeline ==="
echo ""

# Activate venv if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run pipeline
python -m engine.main "$@"

echo ""
echo "=== Pipeline Complete ==="
