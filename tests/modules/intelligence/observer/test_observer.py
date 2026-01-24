import pytest
from datetime import datetime, timedelta, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.app.models.user import User
from src.app.models.user_profile import UserProfile
from src.app.modules.intelligence.observer.observer import Observer
from src.app.modules.intelligence.observer.storage import ObserverFindingStorage

@pytest.mark.asyncio
async def test_solar_correlation_detection(db: AsyncSession, test_user: User):
    """Test detection of solar correlations with seeded data."""
    # 1. Setup Observer
    observer = Observer()
    
    # 2. Seed UserProfile with tracking history and journal entries
    # We create a pattern: High Kp (>5) aligns with "headache"
    
    history = []
    journal = []
    
    # Seed 60 days to be safe, ending TODAY
    end_date = datetime.now(timezone.utc)
    start_date = end_date - timedelta(days=60)
    
    for i in range(61):
        ts = start_date + timedelta(days=i)
        ts_iso = ts.isoformat().replace('+00:00', 'Z')
        if not ts_iso.endswith('Z'):
            ts_iso += 'Z'
        
        # Every 3rd day is a storm (Kp=6) and user has headache
        is_storm = (i % 3 == 0)
        kp = 6.0 if is_storm else 2.0
        
        history.append({
            "timestamp": ts_iso,
            "data": {
                "kp_index": kp,
                "geomagnetic_storm": is_storm
            }
        })
        
        if is_storm:
            journal.append({
                "timestamp": ts_iso,
                "text": "I have a terrible headache today.",
                "mood_score": 3
            })
        else:
            journal.append({
                "timestamp": ts_iso,
                "text": "Feeling fine.",
                "mood_score": 7
            })
            
    # Update profile
    stmt = select(UserProfile).where(UserProfile.user_id == test_user.id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    
    if not profile:
        profile = UserProfile(user_id=test_user.id, data={})
        db.add(profile)
    
    if not profile.data:
        profile.data = {}
        
    profile.data['tracking_history'] = {
        'solar_tracking': history
    }
    profile.data['journal_entries'] = journal
    profile.data['preferences'] = {'observer_enabled': True}
    
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(profile, "data")
    await db.commit()
    
    # 3. Run detection
    findings = await observer.detect_solar_correlations(test_user.id, db)
    
    # 4. Verify
    assert len(findings) > 0
    finding = findings[0]
    assert finding['pattern_type'] == 'solar_symptom'
    assert finding['symptom'] == 'headache'
    assert finding['correlation'] > 0.8 
    assert finding['confidence'] > 0.6

@pytest.mark.asyncio
async def test_observer_storage(db: AsyncSession, test_user: User):
    """Test finding persistence."""
    storage = ObserverFindingStorage()
    
    finding = {
        "pattern_type": "test_pattern",
        "finding": "Test finding",
        "confidence": 0.9,
        "detected_at": datetime.now(timezone.utc).isoformat()
    }
    
    await storage.store_finding(test_user.id, finding, db)
    
    # Retrieve
    stored = await storage.get_findings(test_user.id, min_confidence=0.5)
    
    assert len(stored) >= 1
    assert stored[-1]['pattern_type'] == 'test_pattern'
    
@pytest.mark.asyncio
async def test_observer_preferences(db: AsyncSession, test_user: User):
    """Test observer respects user preference."""
    observer = Observer()
    
    # Get profile
    stmt = select(UserProfile).where(UserProfile.user_id == test_user.id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    
    if not profile:
        profile = UserProfile(user_id=test_user.id, data={})
        db.add(profile)
    
    # Seed some data so it would normally find something
    start_date = datetime.now(timezone.utc) - timedelta(days=5)
    ts_iso = start_date.isoformat().replace('+00:00', 'Z')
    if not ts_iso.endswith('Z'):
        ts_iso += 'Z'
    
    if not profile.data:
        profile.data = {}
        
    profile.data['tracking_history'] = {
        'solar_tracking': [{
            "timestamp": ts_iso,
            "data": {"kp_index": 6.0}
        }]
    }
    profile.data['journal_entries'] = [{
        "timestamp": ts_iso,
        "text": "Headache",
        "mood_score": 3
    }]
    
    # Disable observer
    profile.data['preferences'] = {'observer_enabled': False}
    from sqlalchemy.orm.attributes import flag_modified
    flag_modified(profile, "data")
    await db.commit()
    
    # Invalidate cache
    from src.app.core.memory import get_active_memory
    memory = get_active_memory()
    await memory.initialize()
    await memory.delete(f"memory:warm:preferences:{test_user.id}")
    
    # Run detection (should return empty even with data)
    findings = await observer.detect_solar_correlations(test_user.id, db)
    assert len(findings) == 0
