import React, { useEffect, useState, useCallback, useRef } from 'react';
import { StyleSheet, View, KeyboardAvoidingView, Platform, SafeAreaView, Alert, Keyboard, TouchableWithoutFeedback, Modal, TouchableOpacity } from 'react-native';
import { YStack, Text, Spinner } from 'tamagui';
import Animated, { FadeIn, FadeOut, SlideInDown, SlideOutUp } from 'react-native-reanimated';
import { useAtom, useSetAtom, useAtomValue } from 'jotai';
import { StatusBar } from 'expo-status-bar';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Crypto from 'expo-crypto';
import { useRouter } from 'expo-router';

import { PulsingBorder } from '../../components/genesis/PulsingBorder';
import { GenerativeRenderer } from '../../components/genesis/GenerativeRenderer';
import { ReflexTapComponent } from '../../components/genesis/ReflexTapComponent';
import {
  aiStateAtom,
  currentPhaseAtom,
  currentPayloadAtom,
  sessionIdAtom,
  isStreamingAtom,
  interactionHistoryAtom,
  type GenesisInteraction,
} from '../../lib/state/genesis-atoms';
import { selectedModelAtom } from '../../lib/state/model-atom';
import { hrmConfigAtom, hrmApiPayloadAtom } from '../../lib/state/hrm-atoms';
import { modelConfigAtom } from '../../lib/state/model-config-atoms';
import { enabledModulesAtom } from '../../lib/state/module-preferences-atoms';
import { apiClient } from '../../lib/api-client';
import type { GenesisPayload, ComponentDefinition } from '../../packages/ui/registry';
import { getGameScheduler, type GameDefinition, type GameResult, saveGameResult } from '../../lib/games';

const GENESIS_SESSION_KEY = '@sovereign/genesis_session';
const GENESIS_RESPONSES_KEY = '@sovereign/genesis_responses';

// Profile is considered complete after this many responses
const COMPLETION_THRESHOLD = 25;

interface StoredSession {
  sessionId: string;
  phase: string;
  questionIndex: number;
  responses: Array<{ question: string; response: string; phase: string }>;
  lastPayload?: GenesisPayload | null; // Store the last displayed payload
  profileComplete?: boolean; // Explicit completion flag
  digitalTwin?: Record<string, unknown> | null; // Stored Digital Twin data from backend
  createdAt: string;
}

