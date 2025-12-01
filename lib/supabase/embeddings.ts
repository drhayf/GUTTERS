/**
 * RAG Embeddings Service
 * Uses Hugging Face Inference API for text embeddings
 * Model: BAAI/bge-small-en-v1.5 (384 dimensions)
 */

import { supabase } from './client';

const HF_API_KEY = process.env.EXPO_PUBLIC_HF_API_KEY;
const EMBEDDING_MODEL = 'BAAI/bge-small-en-v1.5';
const EMBEDDING_API_URL = `https://api-inference.huggingface.co/models/${EMBEDDING_MODEL}`;

/**
 * Generate embedding for text using Hugging Face API
 */
export async function generateEmbedding(text: string): Promise<number[]> {
  const response = await fetch(EMBEDDING_API_URL, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${HF_API_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      inputs: text,
      options: { wait_for_model: true },
    }),
  });

  if (!response.ok) {
    throw new Error(`HF API error: ${response.statusText}`);
  }

  const embedding = await response.json();
  return embedding;
}

/**
 * Store journal entry with embedding for semantic search
 */
export async function storeJournalEntry(
  userId: string,
  content: string,
  metadata?: Record<string, any>
) {
  const embedding = await generateEmbedding(content);

  const { data, error } = await supabase.from('journal_entries').insert({
    user_id: userId,
    content,
    embedding,
    metadata,
  });

  if (error) throw error;
  return data;
}

/**
 * Search journal entries by semantic similarity
 */
export async function searchJournalEntries(
  query: string,
  matchThreshold: number = 0.7,
  matchCount: number = 5
) {
  const queryEmbedding = await generateEmbedding(query);

  const { data, error } = await supabase.rpc('match_journal_entries', {
    query_embedding: queryEmbedding,
    match_threshold: matchThreshold,
    match_count: matchCount,
  });

  if (error) throw error;
  return data;
}

/**
 * Store framework knowledge with embedding
 */
export async function storeFrameworkKnowledge(
  framework: string,
  content: string,
  metadata?: Record<string, any>
) {
  const embedding = await generateEmbedding(content);

  const { data, error } = await supabase.from('framework_knowledge').insert({
    framework,
    content,
    embedding,
    metadata,
  });

  if (error) throw error;
  return data;
}

/**
 * Search framework knowledge by semantic similarity
 */
export async function searchFrameworkKnowledge(
  query: string,
  framework?: string,
  matchThreshold: number = 0.7,
  matchCount: number = 3
) {
  const queryEmbedding = await generateEmbedding(query);

  let rpcQuery = supabase.rpc('match_framework_knowledge', {
    query_embedding: queryEmbedding,
    match_threshold: matchThreshold,
    match_count: matchCount,
  });

  if (framework) {
    rpcQuery = rpcQuery.eq('framework', framework);
  }

  const { data, error } = await rpcQuery;

  if (error) throw error;
  return data;
}
