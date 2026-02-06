"""
Vector search engine using pgvector.

Performs semantic similarity search across embeddings.
"""

import logging
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.models.embedding import Embedding

logger = logging.getLogger(__name__)

class VectorSearchEngine:
    """Semantic search using pgvector."""

    async def search(
        self,
        user_id: int,
        query_embedding: List[float],
        db: AsyncSession,
        limit: int = 5,
        metadata_filter: Optional[Dict[str, Any]] = None,
        similarity_threshold: float = 0.3 # Lowered for better discovery
    ) -> List[Dict[str, Any]]:
        """
        Search for semantically similar content.

        Args:
            user_id: User ID
            query_embedding: Embedding vector for query
            db: Database session
            limit: Max results
            metadata_filter: JSONB filter (e.g., {"type": "journal_entry"})
            similarity_threshold: Minimum cosine similarity (0-1)

        Returns:
            List of results with content, metadata, and similarity score
        """
        # build the search query
        # pgvector uses cosine_distance, so similarity is 1 - distance
        similarity_expr = (1 - Embedding.embedding.cosine_distance(query_embedding)).label('similarity')

        stmt = select(
            Embedding.id,
            Embedding.content,
            Embedding.content_metadata,
            Embedding.created_at,
            similarity_expr
        ).where(
            Embedding.user_id == user_id
        )

        # Apply metadata filter (JSONB queries)
        if metadata_filter:
            for key, value in metadata_filter.items():
                # JSONB containment query
                stmt = stmt.where(
                    Embedding.content_metadata[key].astext == str(value)
                )

        # Order by similarity and limit
        stmt = stmt.order_by(similarity_expr.desc()).limit(limit * 2) # Get more to filter by threshold

        result = await db.execute(stmt)
        rows = result.all()

        # Filter by similarity threshold
        results = []
        for row in rows:
            similarity = float(row.similarity)
            if similarity >= similarity_threshold:
                results.append({
                    "id": row.id,
                    "content": row.content,
                    "metadata": row.content_metadata,
                    "created_at": row.created_at.isoformat(),
                    "similarity": similarity
                })

            if len(results) >= limit:
                break

        return results

    async def hybrid_search(
        self,
        user_id: int,
        query_embedding: List[float],
        db: AsyncSession,
        limit: int = 10
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Comprehensive search across all content types.

        Returns:
            {
                "journal_entries": [...],
                "patterns": [...],
                "syntheses": [...]
            }
        """
        # Search all content
        all_results = await self.search(
            user_id,
            query_embedding,
            db,
            limit=limit + 5, # Buffer for sorting
            similarity_threshold=0.25  # Much lower for hybrid coverage
        )

        # Group by type
        grouped = {
            "journal_entries": [],
            "patterns": [],
            "syntheses": []
        }

        for result in all_results:
            content_type = result['metadata'].get('type')

            if content_type == 'journal_entry':
                grouped['journal_entries'].append(result)
            elif content_type in ['observer_finding', 'hypothesis']:
                grouped['patterns'].append(result)
            elif content_type in ['module_synthesis', 'master_synthesis']:
                grouped['syntheses'].append(result)

        # Limit individual categories
        grouped['journal_entries'] = grouped['journal_entries'][:3]
        grouped['patterns'] = grouped['patterns'][:3]
        grouped['syntheses'] = grouped['syntheses'][:2]

        return grouped
