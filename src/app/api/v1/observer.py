from fastapi import APIRouter, Depends
from typing import Annotated, List, Dict, Any

from src.app.api.dependencies import get_current_user
from src.app.models.user import User
from src.app.core.db.database import async_get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/observer", tags=["observer"])

@router.get("/findings")
async def get_findings(
    current_user: Annotated[dict, Depends(get_current_user)],
    min_confidence: float = 0.6
):
    """Get Observer findings for current user."""
    from src.app.modules.intelligence.observer.storage import ObserverFindingStorage
    
    storage = ObserverFindingStorage()
    findings = await storage.get_findings(current_user["id"], min_confidence)
    
    return {
        "findings": findings,
        "total": len(findings)
    }

@router.post("/analyze")
async def trigger_analysis(
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """Manually trigger Observer analysis."""
    from src.app.modules.intelligence.observer.observer import Observer
    from src.app.modules.intelligence.observer.storage import ObserverFindingStorage
    
    observer = Observer()
    storage = ObserverFindingStorage()
    
    async for db in async_get_db():
        solar = await observer.detect_solar_correlations(current_user["id"], db)
        lunar = await observer.detect_lunar_correlations(current_user["id"], db)
        transits = await observer.detect_transit_correlations(current_user["id"], db)
        time_patterns = await observer.detect_time_based_patterns(current_user["id"], db)
        
        all_findings = solar + lunar + transits + time_patterns
        
        for finding in all_findings:
            await storage.store_finding(current_user["id"], finding, db)
        
        return {
            "status": "complete",
            "findings_detected": len(all_findings),
            "solar": len(solar),
            "lunar": len(lunar),
            "transits": len(transits),
            "time_patterns": len(time_patterns)
        }

@router.get("/questions")
async def get_questions(
    current_user: Annotated[dict, Depends(get_current_user)]
):
    """Get questions generated from findings."""
    from src.app.modules.intelligence.observer.observer import Observer
    from src.app.modules.intelligence.observer.storage import ObserverFindingStorage
    
    storage = ObserverFindingStorage()
    findings = await storage.get_findings(current_user["id"], min_confidence=0.7)
    
    observer = Observer()
    questions = observer.generate_questions(findings)
    
    return {
        "questions": questions,
        "based_on_findings": len(findings)
    }
