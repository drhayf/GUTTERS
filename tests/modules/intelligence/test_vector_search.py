"""
High-fidelity integration tests for Vector Search.

Uses real PostgreSQL + pgvector + OpenRouter API.
"""

import logging

import pytest
from sqlalchemy import func, select

from src.app.core.config import settings
from src.app.models.embedding import Embedding
from src.app.models.user_profile import UserProfile
from src.app.modules.intelligence.vector.embedding_service import EmbeddingService
from src.app.modules.intelligence.vector.search_engine import VectorSearchEngine

logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_embed_journal_entry(seeded_user, db):
    """Test embedding generation for journal entry via OpenRouter."""
    service = EmbeddingService(settings.OPENROUTER_API_KEY.get_secret_value())

    # Get seeded journal entry
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == seeded_user)
    )
    profile = result.scalar_one()

    entry = profile.data['journal_entries'][0]

    # Generate embedding
    embedded = await service.embed_journal_entry(entry)

    # Verify structure
    assert 'content' in embedded
    assert 'embedding' in embedded
    assert 'content_metadata' in embedded

    # Verify embedding is correct dimension
    assert len(embedded['embedding']) == 1536  # OpenAI text-embedding-3-small

    # Verify metadata
    assert embedded['content_metadata']['type'] == 'journal_entry'
    assert embedded['content_metadata']['entry_id'] == entry['id']

@pytest.mark.asyncio
async def test_vector_search_finds_relevant_content(seeded_user, db):
    """
    Test vector search finds semantically similar content.

    Verification:
    - Embed seeded journal entries
    - Search for a topic known to be in the seed data
    - Should find relevant entries
    """
    service = EmbeddingService(settings.OPENROUTER_API_KEY.get_secret_value())
    engine = VectorSearchEngine()

    # Get profile
    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == seeded_user)
    )
    profile = result.scalar_one()

    # Embed a few journal entries
    # The SeedDataGenerator creates realistic entries. Let's look for "headache" or "energy"
    # We'll embed 10 entries to have a good search pool
    for entry in profile.data['journal_entries'][:10]:
        embedded = await service.embed_journal_entry(entry)

        embedding_record = Embedding(
            user_id=seeded_user,
            content=embedded['content'],
            embedding=embedded['embedding'],
            content_metadata=embedded['content_metadata']
        )
        db.add(embedding_record)

    await db.commit()

    # VERIFY COUNT
    count_stmt = select(func.count(Embedding.id)).where(Embedding.user_id == seeded_user)
    count_res = await db.execute(count_stmt)
    assert count_res.scalar() >= 10, "Embeddings were not committed correctly"

    # Search for something general like "How's my mood and energy?"
    query = "Why do I get headaches?"
    query_embedding = await service.embed_text(query)

    results = await engine.search(
        seeded_user,
        query_embedding,
        db,
        limit=5,
        similarity_threshold=0.3 # VASTLY lower for noise testing
    )

    # Debug results
    for r in results:
        logger.info(f"DEBUG RELEVANCE: {r['similarity']:.2f} - {r['content'][:50]}...")

    # Verify results
    assert len(results) > 0, f"No results found for query: {query}"

    # Check that top result meets some common sense relevance
    top_result = results[0]
    assert top_result['similarity'] > 0.35
    logger.info(f"Top search result: {top_result['content']} (similarity: {top_result['similarity']})")

@pytest.mark.asyncio
async def test_hybrid_search(seeded_user, db):
    """
    Test hybrid search across all content types.
    """
    service = EmbeddingService(settings.OPENROUTER_API_KEY.get_secret_value())
    engine = VectorSearchEngine()

    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == seeded_user)
    )
    profile = result.scalar_one()

    # Embed different types
    # Journal
    for entry in profile.data['journal_entries'][:5]:
        embedded = await service.embed_journal_entry(entry)
        db.add(Embedding(
            user_id=seeded_user,
            content=embedded['content'],
            embedding=embedded['embedding'],
            content_metadata=embedded['content_metadata']
        ))

    # Observer findings
    for finding in profile.data['observer_findings'][:3]:
        embedded = await service.embed_observer_finding(finding)
        db.add(Embedding(
            user_id=seeded_user,
            content=embedded['content'],
            embedding=embedded['embedding'],
            content_metadata=embedded['content_metadata']
        ))

    await db.commit()

    # Hybrid search
    query = "patterns in my energy levels"
    query_embedding = await service.embed_text(query)

    grouped_results = await engine.hybrid_search(
        seeded_user,
        query_embedding,
        db,
        limit=10
    )

    # Verify grouping
    assert 'journal_entries' in grouped_results
    assert 'patterns' in grouped_results
    assert 'syntheses' in grouped_results

    # Should have found some results in categories we seeded
    assert len(grouped_results['journal_entries']) > 0
    assert len(grouped_results['patterns']) > 0

@pytest.mark.asyncio
async def test_query_with_vector_search(seeded_user, db, memory):
    """
    Test Query Engine with vector search enhancement.
    """
    from src.app.modules.intelligence.query.engine import QueryEngine
    from src.app.modules.intelligence.synthesis.synthesizer import DEFAULT_MODEL

    # Populate some embeddings first
    service = EmbeddingService(settings.OPENROUTER_API_KEY.get_secret_value())

    result = await db.execute(
        select(UserProfile).where(UserProfile.user_id == seeded_user)
    )
    profile = result.scalar_one()

    for entry in profile.data['journal_entries'][:5]:
        embedded = await service.embed_journal_entry(entry)
        db.add(Embedding(
            user_id=seeded_user,
            content=embedded['content'],
            embedding=embedded['embedding'],
            content_metadata=embedded['content_metadata']
        ))

    await db.commit()

    # Query
    engine = QueryEngine(model_id=DEFAULT_MODEL)

    response = await engine.answer_query(
        seeded_user,
        "Analyze the themes in my recent journal entries.",
        db,
        use_vector_search=True
    )

    # Verify response
    assert response.answer is not None
    assert len(response.answer) > 50
    # Note: We can't strictly verify if it used vector search in the response model
    # without adding a field, but we can verify it didn't crash.
    # The logs would show "Vector search found X entries".
