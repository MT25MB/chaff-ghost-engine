#!/bin/bash
echo "=========================================="
echo "  CHAFF Ghost Engine - Dry Run Test"
echo "=========================================="
echo
echo "Generating ghost profile and simulating one cycle..."
echo "Nothing will be posted to Reddit."
echo
python3 ghost_engine.py --dry-run --profiles-only
echo
echo "Running simulated cycle..."
python3 ghost_engine.py --dry-run --run-once
