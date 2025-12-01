/**
 * AI Client Configuration
 *
 * VERIFIED FROM OFFICIAL SOURCES (November 8, 2025):
 * ============================================================
 * - AI SDK Docs: https://ai-sdk.dev/providers/ai-sdk-providers/google-generative-ai
 * - Google Gemini Models: https://ai.google.dev/gemini-api/docs/models
 *
 * Installed Packages:
 * - @ai-sdk/google: v2.0.29 (latest stable)
 * - ai: v5.0.89 (latest stable)
 * - @langchain/google-genai: v1.0.0
 *
 * CURRENT GEMINI MODELS (December 2024):
 * ============================================================
 *
 * Gemini 2.5 Series (LATEST):
 * ----------------------------------------------
 * - gemini-2.5-pro: Most advanced and capable model
 * - gemini-2.5-flash: Latest fast model with excellent capabilities
 * - gemini-2.5-flash-lite: Lightweight variant
 *
 * Gemini 2.0 Series:
 * ----------------------------------------------
 * - gemini-2.0-flash: Fast model with good capabilities
 * - gemini-2.0-flash-exp: Experimental version
 *
 * Gemini 1.5 Series (Stable Production):
 * ----------------------------------------------
 * - gemini-1.5-pro: Stable production model
 * - gemini-1.5-pro-latest: Auto-updating version
 * - gemini-1.5-flash: Stable fast model
 * - gemini-1.5-flash-latest: Auto-updating version
 *
 * IMPORTANT: Model names do NOT include "models/" prefix when using @ai-sdk/google
 *
 * This configuration provides:
 * - Vercel AI SDK integration (generateText, streamText, generateObject)
 * - LangChain integration (for agent workflows)
 */
