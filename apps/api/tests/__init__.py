"""
Project Sovereign Integration Test Suite

This package contains comprehensive integration tests that validate
the actual live functionality of the system. These are NOT unit tests -
they exercise real code paths, real data flows, and real integrations.

Test Categories:
================
1. Domain Architecture Tests - Validate domain hierarchy and registration
2. Trait System Tests - Validate trait storage, retrieval, and updates
3. Agent Integration Tests - Validate agent communication and routing
4. Module Bridge Tests - Validate frontend/backend module mappings
5. End-to-End Flow Tests - Full user journey validation

Running Tests:
==============
From the apps/api directory:
    python -m pytest tests/ -v
    
Or individual test files:
    python -m pytest tests/test_integration_domains.py -v

For live system tests (requires running server):
    python -m pytest tests/test_live_api.py -v
"""
