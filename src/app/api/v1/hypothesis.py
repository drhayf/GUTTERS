from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated, Optional, List

from ...api.dependencies import get_current_user
from ...models.user import User
from ...modules.intelligence.hypothesis.models import Hypothesis
from ...modules.intelligence.hypothesis.storage import HypothesisStorage
from ...modules.intelligence.hypothesis.generator import HypothesisGenerator
from ...modules.intelligence.observer.storage import ObserverFindingStorage
from ...core.db.database import async_get_db
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/hypothesis", tags=["hypothesis"])

@router.get("/list")
async def get_hypotheses(
    current_user: Annotated[User, Depends(get_current_user)],
    min_confidence: float = 0.0,
    status: Optional[str] = None
):
    """Get all theory hypotheses for current user."""
    storage = HypothesisStorage()
    hypotheses = await storage.get_hypotheses(
        current_user.id,
        min_confidence=min_confidence,
        status=status
    )
    
    return {
        "user_id": current_user.id,
        "hypotheses": [h.model_dump(mode='json') for h in hypotheses],
        "total": len(hypotheses)
    }

@router.post("/generate")
async def generate_hypotheses(
    current_user: Annotated[User, Depends(get_current_user)],
    db: AsyncSession = Depends(async_get_db)
):
    """
    Generate theory hypotheses from Observer patterns.
    
    Triggered manually to refresh theories.
    """
    from src.app.modules.intelligence.synthesis.synthesizer import DEFAULT_MODEL
    from src.app.core.ai.llm_factory import get_llm
    
    # Initialize components
    llm = get_llm(DEFAULT_MODEL)
    generator = HypothesisGenerator(llm)
    storage = HypothesisStorage()
    observer_storage = ObserverFindingStorage()
    
    # 1. Get Observer patterns
    patterns = await observer_storage.get_findings(current_user.id, min_confidence=0.7)
    
    if not patterns:
        return {
            "status": "skipped",
            "message": "No patterns available with sufficient confidence (min 0.7)",
            "generated": 0
        }
    
    # 2. Generate hypotheses
    hypotheses = await generator.generate_from_patterns(current_user.id, patterns)
    
    # 3. Store
    for h in hypotheses:
        await storage.store_hypothesis(h, db)
    
    # 4. Update StateTracker
    from src.app.core.state.tracker import get_state_tracker
    tracker = get_state_tracker()
    await tracker.update_hypothesis_status(current_user.id, db)
    
    return {
        "status": "complete",
        "generated": len(hypotheses),
        "hypotheses": [h.model_dump(mode='json') for h in hypotheses]
    }

@router.get("/confirmed")
async def get_confirmed_hypotheses(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Get only confirmed theories (confidence > 0.85)."""
    storage = HypothesisStorage()
    confirmed = await storage.get_confirmed_hypotheses(current_user.id)
    
    return {
        "user_id": current_user.id,
        "confirmed_hypotheses": [h.model_dump(mode='json') for h in confirmed],
        "total": len(confirmed)
    }
