#!/bin/bash
# Quick venv activation script for Git Bash / WSL
echo "Activating GUTTERS virtual environment..."
source .venv/Scripts/activate
echo ""
echo "Virtual environment activated!"
echo "Python: $VIRTUAL_ENV/Scripts/python"
echo ""
echo "To deactivate, type: deactivate"
