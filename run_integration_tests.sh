#!/bin/bash

echo "=========================================="
echo "GUTTERS End-to-End Integration Tests"
echo "=========================================="

# Run integration tests
pytest tests/integration/test_end_to_end.py -v -s --tb=short

# Check exit code
if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✅ ALL INTEGRATION TESTS PASSED"
    echo "=========================================="
    echo "Backend is verified and ready for frontend development."
    exit 0
else
    echo ""
    echo "=========================================="
    echo "❌ INTEGRATION TESTS FAILED"
    echo "=========================================="
    echo "Review errors above and fix before proceeding to frontend."
    exit 1
fi