export default function GenesisScreen() {
  const router = useRouter();
  const [aiState, setAiState] = useAtom(aiStateAtom);
  const [currentPhase, setCurrentPhase] = useAtom(currentPhaseAtom);
  const [currentPayload, setCurrentPayload] = useAtom(currentPayloadAtom);
  const [sessionId, setSessionId] = useAtom(sessionIdAtom);
  const [isStreaming, setIsStreaming] = useAtom(isStreamingAtom);
  const hrmConfig = useAtomValue(hrmConfigAtom);
  const hrmApiPayload = useAtomValue(hrmApiPayloadAtom);
  const modelConfig = useAtomValue(modelConfigAtom);
  const enabledModules = useAtomValue(enabledModulesAtom);
  const [selectedModel] = useAtom(selectedModelAtom);
  const setHistory = useSetAtom(interactionHistoryAtom);
  
  const [isInitialized, setIsInitialized] = useState(false);
  const [isLoadingSession, setIsLoadingSession] = useState(true);
  const [storedResponses, setStoredResponses] = useState<StoredSession['responses']>([]);
  const [error, setError] = useState<string | null>(null);
  const [streamingText, setStreamingText] = useState('');
  const [toastMessage, setToastMessage] = useState<string | null>(null);
  const [activeGame, setActiveGame] = useState<GameDefinition | null>(null);
  const [isRestoredSession, setIsRestoredSession] = useState(false); // Track if session was restored
  const abortControllerRef = useRef<AbortController | null>(null);
  const hasInitializedRef = useRef(false);
  const gameSchedulerRef = useRef(getGameScheduler());
  
  const getPulseColorForPhase = (phase?: string): 'cyan' | 'purple' | 'gold' | 'red' | 'green' => {
    switch (phase) {
      case 'awakening': return 'purple';
      case 'excavation': return 'gold';
      case 'mapping': return 'cyan';
      case 'synthesis': return 'purple';
      case 'activation': return 'red';
      default: return 'cyan';
    }
  };

  // Generate a completion payload when we detect profile is complete but payload is missing/corrupted
  const generateCompletionPayload = useCallback((
    responses: StoredSession['responses'],
    savedDigitalTwin?: Record<string, unknown> | null
  ): GenesisPayload => {
    console.log('[Genesis] Generating completion payload from', responses.length, 'responses', savedDigitalTwin ? '(with saved Digital Twin)' : '(no saved Digital Twin)');
    
    // Use saved Digital Twin if available, otherwise use placeholder
    const digitalTwin = savedDigitalTwin ? savedDigitalTwin : {
      summary: "Your Genesis journey is complete. Your responses have been captured and your Digital Twin awaits synthesis.",
      energetic_signature: {
        hd_type: "Awaiting Synthesis", // Placeholder - would be calculated from birth data
        hd_profile: "View Full Profile",
        hd_strategy: "To Be Revealed",
        hd_authority: "Pending Analysis",
      },
      psychological_profile: {
        cognitive_style: "Unique Pattern Detected",
      },
      archetypes: {
        primary_archetypes: ["Your Archetype"],
      },
    };
    
    return {
      type: 'profiler_step',
      phase: 'activation',
      components: [
        {
          type: 'progress',
          current: responses.length,
          total: responses.length,
        },
        {
          type: 'text',
          content: `Congratulations! You've completed ${responses.length} profound exchanges. Your Digital Twin has been forged from the depths of your responses.`,
          variant: 'insight',
        },
        {
          type: 'digital_twin_card',
          digital_twin: digitalTwin,
        },
        {
          type: 'activation_steps',
          steps: [
            {
              id: '1',
              title: 'Review Your Profile',
              description: 'Explore the insights discovered during your Genesis journey.',
              priority: 'high',
              category: 'reflection',
              icon: '🔮',
            },
            {
              id: '2', 
              title: 'Configure Preferences',
              description: 'Set up your module preferences and personalization settings.',
              priority: 'medium',
              category: 'setup',
              icon: '⚙️',
            },
            {
              id: '3',
              title: 'Begin Your Journey',
              description: 'Start using your personalized AI companion.',
              priority: 'medium',
              category: 'action',
              icon: '🚀',
            },
          ],
        },
        {
          type: 'completion_transition',
          transition_type: 'reveal',
        },
      ],
      interpretationSeed: 'Profile complete',
      calculation: {
        phase: 'activation',
        questionIndex: responses.length,
        totalQuestions: responses.length,
        profile_complete: true,
      },
      visuals: {
        pulse_color: 'red',
        background_intensity: 0.5,
      },
    };
  }, []);
  
  const handleStreamEvent = useCallback((event: { type: string; data?: unknown }) => {
    switch (event.type) {
      case 'start':
        setAiState('thinking');
        setIsStreaming(true);
        setStreamingText('');
        break;
        
      case 'token':
        setStreamingText((prev) => prev + (event.data as string));
        break;
        
      case 'chunk':
        const chunkData = event.data as Partial<GenesisPayload>;
        if (chunkData.phase) {
          setCurrentPhase(chunkData.phase as typeof currentPhase);
          setAiState('thinking');
        }
        break;
        
      case 'end':
        setIsStreaming(false);
        setAiState('listening');
        break;
        
      case 'error':
        setIsStreaming(false);
        setAiState('alert');
        setError(String(event.data));
        break;
    }
  }, [setAiState, setIsStreaming, setCurrentPhase]);
  
  // Load existing session from storage
  const loadSession = useCallback(async (): Promise<StoredSession | null> => {
    try {
      const stored = await AsyncStorage.getItem(GENESIS_SESSION_KEY);
      if (stored) {
        const session = JSON.parse(stored) as StoredSession;
        console.log('[Genesis] Loaded session:', {
          hasPayload: !!session.lastPayload,
          responseCount: session.responses?.length || 0,
          phase: session.phase,
        });
        return session;
      }
    } catch (err) {
      console.error('[Genesis] Failed to load session:', err);
    }
    return null;
  }, []);
  
  // Save session to storage
  const saveSession = useCallback(async (session: Partial<StoredSession>) => {
    try {
      const existing = await loadSession();
      const updated: StoredSession = {
        sessionId: session.sessionId || existing?.sessionId || sessionId || '',
        phase: session.phase || existing?.phase || currentPhase,
        questionIndex: session.questionIndex ?? existing?.questionIndex ?? 0,
        responses: session.responses || existing?.responses || storedResponses,
        lastPayload: session.lastPayload !== undefined ? session.lastPayload : existing?.lastPayload || null,
        profileComplete: session.profileComplete ?? existing?.profileComplete ?? false,
        createdAt: existing?.createdAt || new Date().toISOString(),
      };
      await AsyncStorage.setItem(GENESIS_SESSION_KEY, JSON.stringify(updated));
      console.log('[Genesis] Session saved, phase:', updated.phase, 'responses:', updated.responses.length, 'complete:', updated.profileComplete);
    } catch (err) {
      console.error('[Genesis] Failed to save session:', err);
    }
  }, [loadSession, sessionId, currentPhase, storedResponses]);
  
  // Generate or retrieve session ID
  const getOrCreateSessionId = useCallback(async (): Promise<string> => {
    const existing = await loadSession();
    if (existing?.sessionId) {
      return existing.sessionId;
    }
    // Generate a new UUID
    const newId = await Crypto.randomUUID();
    await saveSession({ sessionId: newId });
    return newId;
  }, [loadSession, saveSession]);
  
  const initializeSessionWithStream = useCallback(async (existingSessionId?: string, existingResponses?: StoredSession['responses']) => {
    // Prevent double initialization
    if (hasInitializedRef.current) {
      return;
    }
    hasInitializedRef.current = true;
    
    setAiState('thinking');
    setError(null);
    setIsStreaming(true);
    
    abortControllerRef.current = new AbortController();
    
    // Get or create session ID
    const activeSessionId = existingSessionId || await getOrCreateSessionId();
    setSessionId(activeSessionId);
    
    // Use passed responses (from loaded session) or fall back to state
    const responsesToUse = existingResponses || storedResponses;
    
    // Build context with previous responses for smarter questions
    // CRITICAL: If no responses exist, this is a FRESH start - always ask question 1
    const contextMessage = responsesToUse.length > 0
      ? `Continue the Genesis profiling. Previous responses:\n${responsesToUse.map(r => `Q: ${r.question}\nA: ${r.response}`).join('\n\n')}\n\nGenerate the next appropriate question.`
      : 'Begin the Genesis profiling process. Introduce yourself as my guide through self-discovery. This is the very first interaction - ask your first penetrating question.';
    
    console.log('[Genesis] Initializing stream with', responsesToUse.length, 'previous responses');
    
    try {
      await apiClient.chatStream(
        {
          message: contextMessage,
          session_id: activeSessionId,
          enable_hrm: hrmConfig.enabled,
          hrm_config: hrmApiPayload,
          model: modelConfig.primary, // Primary model for conversation
          models_config: {
            primary: modelConfig.primary,
            fast: modelConfig.fast,
            synthesis: modelConfig.synthesis,
            fallback: modelConfig.fallback,
          },
          enabled_capabilities: enabledModules, // Include enabled modules
        },
        {
          onStart: () => {
            handleStreamEvent({ type: 'start' });
          },
          onToken: (token: string) => {
            handleStreamEvent({ type: 'token', data: token });
          },
          onAgentOutput: (output) => {
            const payload: GenesisPayload = {
              type: 'profiler_step',
              phase: output.calculation?.phase || 'awakening',
              components: output.visualizationData?.components || [],
              interpretationSeed: output.interpretationSeed,
              calculation: output.calculation,
              correlations: output.correlations,
              method: output.method,
              confidence: output.confidence,
              visuals: {
                pulse_color: getPulseColorForPhase(output.calculation?.phase),
                background_intensity: 0.3,
              },
            };
            
            setCurrentPayload(payload);
            setCurrentPhase(payload.phase as typeof currentPhase || 'awakening');
            
            // Save the payload to session storage
            saveSession({ lastPayload: payload, phase: payload.phase });
            
            if (output.calculation?.session_id) {
              setSessionId(output.calculation.session_id);
            }
            
            const interaction: GenesisInteraction = {
              id: Date.now().toString(),
              type: 'question',
              payload,
              timestamp: new Date(),
            };
            setHistory((prev) => [...prev, interaction]);
          },
          onComplete: (response) => {
            handleStreamEvent({ type: 'end' });
            
            if (response.session_id) {
              setSessionId(response.session_id);
            }
            
            setIsInitialized(true);
          },
          onError: (err) => {
            const errorMsg = err.message || String(err);
            // Check if it's a rate limit error
            if (errorMsg.toLowerCase().includes('rate limit') || 
                errorMsg.toLowerCase().includes('quota') ||
                errorMsg.includes('429')) {
              setToastMessage(`⚠️ Rate limit hit for ${selectedModel}. Go back and select a different model.`);
              Alert.alert(
                'Rate Limit Exceeded',
                `The model "${selectedModel}" has hit its rate limit. Please go back and select a different model.`,
                [{ text: 'OK' }]
              );
            }
            handleStreamEvent({ type: 'error', data: errorMsg });
          },
        },
        abortControllerRef.current.signal
      );
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        console.error('[Genesis] Stream initialization error:', err);
        setError(err instanceof Error ? err.message : 'Failed to initialize');
        setAiState('alert');
        setIsStreaming(false);
      }
    }
  }, [hrmConfig.enabled, hrmApiPayload, selectedModel, setAiState, setIsStreaming, setSessionId, setCurrentPayload, setCurrentPhase, setHistory, handleStreamEvent, getOrCreateSessionId, storedResponses]);
  
  // Game scheduler setup
  useEffect(() => {
    const scheduler = gameSchedulerRef.current;
    
    // Set up callback for when a game should be triggered
    scheduler.setGameTriggerCallback((definition: GameDefinition) => {
      console.log('[Genesis] Game triggered:', definition.type, definition.difficulty);
      setActiveGame(definition);
      setAiState('alert'); // Visual indicator that something's happening
    });
    
    return () => {
      scheduler.cancel();
    };
  }, [setAiState]);
  
  // Notify scheduler when new content is shown
  useEffect(() => {
    if (currentPayload?.components?.some(c => c.type === 'text' || c.type === 'input')) {
      gameSchedulerRef.current.onQuestionShown(currentPhase);
    }
  }, [currentPayload, currentPhase]);
  
  // Handle game completion
  const handleGameComplete = useCallback(async (partialResult: Omit<GameResult, 'gameId' | 'gameType' | 'timestamp' | 'phase'>) => {
    if (!activeGame) return;
    
    const fullResult: GameResult = {
      ...partialResult,
      gameId: activeGame.id,
      gameType: activeGame.type,
      timestamp: new Date(),
      phase: currentPhase,
    };
    
    // Save to storage
    await saveGameResult(fullResult);
    console.log('[Genesis] Game completed:', fullResult.status, fullResult.reactionTimeMs, 'ms');
    
    // Clear active game after a brief delay to show result
    setTimeout(() => {
      setActiveGame(null);
      setAiState('listening');
    }, 1500);
  }, [activeGame, currentPhase, setAiState]);
  
  // Handle game timeout/dismiss
  const handleGameTimeout = useCallback(() => {
    console.log('[Genesis] Game timed out or dismissed');
    setActiveGame(null);
    setAiState('listening');
  }, [setAiState]);
  
  // Manual game trigger (for testing)
  const triggerTestGame = useCallback(() => {
    gameSchedulerRef.current.forceGame(currentPhase);
  }, [currentPhase]);
  
  const handleInteractionWithStream = useCallback(async (componentIndex: number, value: unknown) => {
    const userResponse = String(value);
    
    // Reset restored flag so next question animates normally
    setIsRestoredSession(false);
    
    // Get current question from payload
    const currentQuestion = currentPayload?.components?.find(c => c.type === 'text')?.content || '';
    
    // Save the response locally
    const newResponse = { question: currentQuestion, response: userResponse, phase: currentPhase };
    const updatedResponses = [...storedResponses, newResponse];
    setStoredResponses(updatedResponses);
    
    // Persist to storage
    await saveSession({ responses: updatedResponses, phase: currentPhase });
    
    setAiState('thinking');
    setIsStreaming(true);
    setStreamingText('');
    
    abortControllerRef.current = new AbortController();
    
    // Build context with all previous responses
    const contextMessage = `User's response to "${currentQuestion}": "${userResponse}"\n\nPrevious conversation:\n${updatedResponses.slice(0, -1).map(r => `Q: ${r.question}\nA: ${r.response}`).join('\n\n')}\n\nGenerate the next penetrating question based on their response.`;
    
    try {
      await apiClient.chatStream(
        {
          message: contextMessage,
          session_id: sessionId || undefined,
          enable_hrm: hrmConfig.enabled,
          hrm_config: hrmApiPayload,
          model: modelConfig.primary, // Primary model for conversation
          models_config: {
            primary: modelConfig.primary,
            fast: modelConfig.fast,
            synthesis: modelConfig.synthesis,
            fallback: modelConfig.fallback,
          },
          enabled_capabilities: enabledModules, // Include enabled modules
        },
        {
          onStart: () => {
            handleStreamEvent({ type: 'start' });
          },
          onToken: (token: string) => {
            handleStreamEvent({ type: 'token', data: token });
          },
          onAgentOutput: (output) => {
            const payload: GenesisPayload = {
              type: 'profiler_step',
              phase: output.calculation?.phase || currentPhase,
              components: output.visualizationData?.components || [],
              interpretationSeed: output.interpretationSeed,
              calculation: output.calculation,
              correlations: output.correlations,
              method: output.method,
              confidence: output.confidence,
              visuals: {
                pulse_color: getPulseColorForPhase(output.calculation?.phase),
                background_intensity: 0.5,
              },
            };
            
            setCurrentPayload(payload);
            
            // Save the new payload to session
            saveSession({ lastPayload: payload, phase: payload.phase });
            
            if (payload.phase && payload.phase !== currentPhase) {
              setCurrentPhase(payload.phase as typeof currentPhase);
            }
            
            const interaction: GenesisInteraction = {
              id: Date.now().toString(),
              type: 'response',
              payload,
              timestamp: new Date(),
              userResponse: String(value),
            };
            setHistory((prev) => [...prev, interaction]);
          },
          onComplete: () => {
            handleStreamEvent({ type: 'end' });
          },
          onError: (err) => {
            const errorMsg = err.message || String(err);
            // Check if it's a rate limit error
            if (errorMsg.toLowerCase().includes('rate limit') || 
                errorMsg.toLowerCase().includes('quota') ||
                errorMsg.includes('429')) {
              setToastMessage(`⚠️ Rate limit hit. Please go back and select a different model.`);
              Alert.alert(
                'Rate Limit Exceeded',
                `The model "${selectedModel}" has hit its rate limit. Please go back and select a different model.`,
                [{ text: 'OK' }]
              );
            }
            handleStreamEvent({ type: 'error', data: errorMsg });
          },
        },
        abortControllerRef.current.signal
      );
    } catch (err) {
      if ((err as Error).name !== 'AbortError') {
        console.error('[Genesis] Stream interaction error:', err);
        setError(err instanceof Error ? err.message : 'Failed to process response');
        setAiState('alert');
        setIsStreaming(false);
      }
    }
  }, [sessionId, hrmConfig.enabled, hrmApiPayload, selectedModel, currentPhase, setAiState, setIsStreaming, setCurrentPayload, setCurrentPhase, setHistory, handleStreamEvent, storedResponses, saveSession]);
  
  // Load session on mount
  useEffect(() => {
    const initSession = async () => {
      setIsLoadingSession(true);
      
      try {
        const existingSession = await loadSession();
        
        if (existingSession) {
          // Restore session state
          setSessionId(existingSession.sessionId);
          setCurrentPhase(existingSession.phase as typeof currentPhase);
          setStoredResponses(existingSession.responses);
          
          // Check if profile is complete based on response count or explicit flag
          const isProfileComplete = existingSession.profileComplete || 
                                    existingSession.responses.length >= COMPLETION_THRESHOLD;
          
          // If profile is complete, always show completion screen regardless of saved payload
          if (isProfileComplete) {
            console.log('[Genesis] Profile complete with', existingSession.responses.length, 'responses - showing completion screen');
            
            // Check if we have a valid completion payload saved
            const hasValidCompletionPayload = existingSession.lastPayload?.components?.some(
              (c: any) => c.type === 'digital_twin_card' || c.type === 'completion_transition'
            );
            
            if (hasValidCompletionPayload) {
              console.log('[Genesis] Using saved completion payload');
              setCurrentPayload(existingSession.lastPayload!);
            } else {
              console.log('[Genesis] Generating completion payload (saved payload missing/invalid)');
              // Pass any saved Digital Twin data if available
              const completionPayload = generateCompletionPayload(
                existingSession.responses, 
                existingSession.digitalTwin
              );
              setCurrentPayload(completionPayload);
              // Save the generated completion payload
              await saveSession({ lastPayload: completionPayload, phase: 'activation', profileComplete: true } as Partial<StoredSession>);
            }
            
            setCurrentPhase('activation');
            hasInitializedRef.current = true;
            setIsRestoredSession(true);
            setIsInitialized(true);
            setAiState('listening');
            setIsLoadingSession(false);
            return;
          }
          
          // If we have a stored payload (and not complete), restore it
          if (existingSession.lastPayload && existingSession.lastPayload.components && existingSession.lastPayload.components.length > 0) {
            console.log('[Genesis] Restoring saved payload with', existingSession.lastPayload.components.length, 'components');
            setCurrentPayload(existingSession.lastPayload);
            hasInitializedRef.current = true; // Mark as initialized to prevent re-fetch
            setIsRestoredSession(true); // Mark as restored to skip animations
            setIsInitialized(true);
            setAiState('listening');
            setIsLoadingSession(false);
            return;
          }
          
          // If we have a payload in memory (from previous navigation), don't re-fetch
          if (currentPayload && currentPayload.components && currentPayload.components.length > 0) {
            console.log('[Genesis] Using in-memory payload');
            hasInitializedRef.current = true;
            setIsRestoredSession(true); // Mark as restored to skip animations
            setIsInitialized(true);
            setIsLoadingSession(false);
            return;
          }
        }
        
        // Only initialize if we haven't already and no stored payload exists
        if (!hasInitializedRef.current) {
          console.log('[Genesis] No stored payload, fetching new question. Responses:', existingSession?.responses?.length || 0);
          // Pass the responses from the loaded session directly (don't rely on state)
          await initializeSessionWithStream(existingSession?.sessionId, existingSession?.responses);
        }
        
        setIsInitialized(true);
      } catch (err) {
        console.error('[Genesis] Session init error:', err);
        setError('Failed to initialize session');
      } finally {
        setIsLoadingSession(false);
      }
    };
    
    initSession();
    
    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, []); // Only run on mount
  
  // Function to reset session (for starting over)
  const resetSession = useCallback(async () => {
    console.log('[Genesis] Resetting session...');
    
    // Cancel any in-flight requests
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
    
    // Reset the initialization guard FIRST
    hasInitializedRef.current = false;
    
    // Clear backend session state FIRST (if we have a session ID)
    if (sessionId) {
      try {
        const result = await apiClient.clearSession(sessionId);
        console.log('[Genesis] Backend session clear result:', result);
      } catch (err) {
        console.warn('[Genesis] Failed to clear backend session:', err);
        // Continue anyway - frontend reset is more important
      }
    }
    
    // Clear storage and wait for it
    try {
      await AsyncStorage.removeItem(GENESIS_SESSION_KEY);
      await AsyncStorage.removeItem(GENESIS_RESPONSES_KEY);
      console.log('[Genesis] Storage cleared successfully');
    } catch (err) {
      console.error('[Genesis] Failed to clear storage:', err);
    }
    
    // Reset all state
    setStoredResponses([]);
    setCurrentPayload(null);
    setCurrentPhase('awakening');
    setIsInitialized(false);
    setIsRestoredSession(false);
    setError(null);
    setAiState('idle');
    setStreamingText('');
    setIsStreaming(false);
    setHistory([]);
    
    // Generate a completely fresh session ID (don't rely on getOrCreateSessionId which might race with storage)
    const freshSessionId = await Crypto.randomUUID();
    setSessionId(freshSessionId);
    console.log('[Genesis] Created fresh session:', freshSessionId);
    
    // Small delay to ensure React state is flushed
    await new Promise(resolve => setTimeout(resolve, 100));
    
    // Re-initialize with the fresh session ID and empty responses
    await initializeSessionWithStream(freshSessionId, []);
  }, [sessionId, initializeSessionWithStream, setCurrentPayload, setSessionId, setCurrentPhase, setAiState, setIsStreaming, setHistory]);

  // Function to save current profile
  const saveProfile = useCallback(async () => {
    if (!sessionId) {
      Alert.alert('Error', 'No active session to save');
      return;
    }

    // Prompt for profile name
    Alert.prompt(
      'Save Profile',
      'Enter a name for this profile:',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Save',
          onPress: async (name) => {
            if (!name?.trim()) {
              Alert.alert('Error', 'Please enter a profile name');
              return;
            }

            try {
              setToastMessage('Saving profile...');
              
              // Build session state from local data as fallback
              // (in case backend session is lost due to server restart)
              const localSessionState = {
                session_id: sessionId,
                phase: currentPhase,
                question_index: storedResponses.length,
                total_questions_asked: storedResponses.length,
                responses: storedResponses.map(r => ({
                  phase: r.phase,
                  question: r.question,
                  response: r.response,
                  timestamp: new Date().toISOString(),
                })),
                profile_complete: currentPhase === 'activation' || 
                  currentPayload?.components?.some(c => c.type === 'digital_twin_card'),
                conversation_turn: storedResponses.length,
              };
              
              // Extract digital twin from current payload if available
              const digitalTwinComp = currentPayload?.components?.find(
                (c: any) => c.type === 'digital_twin_card'
              );
              const localDigitalTwin = digitalTwinComp?.digital_twin 
                ? (digitalTwinComp.digital_twin as Record<string, unknown>) 
                : undefined;
              
              const result = await apiClient.saveProfile(
                sessionId, 
                name.trim(),
                undefined, // slotId - let backend assign
                localSessionState,
                localDigitalTwin
              );
              
              if (result.success) {
                setToastMessage(`Profile saved to ${result.slot_id}`);
                setTimeout(() => setToastMessage(null), 3000);
              } else {
                Alert.alert('Error', result.message);
                setToastMessage(null);
              }
            } catch (err) {
              console.error('[Genesis] Failed to save profile:', err);
              Alert.alert('Error', 'Failed to save profile. Please try again.');
              setToastMessage(null);
            }
          },
        },
      ],
      'plain-text',
      `My Profile ${new Date().toLocaleDateString()}`
    );
  }, [sessionId, currentPhase, storedResponses, currentPayload]);

  // Handle completion - navigate to dashboard
  const handleComplete = useCallback(async () => {
    console.log('[Genesis] Profile complete, navigating to dashboard');
    
    // Auto-save the completed profile before navigating
    try {
      const localSessionState = {
        session_id: sessionId,
        phase: currentPhase,
        responses: storedResponses,
        profile_complete: true,
      };
      
      // Try to extract digital twin from payload
      const digitalTwin = currentPayload?.components?.find(
        (c: any) => c.type === 'digital_twin_card'
      )?.digital_twin;
      
      // Get current profiles and find the next slot number
      const response = await apiClient.listProfiles();
      const usedSlotIds = new Set(response.profiles.map(p => p.slot_id));
      
      // Find next available slot (1-10)
      let slotId = '1';
      for (let i = 1; i <= response.max_slots; i++) {
        if (!usedSlotIds.has(String(i))) {
          slotId = String(i);
          break;
        }
      }
      
      await apiClient.saveProfile(
        sessionId || '',
        'Completed Profile',
        slotId,
        localSessionState,
        digitalTwin as Record<string, unknown> | undefined
      );
      console.log('[Genesis] Profile auto-saved to slot', slotId);
    } catch (err) {
      console.warn('[Genesis] Failed to auto-save profile:', err);
      // Continue anyway - user can save manually later
    }
    
    // Navigate to dashboard/home
    router.replace('/(tabs)');
  }, [sessionId, currentPhase, storedResponses, currentPayload, router]);
  
  const renderContent = () => {
    if (error) {
      return (
        <Animated.View
          entering={FadeIn.duration(600)}
          style={styles.centerContent}
        >
          <Text style={styles.errorText}>⚠ {error}</Text>
          <Text
            style={styles.retryText}
            onPress={() => {
              setError(null);
              setIsInitialized(false);
            }}
          >
            Tap to retry
          </Text>
        </Animated.View>
      );
    }
    
    if ((aiState === 'thinking' || isStreaming) && !currentPayload) {
      return (
        <Animated.View
          entering={FadeIn.duration(600)}
          style={styles.centerContent}
        >
          <Spinner size="large" color="#9333EA" />
          <Text style={styles.thinkingText}>
            {streamingText || 'Awakening the void...'}
          </Text>
        </Animated.View>
      );
    }
    
    if (currentPayload?.components && currentPayload.components.length > 0) {
      const keyValue = String(currentPayload.calculation?.questionIndex ?? 'initial');
      
      // Skip enter animation if this is a restored session to prevent layout shift
      const enterAnimation = isRestoredSession ? undefined : SlideInDown.duration(600);
      
      return (
        <View style={styles.contentContainer}>
          {isStreaming && streamingText && (
            <Animated.View entering={FadeIn} style={styles.streamingOverlay}>
              <Text style={styles.streamingText}>{streamingText}</Text>
            </Animated.View>
          )}
          <Animated.View
            key={keyValue}
            entering={enterAnimation}
            exiting={SlideOutUp.duration(400)}
            style={styles.animatedContent}
          >
            <GenerativeRenderer
              components={currentPayload.components as ComponentDefinition[]}
              onInteract={handleInteractionWithStream}
              onComplete={handleComplete}
              phase={currentPhase}
              skipTransition={isRestoredSession}
            />
          </Animated.View>
        </View>
      );
    }
    
    return (
      <Animated.View
        entering={FadeIn.duration(600)}
        style={styles.centerContent}
      >
        <Text style={styles.welcomeText}>Genesis Profiler</Text>
        <Text style={styles.subtitleText}>Building your Digital Twin</Text>
      </Animated.View>
    );
  };

  // Check if we're on completion screen (has digital_twin_card or completion_transition)
  const isCompletionScreen = currentPayload?.components?.some(
    (c: any) => c.type === 'digital_twin_card' || c.type === 'completion_transition'
  );

  // Show loading state while checking session
  if (isLoadingSession) {
    return (
      <View style={styles.container}>
        <StatusBar style="light" />
        <View style={styles.centerContent}>
          <Spinner size="large" color="#9333EA" />
          <Text style={styles.thinkingText}>Loading session...</Text>
        </View>
      </View>
    );
  }

  // Main content wrapper - Skip TouchableWithoutFeedback on completion screen
  // because it interferes with ScrollView touch handling
  const ContentWrapper = isCompletionScreen 
    ? ({ children }: { children: React.ReactNode }) => <>{children}</>
    : ({ children }: { children: React.ReactNode }) => (
        <TouchableWithoutFeedback onPress={Keyboard.dismiss} accessible={false}>
          {children}
        </TouchableWithoutFeedback>
      );

  return (
    <ContentWrapper>
      <View style={styles.container}>
        <StatusBar style="light" />
        <PulsingBorder>
          <SafeAreaView style={styles.safeArea}>
            <KeyboardAvoidingView
              style={styles.keyboardView}
              behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
              keyboardVerticalOffset={Platform.OS === 'ios' ? 0 : 20}
            >
              <View style={styles.header}>
                <TouchableOpacity 
                  onPress={() => router.back()} 
                  style={styles.backButton}
                  hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                >
                  <Text style={styles.backButtonText}>←</Text>
                </TouchableOpacity>
                
                <Text style={styles.phaseIndicator}>
                  {currentPhase.toUpperCase()}
                </Text>
                
                <View style={styles.headerButtons}>
                  {/* Save Profile Button */}
                  <TouchableOpacity 
                    onPress={saveProfile}
                    style={styles.saveButton}
                    hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                  >
                    <Text style={styles.saveButtonText}>💾</Text>
                  </TouchableOpacity>
                  
                  {/* Reset Button */}
                  <TouchableOpacity 
                    onPress={() => {
                      Alert.alert(
                        'Reset Session?',
                        'This will start the profiling from the beginning. Your current progress will be lost.',
                        [
                          { text: 'Cancel', style: 'cancel' },
                          { text: 'Reset', style: 'destructive', onPress: resetSession },
                        ]
                      );
                    }} 
                    style={styles.resetButton}
                    hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
                  >
                    <Text style={styles.resetButtonText}>↺</Text>
                  </TouchableOpacity>
                </View>
              </View>
              
              {/* Status indicators below header */}
              <View style={styles.statusBar}>
                {aiState === 'thinking' && hrmConfig.enabled && (
                  <Animated.View entering={FadeIn} exiting={FadeOut}>
                    <Text style={styles.stateIndicator}>HRM ACTIVE</Text>
                  </Animated.View>
                )}
                {aiState === 'thinking' && !hrmConfig.enabled && (
                  <Animated.View entering={FadeIn} exiting={FadeOut}>
                    <Text style={[styles.stateIndicator, { color: '#06B6D4' }]}>THINKING...</Text>
                  </Animated.View>
                )}
                {storedResponses.length > 0 && (
                  <Text style={styles.progressText}>
                    {storedResponses.length} response{storedResponses.length !== 1 ? 's' : ''}
                  </Text>
                )}
              </View>
              
              <View style={styles.mainContent}>
                {renderContent()}
              </View>
              
              <View style={styles.footer}>
                <Text style={styles.footerText}>
                  Project Sovereign • v1.0
                </Text>
              </View>
            </KeyboardAvoidingView>
          </SafeAreaView>
        </PulsingBorder>
        
        {/* Game Modal - overlays everything when active */}
        {activeGame && (
          <Modal
            visible={true}
            transparent
            animationType="fade"
            onRequestClose={handleGameTimeout}
          >
            <View style={styles.gameModalOverlay}>
              <View style={styles.gameModalContent}>
                <ReflexTapComponent
                  definition={activeGame}
                  onComplete={handleGameComplete}
                  onTimeout={handleGameTimeout}
                  phase={currentPhase}
                />
              </View>
            </View>
          </Modal>
        )}
      </View>
    </ContentWrapper>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#050505',
  },
  safeArea: {
    flex: 1,
  },
  keyboardView: {
    flex: 1,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  backButton: {
    padding: 8,
    marginLeft: -8,
  },
  backButtonText: {
    color: 'rgba(255, 255, 255, 0.6)',
    fontSize: 24,
    fontWeight: '300',
  },
  headerButtons: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  saveButton: {
    padding: 8,
  },
  saveButtonText: {
    fontSize: 18,
  },
  resetButton: {
    padding: 8,
    marginRight: -8,
  },
  resetButtonText: {
    color: 'rgba(255, 255, 255, 0.4)',
    fontSize: 20,
    fontWeight: '300',
  },
  phaseIndicator: {
    color: 'rgba(255, 255, 255, 0.5)',
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 3,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  statusBar: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: 16,
    paddingBottom: 8,
  },
  stateIndicator: {
    color: '#9333EA',
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 2,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  progressText: {
    color: 'rgba(255, 255, 255, 0.3)',
    fontSize: 10,
    fontWeight: '500',
    letterSpacing: 1,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  mainContent: {
    flex: 1,
  },
  contentContainer: {
    flex: 1,
  },
  animatedContent: {
    flex: 1,
  },
  centerContent: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
  },
  welcomeText: {
    color: 'rgba(255, 255, 255, 0.9)',
    fontSize: 32,
    fontWeight: '200',
    letterSpacing: 4,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  subtitleText: {
    color: 'rgba(255, 255, 255, 0.5)',
    fontSize: 14,
    fontWeight: '400',
    letterSpacing: 2,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  thinkingText: {
    color: 'rgba(255, 255, 255, 0.6)',
    fontSize: 16,
    fontWeight: '300',
    marginTop: 16,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  errorText: {
    color: '#FF4444',
    fontSize: 16,
    fontWeight: '500',
    textAlign: 'center',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  retryText: {
    color: 'rgba(255, 255, 255, 0.5)',
    fontSize: 14,
    textDecorationLine: 'underline',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  footer: {
    paddingVertical: 16,
    alignItems: 'center',
  },
  footerText: {
    color: 'rgba(255, 255, 255, 0.3)',
    fontSize: 10,
    letterSpacing: 2,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  streamingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    padding: 20,
    backgroundColor: 'rgba(5, 5, 5, 0.9)',
    zIndex: 10,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(147, 51, 234, 0.3)',
  },
  streamingText: {
    color: 'rgba(255, 255, 255, 0.8)',
    fontSize: 14,
    fontWeight: '300',
    lineHeight: 22,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  gameModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(5, 5, 5, 0.98)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  gameModalContent: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
  },
});
