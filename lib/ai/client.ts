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

import { createGoogleGenerativeAI } from '@ai-sdk/google';

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
export const google = createGoogleGenerativeAI({
  apiKey: process.env.EXPO_PUBLIC_GOOGLE_API_KEY || '',
});

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
export const chatModel = google('gemini-2.5-flash');
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
export const synthesisModel = google('gemini-2.5-pro');
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
export const quickModel = google('gemini-2.5-flash-lite');
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
export const stableModel = google('gemini-2.5-pro');
console.log('[AI Client] stableModel initialized: gemini-2.5-pro');

/**
 * EXAMPLE USAGE - Vercel AI SDK:
 * 
 * Basic Text Generation:
 * ```typescript
 * import { generateText } from 'ai';
 * import { stableModel } from '@/lib/ai/client';
 * 
 * const result = await generateText({
 *   model: stableModel,
 *   prompt: 'Explain Human Design Type concepts',
 *   temperature: 0.7,
 *   maxTokens: 2000,
 * });
 * 
 * console.log(result.text);
 * ```
 * 
 * Streaming Text:
 * ```typescript
 * import { streamText } from 'ai';
 * import { chatModel } from '@/lib/ai/client';
 * 
 * const stream = await streamText({
 *   model: chatModel,
 *   prompt: 'Generate a detailed birth chart analysis',
 *   temperature: 0.8,
 * });
 * 
 * for await (const chunk of stream.textStream) {
 *   process.stdout.write(chunk);
 * }
 * ```
 * 
 * Structured Output:
 * ```typescript
 * import { generateObject } from 'ai';
 * import { synthesisModel } from '@/lib/ai/client';
 * import { z } from 'zod';
 * 
 * const result = await generateObject({
 *   model: synthesisModel,
 *   schema: z.object({
 *     type: z.string(),
 *     strategy: z.string(),
 *     authority: z.string(),
 *   }),
 *   prompt: 'Extract Human Design chart data from: ...',
 * });
 * ```
 */

/**
 * ==========================================
 * SECTION 2: LANGCHAIN CONFIGURATION
 * ==========================================
 * For use with LangChain agents, chains, and tools
 * Package: @langchain/google-genai (v1.0.0)
 * 
 * NOTE: LangChain is only available on native platforms due to
 * Node.js dependencies that don't work in web environments.
 */

import { Platform } from 'react-native';

let ChatGoogleGenerativeAI: any;
if (Platform.OS !== 'web') {
  try {
    ({ ChatGoogleGenerativeAI } = require('@langchain/google-genai'));
  } catch (e) {
    console.warn('[AI Client] LangChain not available on this platform');
  }
}

/**
 * LangChain Chat Model for Agents
 * 
 * This provides a LangChain-compatible interface to Gemini models
 * for use in agent-based workflows, chains, and tools.
 * 
 * Using Gemini 2.5 Flash for best performance with LangChain agents.
 * 
 * Documentation: https://js.langchain.com/docs/integrations/chat/google_generativeai
 * 
 * ⚠️ NATIVE ONLY: Not available on web platform
 */
export const langchainChatModel = Platform.OS !== 'web' && ChatGoogleGenerativeAI ? new ChatGoogleGenerativeAI({
  model: 'gemini-2.5-flash',
  temperature: 0.7,
  maxOutputTokens: 8192,
  apiKey: process.env.EXPO_PUBLIC_GOOGLE_API_KEY,
}) : null;

if (langchainChatModel) {
  console.log('[AI Client] langchainChatModel initialized: gemini-2.5-flash');
} else {
  console.log('[AI Client] langchainChatModel not available (web platform)');
}

/**
 * LangChain Synthesis Model (High Capability)
 * 
 * For complex reasoning tasks in agent workflows.
 * Using Gemini 2.5 Pro for maximum capabilities.
 * 
 * ⚠️ NATIVE ONLY: Not available on web platform
 */
export const langchainSynthesisModel = Platform.OS !== 'web' && ChatGoogleGenerativeAI ? new ChatGoogleGenerativeAI({
  model: 'gemini-2.5-pro',
  temperature: 0.7,
  maxOutputTokens: 8192,
  apiKey: process.env.EXPO_PUBLIC_GOOGLE_API_KEY,
}) : null;

if (langchainSynthesisModel) {
  console.log('[AI Client] langchainSynthesisModel initialized: gemini-2.5-pro');
} else {
  console.log('[AI Client] langchainSynthesisModel not available (web platform)');
}

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
export const defaultConfig = {
  temperature: 0.7, // 0.0-2.0: Controls randomness (lower = more focused)
  maxTokens: 8192, // Maximum output tokens
  topP: 0.95, // Nucleus sampling threshold
  topK: 40, // Top-K sampling for diversity
};

