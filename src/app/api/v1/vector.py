from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.api.dependencies import get_current_user
from src.app.core.config import settings
from src.app.core.db.database import async_get_db
from src.app.modules.intelligence.vector.embedding_service import EmbeddingService
from src.app.modules.intelligence.vector.search_engine import VectorSearchEngine

router = APIRouter(prefix="/vector", tags=["vector"])

@router.post("/search")
async def semantic_search(
    query: Annotated[str, Query(..., description="Semantic search query")],
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)],
    limit: int = 5
):
    """
    Perform a semantic search across all your cosmic profile data,
    including journal entries, patterns, and syntheses.
    """
    service = EmbeddingService(settings.OPENROUTER_API_KEY.get_secret_value())
    engine = VectorSearchEngine()

    try:
        # Embed query
        query_embedding = await service.embed_text(query)

        # Search
        results = await engine.search(
            current_user["id"],
            query_embedding,
            db,
            limit=limit
        )

        return {
            "query": query,
            "results": results,
            "total": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.post("/populate")
async def populate_embeddings(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)]
):
    """
    Manually trigger embedding population for your current profile data.
    Useful for immediately indexing new journal entries.
    """
    from sqlalchemy import select

    from src.app.models.embedding import Embedding
    from src.app.models.user_profile import UserProfile

    service = EmbeddingService(settings.OPENROUTER_API_KEY.get_secret_value())

    # Get user profile
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == current_user["id"])
    )
    profile = result.scalar_one_or_none()

    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    embeddings_created = 0

    # Define task for each content type
    async def process_content(items, type_key, id_key, embed_func):
        nonlocal embeddings_created
        for item in items:
            item_id = item.get(id_key)
            if not item_id:
                continue

            # Check if exists
            exists_stmt = select(Embedding).where(
                Embedding.user_id == current_user["id"],
                Embedding.content_metadata[type_key].astext == str(item_id)
            )
            exists_result = await db.execute(exists_stmt)
            if exists_result.scalar_one_or_none():
                continue

            embedded = await embed_func(item)
            db.add(Embedding(
                user_id=current_user.id,
                content=embedded['content'],
                embedding=embedded['embedding'],
                content_metadata=embedded['content_metadata']
            ))
            embeddings_created += 1

    try:
        # 1. Journal Entries
        await process_content(
            profile.data.get('journal_entries', []),
            'entry_id', 'id', service.embed_journal_entry
        )

        # 2. Observer Findings
        await process_content(
            profile.data.get('observer_findings', []),
            'finding_id', 'id', service.embed_observer_finding
        )

        # 3. Hypotheses
        await process_content(
            profile.data.get('hypotheses', []),
            'hypothesis_id', 'id', service.embed_hypothesis
        )

        if embeddings_created > 0:
            await db.commit()

        return {
            "status": "complete",
            "embeddings_created": embeddings_created
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Population failed: {str(e)}")
