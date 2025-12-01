import { atom } from 'jotai';
import { AgentOutput } from '../agents/base-agent';

/**
 * Global state atoms for the app
 */

// Birth data
export const birthDataAtom = atom<{
  date: string;
  time: string;
  location: { latitude: number; longitude: number };
} | null>(null);

// Current active framework
export const activeFrameworkAtom = atom<string>('human-design');

// Agent outputs cache
export const agentOutputsAtom = atom<Record<string, AgentOutput>>({});

// Chat messages
export interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  agentData?: AgentOutput;
}

export const messagesAtom = atom<Message[]>([]);

// Health metrics (from HealthKit)
export const healthMetricsAtom = atom<Record<string, any>>({});

// Journal entries
export const journalEntriesAtom = atom<
  Array<{
    id: string;
    content: string;
    timestamp: Date;
    tags: string[];
  }>
>([]);
