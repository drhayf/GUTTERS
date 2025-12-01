import { createClient } from '@supabase/supabase-js';

const supabaseUrl = process.env.EXPO_PUBLIC_SUPABASE_URL || '';
const supabaseAnonKey = process.env.EXPO_PUBLIC_SUPABASE_ANON_KEY || '';

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn('Supabase credentials not configured. RAG features will be disabled.');
}

export const supabase = createClient(supabaseUrl, supabaseAnonKey, {
  auth: {
    storage: undefined, // We'll use MMKV for secure storage
    autoRefreshToken: true,
    persistSession: true,
    detectSessionInUrl: false,
  },
});

/**
 * Initialize Supabase schema for RAG
 * Run this once to set up your database
 */
export const initializeSupabaseSchema = async () => {
  // This would typically be run via Supabase migrations
  // Included here for reference
  const schema = `
    -- Enable pgvector extension
    CREATE EXTENSION IF NOT EXISTS vector;

    -- Journal entries table
    CREATE TABLE IF NOT EXISTS journal_entries (
      id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      user_id UUID REFERENCES auth.users(id),
      content TEXT NOT NULL,
      embedding VECTOR(1536),
      metadata JSONB,
      created_at TIMESTAMPTZ DEFAULT NOW()
    );

    -- Framework knowledge base
    CREATE TABLE IF NOT EXISTS framework_knowledge (
      id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
      framework TEXT NOT NULL,
      content TEXT NOT NULL,
      embedding VECTOR(1536),
      metadata JSONB,
      created_at TIMESTAMPTZ DEFAULT NOW()
    );

    -- Create indexes for vector similarity search
    CREATE INDEX IF NOT EXISTS journal_embedding_idx ON journal_entries 
    USING ivfflat (embedding vector_cosine_ops);

    CREATE INDEX IF NOT EXISTS framework_embedding_idx ON framework_knowledge 
    USING ivfflat (embedding vector_cosine_ops);

    -- Function for similarity search
    CREATE OR REPLACE FUNCTION match_journal_entries(
      query_embedding VECTOR(1536),
      match_threshold FLOAT,
      match_count INT
    )
    RETURNS TABLE (
      id UUID,
      content TEXT,
      similarity FLOAT
    )
    LANGUAGE SQL STABLE
    AS $$
      SELECT
        id,
        content,
        1 - (embedding <=> query_embedding) AS similarity
      FROM journal_entries
      WHERE 1 - (embedding <=> query_embedding) > match_threshold
      ORDER BY embedding <=> query_embedding
      LIMIT match_count;
    $$;
  `;

  console.log('Supabase schema initialized. Run migrations manually.');
  return schema;
};
