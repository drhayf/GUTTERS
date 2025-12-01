export const AI_MODELS = {
  GEMINI_3_PRO_PREVIEW: 'gemini-3-pro-preview',
  GEMINI_25_FLASH: 'gemini-2.5-flash',
  GEMINI_25_PRO: 'gemini-2.5-pro',
  GEMINI_25_FLASH_LITE: 'gemini-2.5-flash-lite',
} as const;

export const DEFAULT_MODELS = {
  PRIMARY_CHAT: AI_MODELS.GEMINI_3_PRO_PREVIEW,
  SYNTHESIS: AI_MODELS.GEMINI_25_PRO,
  QUICK: AI_MODELS.GEMINI_25_FLASH_LITE,
  STABLE: AI_MODELS.GEMINI_25_PRO,
} as const;

export const HRM_CONFIG = {
  ENABLE_HRM_LOGIC: true,
  THINKING_LEVEL: 'high' as 'low' | 'high',
  MAX_REASONING_DEPTH: 3,
  BEAM_SIZE: 2,
  CANDIDATE_COUNT: 3,
  SCORE_THRESHOLD: 0.6,
} as const;

export const GENESIS_PHASES = {
  AWAKENING: 'awakening',
  EXCAVATION: 'excavation',
  MAPPING: 'mapping',
  SYNTHESIS: 'synthesis',
  ACTIVATION: 'activation',
} as const;

export const UNIVERSAL_PROTOCOL = {
  INSIGHT_TYPES: ['Pattern', 'Fact', 'Suggestion'] as const,
  CONFIDENCE_RANGE: { min: 0.0, max: 1.0 },
} as const;

export const API_CONFIG = {
  PYTHON_API_PREFIX: '/api/python',
  FASTAPI_PORT: 8000,
  EXPO_PORT: 5000,
} as const;

export type AIModel = typeof AI_MODELS[keyof typeof AI_MODELS];
export type GenesisPhase = typeof GENESIS_PHASES[keyof typeof GENESIS_PHASES];
export type InsightType = typeof UNIVERSAL_PROTOCOL.INSIGHT_TYPES[number];
