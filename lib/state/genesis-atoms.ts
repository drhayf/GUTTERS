import { atom } from 'jotai';
import type { GenesisPayload, VisualsConfig } from '../../packages/ui/registry';

export type AIState = 'idle' | 'listening' | 'thinking' | 'responding' | 'alert';

export type GenesisPhase = 
  | 'awakening'
  | 'excavation'
  | 'mapping'
  | 'synthesis'
  | 'activation';

export interface GenesisInteraction {
  id: string;
  type: 'question' | 'response' | 'insight';
  payload: GenesisPayload;
  timestamp: Date;
  userResponse?: string;
}

export const aiStateAtom = atom<AIState>('idle');

export const currentPhaseAtom = atom<GenesisPhase>('awakening');

export const pulseColorAtom = atom<string>((get) => {
  const state = get(aiStateAtom);
  switch (state) {
    case 'listening':
    case 'idle':
      return '#00FFFF';
    case 'thinking':
      return '#9333EA';
    case 'responding':
      return '#FFD700';
    case 'alert':
      return '#FF0000';
    default:
      return '#00FFFF';
  }
});

export const backgroundIntensityAtom = atom<number>(0.3);

export const currentVisualsAtom = atom<VisualsConfig>({
  pulse_color: 'cyan',
  background_intensity: 0.3,
  theme: 'void',
  animation: 'pulse',
});

export const currentPayloadAtom = atom<GenesisPayload | null>(null);

export const interactionHistoryAtom = atom<GenesisInteraction[]>([]);

export const sessionIdAtom = atom<string | null>(null);

export const isStreamingAtom = atom<boolean>(false);

// HRM atoms have been moved to lib/state/hrm-atoms.ts
// Import hrmConfigAtom, hrmEnabledAtom from there instead

export const phaseColorsAtom = atom<Record<GenesisPhase, string>>({
  awakening: '#6B21A8',
  excavation: '#92400E',
  mapping: '#0891B2',
  synthesis: '#7C3AED',
  activation: '#DC2626',
});