/**
 * ==========================================
 * CONVENIENCE EXPORTS
 * ==========================================
 */

// Primary provider for general use
export { google as aiProvider };

// Organized model export
export const models = {
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
} as const;

/**
 * ==========================================
 * IMPLEMENTATION NOTES & BEST PRACTICES
 * ==========================================
 * 
 * ENVIRONMENT SETUP:
 * ------------------
 * 1. Get API key from: https://aistudio.google.com/app/apikey
 * 2. Create .env file in project root:
 * ```
 * EXPO_PUBLIC_GOOGLE_API_KEY=your_actual_api_key_here
 * ```
 * 3. Restart Expo dev server after adding environment variables
 * 
 * MODEL SELECTION GUIDE:
 * ----------------------
 * Choose based on your use case:
 * 
 * For Production Apps:
 * → stableModel (Gemini 1.5 Flash) - RECOMMENDED
 *   Best balance of speed, cost, and reliability
 * 
 * For Complex Analysis:
 * → synthesisModel (Gemini 1.5 Pro)
 *   Use when you need maximum context (2M tokens) or superior reasoning
 * 
 * For High Volume/Simple Tasks:
 * → quickModel (Gemini 1.5 Flash-8B)
 *   Use for simple queries, validations, or cost optimization
 * 
 * For Experimentation Only:
 * → chatModel (Gemini 2.0 Flash Experimental)
 *   Test latest features but expect potential instability
 * 
 * RATE LIMITS (Free Tier - December 2024):
 * -----------------------------------------
 * Gemini 1.5 Flash:
 * - 15 requests/minute
 * - 1M tokens/minute
 * - 1,500 requests/day
 * 
 * Gemini 1.5 Pro:
 * - 2 requests/minute
 * - 32,000 tokens/minute
 * - 50 requests/day
 * 
 * Gemini 2.0 Flash (Experimental):
 * - Rate limits may vary
 * - Subject to change during preview period
 * 
 * For higher limits: https://ai.google.dev/pricing
 * 
 * CURRENT MODEL STATUS (December 2024):
 * -------------------------------------
 * ✅ STABLE & PRODUCTION-READY:
 * - Gemini 1.5 Pro (most capable, 2M context)
 * - Gemini 1.5 Flash (recommended for most use cases)
 * - Gemini 1.5 Flash-8B (fastest, lightest)
 * 
 * ⚠️ EXPERIMENTAL (Use with caution):
 * - Gemini 2.0 Flash (preview, may change)
 * 
 * 📌 IMPORTANT:
 * Gemini 1.5 is NOT outdated - it's the current stable production line
 * with proven reliability. Gemini 2.0 is experimental preview only.
 * 
 * PACKAGE VERSIONS (Verified Nov 8, 2025):
 * -----------------------------------------
 * - @ai-sdk/google: 2.0.29 (latest stable)
 * - ai: 5.0.89 (latest stable)
 * - @langchain/google-genai: 1.0.0
 * - langchain: 1.0.3
 * 
 * Beta versions exist (ai@6.0.0-beta, @ai-sdk/google@3.0.0-beta)
 * but are not recommended for production use.
 * 
 * MULTIMODAL CAPABILITIES:
 * ------------------------
 * All Gemini 1.5 and 2.0 models support:
 * - Text generation
 * - Image understanding
 * - Audio processing
 * - Video analysis
 * - Document parsing
 * 
 * See: https://ai.google.dev/gemini-api/docs/vision
 * 
 * ERROR HANDLING:
 * ---------------
 * Always wrap AI calls in try-catch blocks:
 * ```typescript
 * try {
 *   const result = await generateText({
 *     model: stableModel,
 *     prompt: 'Your prompt',
 *   });
 * } catch (error) {
 *   if (error.message.includes('rate limit')) {
 *     // Handle rate limit
 *   } else if (error.message.includes('API key')) {
 *     // Handle auth error
 *   }
 *   console.error('AI generation failed:', error);
 * }
 * ```
 * 
 * EXPO SPECIFIC NOTES:
 * --------------------
 * - Environment variables must start with EXPO_PUBLIC_ to be accessible
 * - Restart dev server after changing .env file
 * - API calls work in both development and production builds
 * - Consider implementing request caching for better UX
 * 
 * USEFUL LINKS:
 * -------------
 * - AI SDK Docs: https://ai-sdk.dev
 * - Google AI Studio: https://aistudio.google.com
 * - Model Pricing: https://ai.google.dev/pricing
 * - LangChain Docs: https://js.langchain.com
 * - Expo Docs: https://docs.expo.dev
 */
