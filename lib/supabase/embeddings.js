/**
 * RAG Embeddings Service
 * Uses Hugging Face Inference API for text embeddings
 * Model: BAAI/bge-small-en-v1.5 (384 dimensions)
 */
System.register(["./client"], function (exports_1, context_1) {
    "use strict";
    var client_1, HF_API_KEY, EMBEDDING_MODEL, EMBEDDING_API_URL;
    var __moduleName = context_1 && context_1.id;
    /**
     * Generate embedding for text using Hugging Face API
     */
    async function generateEmbedding(text) {
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
    exports_1("generateEmbedding", generateEmbedding);
    /**
     * Store journal entry with embedding for semantic search
     */
    async function storeJournalEntry(userId, content, metadata) {
        const embedding = await generateEmbedding(content);
        const { data, error } = await client_1.supabase.from('journal_entries').insert({
            user_id: userId,
            content,
            embedding,
            metadata,
        });
        if (error)
            throw error;
        return data;
    }
    exports_1("storeJournalEntry", storeJournalEntry);
    /**
     * Search journal entries by semantic similarity
     */
    async function searchJournalEntries(query, matchThreshold = 0.7, matchCount = 5) {
        const queryEmbedding = await generateEmbedding(query);
        const { data, error } = await client_1.supabase.rpc('match_journal_entries', {
            query_embedding: queryEmbedding,
            match_threshold: matchThreshold,
            match_count: matchCount,
        });
        if (error)
            throw error;
        return data;
    }
    exports_1("searchJournalEntries", searchJournalEntries);
    /**
     * Store framework knowledge with embedding
     */
    async function storeFrameworkKnowledge(framework, content, metadata) {
        const embedding = await generateEmbedding(content);
        const { data, error } = await client_1.supabase.from('framework_knowledge').insert({
            framework,
            content,
            embedding,
            metadata,
        });
        if (error)
            throw error;
        return data;
    }
    exports_1("storeFrameworkKnowledge", storeFrameworkKnowledge);
    /**
     * Search framework knowledge by semantic similarity
     */
    async function searchFrameworkKnowledge(query, framework, matchThreshold = 0.7, matchCount = 3) {
        const queryEmbedding = await generateEmbedding(query);
        let rpcQuery = client_1.supabase.rpc('match_framework_knowledge', {
            query_embedding: queryEmbedding,
            match_threshold: matchThreshold,
            match_count: matchCount,
        });
        if (framework) {
            rpcQuery = rpcQuery.eq('framework', framework);
        }
        const { data, error } = await rpcQuery;
        if (error)
            throw error;
        return data;
    }
    exports_1("searchFrameworkKnowledge", searchFrameworkKnowledge);
    return {
        setters: [
            function (client_1_1) {
                client_1 = client_1_1;
            }
        ],
        execute: function () {
            HF_API_KEY = process.env.EXPO_PUBLIC_HF_API_KEY;
            EMBEDDING_MODEL = 'BAAI/bge-small-en-v1.5';
            EMBEDDING_API_URL = `https://api-inference.huggingface.co/models/${EMBEDDING_MODEL}`;
        }
    };
});