System.register(["@ai-sdk/google", "@langchain/google-genai"], function (exports_1, context_1) {
    "use strict";
    var google_1, google, chatModel, synthesisModel, quickModel, stableModel, google_genai_1, langchainChatModel, langchainSynthesisModel, defaultConfig, models;
    var __moduleName = context_1 && context_1.id;
    return {
        setters: [
            function (google_1_1) {
                google_1 = google_1_1;
            },
            function (google_genai_1_1) {
                google_genai_1 = google_genai_1_1;
            }
        ],
        execute: function () {
            // Log configuration on module load
            console.log('[AI Client] Initializing AI SDK configuration');
            console.log('[AI Client] API Key present:', !!process.env.EXPO_PUBLIC_GOOGLE_API_KEY);
            console.log('[AI Client] API Key length:', process.env.EXPO_PUBLIC_GOOGLE_API_KEY?.length || 0);
            /**
             * ==========================================
             * SECTION 1: VERCEL AI SDK CONFIGURATION
             * ==========================================
             * Documentation: https://ai-sdk.dev/providers/ai-sdk-providers/google-generative-ai
             * For use with generateText(), streamText(), and generateObject() from 'ai' package
             */
            /**
             * Initialize Google AI provider for Vercel AI SDK
             *
             * Environment Variable Required: EXPO_PUBLIC_GOOGLE_API_KEY
             * Get your API key: https://aistudio.google.com/app/apikey
             */
            exports_1("google", google = google_1.createGoogleGenerativeAI({
                apiKey: process.env.EXPO_PUBLIC_GOOGLE_API_KEY || '',
            }));
            exports_1("aiProvider", google);
            console.log('[AI Client] Google AI provider created');
            /**
             * PRIMARY CHAT MODEL: Gemini 2.5 Flash
             *
             * Model ID: gemini-2.5-flash
             *
             * Latest fast model from Google with excellent capabilities.
             * Best choice for most interactive applications.
             *
             * Use for:
             * - Real-time chat applications
             * - Interactive conversations
             * - General-purpose AI tasks
             * - Multimodal interactions (text, images, audio, video)
             *
             * ✅ RECOMMENDED: Latest generation, production-ready
             */
            exports_1("chatModel", chatModel = google('gemini-2.5-flash'));
            console.log('[AI Client] chatModel initialized: gemini-2.5-flash');
            /**
             * SYNTHESIS MODEL: Gemini 2.5 Pro
             *
             * Model ID: gemini-2.5-pro
             *
             * Google's most advanced and capable AI model.
             * Use when you need maximum reasoning and analysis capabilities.
             *
             * Use for:
             * - Complex reasoning and analysis
             * - Long-context understanding
             * - Human Design chart interpretations
             * - Multi-document synthesis
             * - Advanced code generation
             *
             * ✅ MOST CAPABLE: Best for complex tasks
             */
            exports_1("synthesisModel", synthesisModel = google('gemini-2.5-pro'));
            console.log('[AI Client] synthesisModel initialized: gemini-2.5-pro');
            /**
             * QUICK MODEL: Gemini 2.5 Flash Lite
             *
             * Model ID: gemini-2.5-flash-lite
             *
             * Lightweight, fast variant for high-volume simple tasks.
             *
             * Use for:
             * - Simple queries
             * - High-volume requests
             * - Quick validations
             * - Cost optimization
             *
             * ✅ FASTEST: Optimized for speed and efficiency
             */
            exports_1("quickModel", quickModel = google('gemini-2.5-flash-lite'));
            console.log('[AI Client] quickModel initialized: gemini-2.5-flash-lite');
            /**
             * STABLE MODEL: Gemini 2.5 Pro
             *
             * Model ID: gemini-2.5-pro
             *
             * Google's most advanced and capable AI model.
             * Use when you need maximum reasoning and reliability.
             *
             * Use for:
             * - Production workloads requiring highest quality
             * - Complex reasoning and analysis
             * - Mission-critical applications
             * - Maximum capability and stability
             *
             * ✅ MOST CAPABLE: Best reasoning and reliability
             */
            exports_1("stableModel", stableModel = google('gemini-2.5-pro'));
            console.log('[AI Client] stableModel initialized: gemini-2.5-pro');
            /**
             * LangChain Chat Model for Agents
             *
             * This provides a LangChain-compatible interface to Gemini models
             * for use in agent-based workflows, chains, and tools.
             *
             * Using Gemini 2.5 Flash for best performance with LangChain agents.
             *
             * Documentation: https://js.langchain.com/docs/integrations/chat/google_generativeai
             */
            exports_1("langchainChatModel", langchainChatModel = new google_genai_1.ChatGoogleGenerativeAI({
                model: 'gemini-2.5-flash',
                temperature: 0.7,
                maxOutputTokens: 8192,
                apiKey: process.env.EXPO_PUBLIC_GOOGLE_API_KEY,
            }));
            console.log('[AI Client] langchainChatModel initialized: gemini-2.5-flash');
            /**
             * LangChain Synthesis Model (High Capability)
             *
             * For complex reasoning tasks in agent workflows.
             * Using Gemini 2.5 Pro for maximum capabilities.
             */
            exports_1("langchainSynthesisModel", langchainSynthesisModel = new google_genai_1.ChatGoogleGenerativeAI({
                model: 'gemini-2.5-pro',
                temperature: 0.7,
                maxOutputTokens: 8192,
                apiKey: process.env.EXPO_PUBLIC_GOOGLE_API_KEY,
            }));
            console.log('[AI Client] langchainSynthesisModel initialized: gemini-2.5-pro');
            /**
             * EXAMPLE USAGE - LangChain:
             *
             * Simple Invocation:
             * ```typescript
             * import { langchainChatModel } from '@/lib/ai/client';
             * import { HumanMessage, SystemMessage } from '@langchain/core/messages';
             *
             * const response = await langchainChatModel.invoke([
             *   new SystemMessage('You are a Human Design expert.'),
             *   new HumanMessage('What is my Type if I have a defined Sacral?')
             * ]);
             *
             * console.log(response.content);
             * ```
             *
             * With Streaming:
             * ```typescript
             * import { langchainChatModel } from '@/lib/ai/client';
             *
             * const stream = await langchainChatModel.stream([
             *   { role: 'user', content: 'Explain Gene Keys' }
             * ]);
             *
             * for await (const chunk of stream) {
             *   console.log(chunk.content);
             * }
             * ```
             *
             * In a Chain:
             * ```typescript
             * import { langchainSynthesisModel } from '@/lib/ai/client';
             * import { PromptTemplate } from '@langchain/core/prompts';
             *
             * const prompt = PromptTemplate.fromTemplate(
             *   'Analyze this birth data: {birthData}'
             * );
             *
             * const chain = prompt.pipe(langchainSynthesisModel);
             * const result = await chain.invoke({ birthData: '...' });
             * ```
             */
            /**
             * ==========================================
             * SECTION 3: SHARED CONFIGURATION
             * ==========================================
             */
            /**
             * Default generation parameters
             * Apply these when calling AI SDK functions
             */
            exports_1("defaultConfig", defaultConfig = {
                temperature: 0.7, // 0.0-2.0: Controls randomness (lower = more focused)
                maxTokens: 8192, // Maximum output tokens
                topP: 0.95, // Nucleus sampling threshold
                topK: 40, // Top-K sampling for diversity
            });
            // Organized model export
            exports_1("models", models = {
                // Vercel AI SDK models
                vercel: {
                    chat: chatModel, // Gemini 2.5 Flash (latest)
                    synthesis: synthesisModel, // Gemini 2.5 Pro (most capable)
                    quick: quickModel, // Gemini 2.5 Flash Lite (fastest)
                    stable: stableModel, // Gemini 2.5 Pro (stable & capable)
                },
                // LangChain models
                langchain: {
                    chat: langchainChatModel,
                    synthesis: langchainSynthesisModel,
                },
            });
        }
    };
});
