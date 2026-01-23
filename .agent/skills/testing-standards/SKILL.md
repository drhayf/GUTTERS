---
name: testing-standards
description: Testing standards for GUTTERS. Use when writing tests for modules, calculations, or integrations. Ensures 80%+ coverage with validated test data.
---

# Testing Standards

Pytest async testing for GUTTERS. All calculations tested against known data, 80% minimum coverage.

## Test Structure
```
tests/
├── conftest.py              # Shared fixtures
├── test_active_memory.py    # Core systems
├── test_synthesis.py
└── modules/
    ├── test_astrology.py
    └── test_numerology.py
```

## Required Test Types

**1. Initialization Test**
```python
@pytest.mark.asyncio
async def test_module_initializes():
    module = AstrologyModule()
    await module.initialize()
    
    assert module.initialized == True
    assert module.config is not None
```

**2. Calculation Against Known Data**
```python
@pytest.mark.asyncio
async def test_natal_chart_steve_jobs():
    """Test against verified birth chart."""
    # Steve Jobs: Feb 24, 1955, 7:15 PM PST, San Francisco
    chart = await calculate_natal_chart(
        datetime(1955, 2, 24, 19, 15, tzinfo=ZoneInfo("America/Los_Angeles")),
        lat=37.7749,
        lon=-122.4194
    )
    
    # Known placements (verified against astro.com)
    assert chart.sun.sign == "Pisces"
    assert abs(chart.sun.degree - 5.5) < 1.0
    assert chart.rising_sign == "Virgo"
```

**3. Synthesis Contribution**
```python
@pytest.mark.asyncio
async def test_synthesis_contribution():
    module = AstrologyModule()
    contribution = await module.contribute_to_synthesis(user_id)
    
    assert contribution["module"] == "astrology"
    assert "data" in contribution
    assert "insights" in contribution
    assert len(contribution["insights"]) > 0
```

**4. Edge Cases**
```python
@pytest.mark.asyncio
async def test_invalid_birth_date_raises_error():
    with pytest.raises(ValidationError):
        await calculate_natal_chart(
            datetime(1800, 1, 1),  # Before ephemeris range
            lat=0, lon=0
        )
```

## Fixtures (conftest.py)
```python
@pytest.fixture
def mock_db():
    """Mock database session."""
    return Mock(spec=AsyncSession)

@pytest.fixture
def sample_user_data():
    """Sample birth data."""
    return {
        "name": "Test User",
        "birth_date": datetime(1990, 1, 1, 12, 0),
        "birth_location": {"lat": 40.7128, "lon": -74.0060}
    }
```

## Coverage Requirements
```bash
# Run with coverage
uv run pytest --cov=app --cov-report=html tests/

# Minimum 80% overall
# 100% for calculation functions
```

## Validation Data Sources

- astro.com - Verified natal charts
- Human Design official calculators
- Known numerology examples

## Critical Rules

- Test against KNOWN/VERIFIED data (not random)
- Mock external APIs (NOAA, ephemeris lookups)
- Test edge cases (invalid input, missing data)
- NO test should depend on another test
- Tests must be deterministic (same input = same output)