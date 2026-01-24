from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
import json

class ObserverFindingStorage:
    """
    Store and retrieve Observer findings.
    
    Findings stored in:
    - UserProfile.data['observer_findings']
    - Redis cache for fast access
    """
    
    async def store_finding(
        self,
        user_id: int,
        finding: Dict[str, Any],
        db: AsyncSession
    ) -> None:
        """Store a new finding."""
        from src.app.models.user_profile import UserProfile
        from sqlalchemy.orm.attributes import flag_modified
        
        result = await db.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile = result.scalar_one_or_none()
        
        if not profile:
            return
        
        if 'observer_findings' not in profile.data:
            profile.data['observer_findings'] = []
        
        # Check if finding already exists (deduplicate based on finding text and type)
        # Or just append. User code appended.
        # Ideally we deduplicate recent duplicates.
        
        profile.data['observer_findings'].append(finding)
        
        # Keep last 100 findings
        profile.data['observer_findings'] = profile.data['observer_findings'][-100:]
        
        flag_modified(profile, "data")
        await db.commit()
        
        # Cache in Redis
        from src.app.core.memory import get_active_memory
        memory = get_active_memory()
        await memory.initialize()
        
        await memory.set(
            f"observer:findings:{user_id}",
            profile.data['observer_findings'],
            ttl=604800  # 7 days
        )
    
    async def get_findings(
        self,
        user_id: int,
        min_confidence: float = 0.6
    ) -> List[Dict[str, Any]]:
        """Get findings above confidence threshold."""
        from src.app.core.memory import get_active_memory
        memory = get_active_memory()
        await memory.initialize()
        
        # Try Redis first
        cached = await memory.get(f"observer:findings:{user_id}")
        if cached:
            return [f for f in cached if f.get('confidence', 0) >= min_confidence]
        
        
        # Fallback to database
        from src.app.core.db.database import async_get_db
        from src.app.models.user_profile import UserProfile
        
        async for db in async_get_db():
            result = await db.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            profile = result.scalar_one_or_none()
            
            if profile and 'observer_findings' in profile.data:
                findings = profile.data['observer_findings']
                
                # Cache
                await memory.set(
                    f"observer:findings:{user_id}",
                    findings,
                    ttl=604800
                )
                
                return [f for f in findings if f.get('confidence', 0) >= min_confidence]
        
        return []
