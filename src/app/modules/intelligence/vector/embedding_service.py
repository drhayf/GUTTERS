"""
Embedding generation service.

Converts text to vectors using OpenAI's text-embedding-3-small model via OpenRouter.
"""

import logging
from datetime import UTC, datetime
from typing import Any, Dict, List

import openai

logger = logging.getLogger(__name__)

class EmbeddingService:
    """Generate embeddings using OpenAI via OpenRouter."""

    def __init__(self, api_key: str):
        self.client = openai.AsyncOpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        self.model = "openai/text-embedding-3-small"  # OpenRouter format

    async def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for single text.

        Args:
            text: Text to embed

        Returns:
            List of 1536 floats (embedding vector)
        """
        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (batch).

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors
        """
        if not texts:
            return []

        try:
            response = await self.client.embeddings.create(
                model=self.model,
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            raise

    async def embed_journal_entry(self, entry: Dict[str, Any]) -> Dict[str, Any]:
        """
        Embed journal entry with metadata.

        Args:
            entry: Journal entry dict

        Returns:
            {
                "content": "formatted text",
                "embedding": [vector],
                "content_metadata": {...}
            }
        """
        # Format content for embedding
        content = f"""Journal Entry ({entry.get('timestamp')}):
{entry.get('text', '')}

Mood: {entry.get('mood_score', 'N/A')}/10
Energy: {entry.get('energy_score', 'N/A')}/10
Tags: {', '.join(entry.get('tags', []))}"""

        # Generate embedding
        embedding = await self.embed_text(content)

        # Build metadata
        metadata = {
            "type": "journal_entry",
            "entry_id": entry.get('id'),
            "timestamp": entry.get('timestamp'),
            "mood_score": entry.get('mood_score'),
            "energy_score": entry.get('energy_score'),
            "tags": entry.get('tags', []),
            "themes": entry.get('themes', []),
            "lunar_phase": entry.get('lunar_phase'),
            "kp_index": entry.get('kp_index')
        }

        return {
            "content": content,
            "embedding": embedding,
            "content_metadata": metadata
        }

    async def embed_observer_finding(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """Embed Observer finding."""
        content = f"""Detected Pattern:
{finding.get('finding', '')}

Type: {finding.get('pattern_type', 'unknown')}
Confidence: {finding.get('confidence', 0):.0%}
Data Points: {finding.get('data_points', 0)}"""

        embedding = await self.embed_text(content)

        metadata = {
            "type": "observer_finding",
            "finding_id": finding.get('id', 'unknown'),
            "pattern_type": finding.get('pattern_type'),
            "confidence": finding.get('confidence'),
            "data_points": finding.get('data_points'),
            "detected_at": finding.get('detected_at')
        }

        return {
            "content": content,
            "embedding": embedding,
            "content_metadata": metadata
        }

    async def embed_hypothesis(self, hypothesis: Dict[str, Any]) -> Dict[str, Any]:
        """Embed Hypothesis claim."""
        content = f"""Theory:
{hypothesis.get('claim', '')}

Predicted Value: {hypothesis.get('predicted_value', 'N/A')}
Confidence: {hypothesis.get('confidence', 0):.0%}
Status: {hypothesis.get('status', 'unknown')}
Evidence Count: {hypothesis.get('evidence_count', 0)}"""

        embedding = await self.embed_text(content)

        metadata = {
            "type": "hypothesis",
            "hypothesis_id": hypothesis.get('id'),
            "hypothesis_type": hypothesis.get('hypothesis_type'),
            "confidence": hypothesis.get('confidence'),
            "status": hypothesis.get('status'),
            "evidence_count": hypothesis.get('evidence_count')
        }

        return {
            "content": content,
            "embedding": embedding,
            "content_metadata": metadata
        }

    async def embed_module_synthesis(self, module_name: str, synthesis: str) -> Dict[str, Any]:
        """Embed module-specific synthesis."""
        content = f"""{module_name.title()} Synthesis:
{synthesis}"""

        embedding = await self.embed_text(content)

        metadata = {
            "type": "module_synthesis",
            "module": module_name,
            "generated_at": datetime.now(UTC).isoformat()
        }

        return {
            "content": content,
            "embedding": embedding,
            "content_metadata": metadata
        }
