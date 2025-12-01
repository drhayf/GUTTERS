/**
 * GlobalAgentShell - The Omnipresent AI Interface
 * 
 * This component provides a floating, always-accessible AI agent interface
 * that can be summoned from anywhere in the app. It integrates with:
 * 
 * - Orchestrator: Routes queries to appropriate agents
 * - Digital Twin: Maintains context about the user
 * - Generative UI: Renders dynamic components
 * - Module System: Only shows relevant capabilities
 * 
 * Features:
 * ━━━━━━━━━━
 * - Floating action button (FAB) for quick access
 * - Expandable chat interface with voice input ready
 * - Context-aware suggestions based on current screen
 * - Smooth animations and sci-fi aesthetic
 * - Keyboard-friendly with proper handling
 * 
 * @module GlobalAgentShell
 */

import React, { useState, useCallback, useRef, useEffect } from 'react';
import {
  View,
  StyleSheet,
  Pressable,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  Keyboard,
  Dimensions,
  ScrollView,
} from 'react-native';
import { Text } from 'tamagui';
import Animated, {
  FadeIn,
  FadeOut,
  SlideInUp,
  SlideOutDown,
  SlideInRight,
  withSpring,
  withTiming,
  withRepeat,
  useSharedValue,
  useAnimatedStyle,
  interpolate,
  Extrapolate,
  runOnJS,
} from 'react-native-reanimated';
import { BlurView } from 'expo-blur';
import { useAtom, useAtomValue, useSetAtom } from 'jotai';
import {
  MessageCircle,
  X,
  Send,
  Mic,
  Sparkles,
  Loader2,
  ChevronUp,
} from '@tamagui/lucide-icons';

import {
  agentVisibleAtom,
  agentActivityAtom,
  updateAgentActivityAtom,
  digitalTwinAtom,
  essenceStatementAtom,
  type GlobalAgentState,
} from '../lib/state/dashboard-atoms';
import { enabledModulesAtom } from '../lib/state/module-preferences-atoms';
import { hrmConfigAtom, hrmApiPayloadAtom } from '../lib/state/hrm-atoms';
import { modelConfigAtom } from '../lib/state/model-config-atoms';
import { apiClient, type SovereignToolCall, type ComponentDefinition as ApiComponentDef } from '../lib/api-client';
import { GenerativeRenderer } from './genesis/GenerativeRenderer';
import type { ComponentDefinition } from '../packages/ui/registry';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');
const FAB_SIZE = 60;
const EXPANDED_HEIGHT = SCREEN_HEIGHT * 0.7;

// ============================================================================
// MINI PULSING BORDER (for small elements, not full-screen)
// ============================================================================

interface MiniPulsingBorderProps {
  color: string;
  intensity?: number;
  style?: any;
  children: React.ReactNode;
}

/**
 * A simple pulsing border for small elements like buttons and avatars.
 * Unlike the full PulsingBorder, this doesn't create a screen-spanning effect.
 */
function MiniPulsingBorder({ color, intensity = 0.5, style, children }: MiniPulsingBorderProps) {
  const pulseValue = useSharedValue(0);
  
  useEffect(() => {
    pulseValue.value = withRepeat(
      withTiming(1, { duration: 2000 }),
      -1,
      true
    );
  }, []);
  
  const animatedStyle = useAnimatedStyle(() => ({
    shadowColor: color,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: interpolate(pulseValue.value, [0, 1], [0.3, 0.8]) * intensity,
    shadowRadius: interpolate(pulseValue.value, [0, 1], [4, 12]),
    elevation: 8,
  }));
  
  return (
    <Animated.View style={[style, animatedStyle]}>
      {children}
    </Animated.View>
  );
}

// ============================================================================
// TYPES
// ============================================================================

interface Message {
  id: string;
  role: 'user' | 'assistant' | 'tool';
  content: string;
  components?: ComponentDefinition[];
  toolCalls?: SovereignToolCall[];
  timestamp: Date;
}

interface QuickSuggestion {
  id: string;
  label: string;
  prompt: string;
  icon: string;
}

// ============================================================================
// QUICK SUGGESTIONS
// ============================================================================

const QUICK_SUGGESTIONS: QuickSuggestion[] = [
  {
    id: 'insight',
    label: 'Give me an insight',
    prompt: 'Share a personalized insight about me based on what you know.',
    icon: '💡',
  },
  {
    id: 'energy',
    label: "Today's energy",
    prompt: 'What should I be aware of about my energy today?',
    icon: '⚡',
  },
  {
    id: 'challenge',
    label: 'Challenge me',
    prompt: 'Give me a meaningful challenge to work on today.',
    icon: '🎯',
  },
  {
    id: 'reflect',
    label: 'Help me reflect',
    prompt: 'Ask me a deep question to help me reflect on my current state.',
    icon: '🪞',
  },
];

// ============================================================================
// COMPONENT
// ============================================================================

interface GlobalAgentShellProps {
  // No props needed - this is a floating overlay component
}

export function GlobalAgentShell(_props: GlobalAgentShellProps = {}) {
  // State
  const [isVisible, setIsVisible] = useAtom(agentVisibleAtom);
  const agentActivity = useAtomValue(agentActivityAtom);
  const updateActivity = useSetAtom(updateAgentActivityAtom);
  const digitalTwin = useAtomValue(digitalTwinAtom);
  const essence = useAtomValue(essenceStatementAtom);
  const enabledModules = useAtomValue(enabledModulesAtom);
  const hrmConfig = useAtomValue(hrmConfigAtom);
  const hrmApiPayload = useAtomValue(hrmApiPayloadAtom);
  const modelConfig = useAtomValue(modelConfigAtom);
  
  // Local state
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [streamingText, setStreamingText] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(true);
  const [pendingToolCalls, setPendingToolCalls] = useState<SovereignToolCall[]>([]);
  const [pendingComponents, setPendingComponents] = useState<ComponentDefinition[]>([]);
  const [sessionId, setSessionId] = useState<string | undefined>();
  
  // Refs
  const inputRef = useRef<TextInput>(null);
  const scrollRef = useRef<ScrollView>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  
  // Animations
  const fabScale = useSharedValue(1);
  const fabRotation = useSharedValue(0);
  
  // FAB animation styles
  const fabAnimatedStyle = useAnimatedStyle(() => ({
    transform: [
      { scale: fabScale.value },
      { rotate: `${fabRotation.value}deg` },
    ],
  }));
  
  // Get pulse color based on agent state
  const getPulseColor = useCallback((state: GlobalAgentState): 'cyan' | 'purple' | 'gold' | 'red' | 'green' => {
    switch (state) {
      case 'listening': return 'cyan';
      case 'processing': return 'purple';
      case 'synthesizing': return 'gold';
      case 'presenting': return 'green';
      default: return 'cyan';
    }
  }, []);
  
  // Toggle visibility
  const handleToggle = useCallback(() => {
    if (isVisible) {
      // Closing
      fabRotation.value = withSpring(0);
      setIsVisible(false);
      Keyboard.dismiss();
    } else {
      // Opening
      fabRotation.value = withSpring(45);
      setIsVisible(true);
      updateActivity({ state: 'ready' });
      setTimeout(() => inputRef.current?.focus(), 300);
    }
  }, [isVisible, setIsVisible, updateActivity, fabRotation]);
  
  // Handle FAB press animation
  const handleFabPressIn = useCallback(() => {
    fabScale.value = withSpring(0.9);
  }, [fabScale]);
  
  const handleFabPressOut = useCallback(() => {
    fabScale.value = withSpring(1);
  }, [fabScale]);
  
  // Send message - Uses Sovereign Agent for omniscient capabilities
  const handleSend = useCallback(async (text?: string) => {
    const messageText = text || inputText.trim();
    if (!messageText || isLoading) return;
    
    // Add user message
    const userMessage: Message = {
      id: `msg_${Date.now()}`,
      role: 'user',
      content: messageText,
      timestamp: new Date(),
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setShowSuggestions(false);
    setIsLoading(true);
    setStreamingText('');
    setPendingToolCalls([]);
    setPendingComponents([]);
    updateActivity({ state: 'processing', currentTask: 'Thinking...' });
    
    // Scroll to bottom
    setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 100);
    
    // Create abort controller
    abortControllerRef.current = new AbortController();
    
    // Collected data during streaming
    let collectedToolCalls: SovereignToolCall[] = [];
    let collectedComponents: ComponentDefinition[] = [];
    let collectedText = '';
    
    try {
      await apiClient.sovereignChatStream(
        {
          message: messageText,
          session_id: sessionId,
          digital_twin: (digitalTwin as unknown) as Record<string, unknown> | undefined,
          enabled_capabilities: enabledModules,
          hrm_config: hrmConfig.enabled ? hrmApiPayload : undefined,
          models_config: {
            primary: modelConfig.primary,
            fast: modelConfig.fast,
            synthesis: modelConfig.synthesis,
            fallback: modelConfig.fallback,
          },
        },
        {
          onStart: () => {
            updateActivity({ state: 'synthesizing', currentTask: 'Consulting knowledge...' });
          },
          
          onToken: (token: string) => {
            collectedText += token;
            setStreamingText(collectedText);
          },
          
          onToolCall: (toolCall: SovereignToolCall) => {
            // Track tool being called
            collectedToolCalls.push(toolCall);
            setPendingToolCalls([...collectedToolCalls]);
            updateActivity({ 
              state: 'processing', 
              currentTask: `Using ${toolCall.tool_name}...` 
            });
          },
          
          onToolResult: (result) => {
            // Update the tool call with its result
            const idx = collectedToolCalls.findIndex(t => t.tool_name === result.tool_name);
            if (idx >= 0) {
              collectedToolCalls[idx] = {
                ...collectedToolCalls[idx],
                result: result.result,
                success: result.success,
                error: result.error,
              };
              setPendingToolCalls([...collectedToolCalls]);
            }
          },
          
          onComponent: (component: ApiComponentDef) => {
            // Collect generative UI components
            collectedComponents.push(component as ComponentDefinition);
            setPendingComponents([...collectedComponents]);
            updateActivity({ state: 'presenting', currentTask: 'Rendering...' });
          },
          
          onComplete: (response) => {
            setIsLoading(false);
            setSessionId(response.session_id);
            
            // Build the final assistant message
            const assistantMessage: Message = {
              id: `msg_${Date.now()}`,
              role: 'assistant',
              content: response.text || collectedText,
              components: collectedComponents.length > 0 
                ? collectedComponents 
                : (response.components as ComponentDefinition[]) || undefined,
              toolCalls: collectedToolCalls.length > 0 
                ? collectedToolCalls 
                : (response.tool_calls as SovereignToolCall[]) || undefined,
              timestamp: new Date(),
            };
            
            setMessages(prev => [...prev, assistantMessage]);
            setStreamingText('');
            setPendingToolCalls([]);
            setPendingComponents([]);
            
            updateActivity({ state: 'presenting' });
            setTimeout(() => updateActivity({ state: 'ready' }), 1000);
          },
          
          onError: (error) => {
            console.error('[Sovereign] Error:', error);
            setIsLoading(false);
            setStreamingText('');
            setPendingToolCalls([]);
            setPendingComponents([]);
            
            const errorMessage: Message = {
              id: `msg_${Date.now()}`,
              role: 'assistant',
              content: 'I encountered an issue processing your request. Please try again.',
              timestamp: new Date(),
            };
            setMessages(prev => [...prev, errorMessage]);
            updateActivity({ state: 'ready' });
          },
        },
        abortControllerRef.current.signal
      );
    } catch (error) {
      console.error('[Sovereign] Exception:', error);
      setIsLoading(false);
      updateActivity({ state: 'ready' });
    }
  }, [
    inputText, 
    isLoading, 
    sessionId,
    digitalTwin,
    hrmConfig,
    hrmApiPayload,
    modelConfig, 
    enabledModules,
    updateActivity,
  ]);
  
  // Handle suggestion tap
  const handleSuggestion = useCallback((suggestion: QuickSuggestion) => {
    handleSend(suggestion.prompt);
  }, [handleSend]);
  
  // Cleanup on unmount
  useEffect(() => {
    return () => {
      abortControllerRef.current?.abort();
    };
  }, []);
  
  return (
    <View style={styles.container} pointerEvents="box-none">
      {/* Expanded Agent Interface */}
      {isVisible && (
        <Animated.View 
          entering={SlideInUp.springify().damping(20)}
          exiting={SlideOutDown.springify().damping(20)}
          style={styles.expandedContainer}
        >
          <BlurView intensity={80} tint="dark" style={styles.blurBackground}>
            <KeyboardAvoidingView
              behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
              style={styles.keyboardAvoid}
            >
              {/* Header */}
              <View style={styles.header}>
                <View style={styles.headerLeft}>
                  <View style={styles.agentIndicator}>
                    <MiniPulsingBorder 
                      color={getPulseColor(agentActivity.state)} 
                      intensity={0.6}
                      style={styles.headerPulse}
                    >
                      <Sparkles size={20} color="#A855F7" />
                    </MiniPulsingBorder>
                  </View>
                  <View style={styles.headerText}>
                    <Text style={styles.headerTitle}>Sovereign</Text>
                    <Text style={styles.headerSubtitle}>
                      {agentActivity.currentTask || 'Ready to assist'}
                    </Text>
                  </View>
                </View>
                
                <Pressable style={styles.closeButton} onPress={handleToggle}>
                  <X size={24} color="rgba(255,255,255,0.7)" />
                </Pressable>
              </View>
              
              {/* Essence Banner */}
              {digitalTwin && (
                <View style={styles.essenceBanner}>
                  <Text style={styles.essenceText}>✨ {essence}</Text>
                </View>
              )}
              
              {/* Messages */}
              <ScrollView
                ref={scrollRef}
                style={styles.messagesContainer}
                contentContainerStyle={styles.messagesContent}
                showsVerticalScrollIndicator={false}
                keyboardShouldPersistTaps="handled"
              >
                {/* Quick Suggestions */}
                {showSuggestions && messages.length === 0 && (
                  <View style={styles.suggestionsContainer}>
                    <Text style={styles.suggestionsTitle}>Quick Actions</Text>
                    <View style={styles.suggestionsGrid}>
                      {QUICK_SUGGESTIONS.map(suggestion => (
                        <Pressable
                          key={suggestion.id}
                          style={styles.suggestionCard}
                          onPress={() => handleSuggestion(suggestion)}
                        >
                          <Text style={styles.suggestionIcon}>{suggestion.icon}</Text>
                          <Text style={styles.suggestionLabel}>{suggestion.label}</Text>
                        </Pressable>
                      ))}
                    </View>
                  </View>
                )}
                
                {/* Message List */}
                {messages.map(message => (
                  <Animated.View
                    key={message.id}
                    entering={FadeIn.duration(300)}
                    style={[
                      styles.messageContainer,
                      message.role === 'user' ? styles.userMessage : styles.assistantMessage,
                    ]}
                  >
                    {message.role === 'assistant' && (
                      <View style={styles.assistantAvatar}>
                        <Sparkles size={16} color="#A855F7" />
                      </View>
                    )}
                    <View style={[
                      styles.messageBubble,
                      message.role === 'user' ? styles.userBubble : styles.assistantBubble,
                    ]}>
                      {/* Tool calls indicator */}
                      {message.toolCalls && message.toolCalls.length > 0 && (
                        <View style={styles.toolCallsContainer}>
                          {message.toolCalls.map((tc, idx) => (
                            <View key={idx} style={styles.toolCallBadge}>
                              <Text style={styles.toolCallText}>
                                🔧 {tc.tool_name.replace(/_/g, ' ')}
                                {tc.success === false && ' ❌'}
                                {tc.success === true && ' ✓'}
                              </Text>
                            </View>
                          ))}
                        </View>
                      )}
                      
                      <Text style={[
                        styles.messageText,
                        message.role === 'user' && styles.userMessageText,
                      ]}>
                        {message.content}
                      </Text>
                      
                      {/* Render generative components */}
                      {message.components && message.components.length > 0 && (
                        <View style={styles.componentsContainer}>
                          <GenerativeRenderer
                            components={message.components}
                            phase="synthesis"
                            onInteract={() => {}}
                          />
                        </View>
                      )}
                    </View>
                  </Animated.View>
                ))}
                
                {/* Pending tool calls during streaming */}
                {pendingToolCalls.length > 0 && isLoading && (
                  <View style={[styles.messageContainer, styles.assistantMessage]}>
                    <View style={styles.assistantAvatar}>
                      <Loader2 size={16} color="#A855F7" />
                    </View>
                    <View style={[styles.messageBubble, styles.assistantBubble]}>
                      <View style={styles.toolCallsContainer}>
                        {pendingToolCalls.map((tc, idx) => (
                          <View key={idx} style={[styles.toolCallBadge, styles.toolCallActive]}>
                            <Text style={styles.toolCallText}>
                              ⚙️ {tc.tool_name.replace(/_/g, ' ')}...
                            </Text>
                          </View>
                        ))}
                      </View>
                    </View>
                  </View>
                )}
                
                {/* Streaming text */}
                {streamingText && (
                  <View style={[styles.messageContainer, styles.assistantMessage]}>
                    <View style={styles.assistantAvatar}>
                      <Sparkles size={16} color="#A855F7" />
                    </View>
                    <View style={[styles.messageBubble, styles.assistantBubble]}>
                      <Text style={styles.messageText}>{streamingText}</Text>
                    </View>
                  </View>
                )}
                
                {/* Loading indicator */}
                {isLoading && !streamingText && (
                  <View style={[styles.messageContainer, styles.assistantMessage]}>
                    <View style={styles.assistantAvatar}>
                      <Loader2 size={16} color="#A855F7" />
                    </View>
                    <View style={[styles.messageBubble, styles.assistantBubble]}>
                      <View style={styles.typingIndicator}>
                        <View style={[styles.typingDot, styles.typingDot1]} />
                        <View style={[styles.typingDot, styles.typingDot2]} />
                        <View style={[styles.typingDot, styles.typingDot3]} />
                      </View>
                    </View>
                  </View>
                )}
              </ScrollView>
              
              {/* Input Area */}
              <View style={styles.inputContainer}>
                <View style={styles.inputWrapper}>
                  <TextInput
                    ref={inputRef}
                    style={styles.textInput}
                    placeholder="Ask me anything..."
                    placeholderTextColor="rgba(255,255,255,0.4)"
                    value={inputText}
                    onChangeText={setInputText}
                    onSubmitEditing={() => handleSend()}
                    returnKeyType="send"
                    multiline
                    maxLength={1000}
                    editable={!isLoading}
                  />
                  
                  <View style={styles.inputActions}>
                    {/* Voice button (future) */}
                    <Pressable style={styles.inputButton} disabled>
                      <Mic size={20} color="rgba(255,255,255,0.3)" />
                    </Pressable>
                    
                    {/* Send button */}
                    <Pressable
                      style={[
                        styles.sendButton,
                        (!inputText.trim() || isLoading) && styles.sendButtonDisabled,
                      ]}
                      onPress={() => handleSend()}
                      disabled={!inputText.trim() || isLoading}
                    >
                      <Send size={18} color={inputText.trim() && !isLoading ? '#FFFFFF' : 'rgba(255,255,255,0.3)'} />
                    </Pressable>
                  </View>
                </View>
              </View>
            </KeyboardAvoidingView>
          </BlurView>
        </Animated.View>
      )}
      
      {/* Floating Action Button */}
      {!isVisible && (
        <Animated.View style={[styles.fabContainer, fabAnimatedStyle]}>
          <Pressable
            onPress={handleToggle}
            onPressIn={handleFabPressIn}
            onPressOut={handleFabPressOut}
          >
            <MiniPulsingBorder 
              color={getPulseColor(agentActivity.state)} 
              intensity={0.5}
              style={styles.fab}
            >
              <View style={styles.fabInner}>
                <MessageCircle size={28} color="#FFFFFF" />
              </View>
            </MiniPulsingBorder>
          </Pressable>
        </Animated.View>
      )}
    </View>
  );
}

// ============================================================================
// STYLES
// ============================================================================

const styles = StyleSheet.create({
  // Root container - must NOT take up layout space, only overlay
  container: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    pointerEvents: 'box-none', // Allow touches to pass through to content below
  },
  
  // FAB
  fabContainer: {
    position: 'absolute',
    right: 20,
    bottom: Platform.OS === 'ios' ? 100 : 80,
    zIndex: 1000,
    pointerEvents: 'auto', // FAB should capture touches
  },
  fab: {
    width: FAB_SIZE,
    height: FAB_SIZE,
    borderRadius: FAB_SIZE / 2,
    overflow: 'hidden',
  },
  fabInner: {
    width: '100%',
    height: '100%',
    backgroundColor: '#A855F7',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: FAB_SIZE / 2,
  },
  
  // Expanded Container
  expandedContainer: {
    position: 'absolute',
    left: 0,
    right: 0,
    bottom: 0,
    height: EXPANDED_HEIGHT,
    zIndex: 1001,
    pointerEvents: 'auto', // Capture all touches when expanded
  },
  blurBackground: {
    flex: 1,
    borderTopLeftRadius: 24,
    borderTopRightRadius: 24,
    overflow: 'hidden',
  },
  keyboardAvoid: {
    flex: 1,
  },
  
  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingTop: 16,
    paddingBottom: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.1)',
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  agentIndicator: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerPulse: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(168, 85, 247, 0.2)',
  },
  headerText: {
    gap: 2,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  headerSubtitle: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.5)',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  closeButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255,255,255,0.1)',
  },
  
  // Essence Banner
  essenceBanner: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    backgroundColor: 'rgba(168, 85, 247, 0.1)',
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(168, 85, 247, 0.2)',
  },
  essenceText: {
    fontSize: 13,
    color: '#A855F7',
    fontStyle: 'italic',
    textAlign: 'center',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  
  // Messages
  messagesContainer: {
    flex: 1,
  },
  messagesContent: {
    paddingHorizontal: 16,
    paddingVertical: 16,
    gap: 12,
  },
  messageContainer: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 8,
  },
  userMessage: {
    justifyContent: 'flex-end',
  },
  assistantMessage: {
    justifyContent: 'flex-start',
  },
  assistantAvatar: {
    width: 28,
    height: 28,
    borderRadius: 14,
    backgroundColor: 'rgba(168, 85, 247, 0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  messageBubble: {
    maxWidth: '80%',
    paddingHorizontal: 14,
    paddingVertical: 10,
    borderRadius: 16,
  },
  userBubble: {
    backgroundColor: '#A855F7',
    borderBottomRightRadius: 4,
  },
  assistantBubble: {
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderBottomLeftRadius: 4,
  },
  messageText: {
    fontSize: 15,
    color: 'rgba(255,255,255,0.9)',
    lineHeight: 22,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  userMessageText: {
    color: '#FFFFFF',
  },
  componentsContainer: {
    marginTop: 12,
  },
  
  // Tool Calls
  toolCallsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 6,
    marginBottom: 8,
  },
  toolCallBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    backgroundColor: 'rgba(34, 211, 238, 0.15)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(34, 211, 238, 0.3)',
  },
  toolCallActive: {
    backgroundColor: 'rgba(168, 85, 247, 0.2)',
    borderColor: 'rgba(168, 85, 247, 0.4)',
  },
  toolCallText: {
    fontSize: 11,
    color: 'rgba(255,255,255,0.7)',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  
  // Typing Indicator
  typingIndicator: {
    flexDirection: 'row',
    gap: 4,
    paddingVertical: 4,
  },
  typingDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: 'rgba(255,255,255,0.5)',
  },
  typingDot1: {
    opacity: 0.4,
  },
  typingDot2: {
    opacity: 0.6,
  },
  typingDot3: {
    opacity: 0.8,
  },
  
  // Suggestions
  suggestionsContainer: {
    gap: 12,
    marginBottom: 20,
  },
  suggestionsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: 'rgba(255,255,255,0.5)',
    textAlign: 'center',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  suggestionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 10,
    justifyContent: 'center',
  },
  suggestionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    paddingHorizontal: 14,
    paddingVertical: 10,
    backgroundColor: 'rgba(255,255,255,0.08)',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
  },
  suggestionIcon: {
    fontSize: 16,
  },
  suggestionLabel: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.8)',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  
  // Input
  inputContainer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.1)',
    backgroundColor: 'rgba(0,0,0,0.3)',
  },
  inputWrapper: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 24,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.15)',
    paddingLeft: 16,
    paddingRight: 6,
    paddingVertical: 6,
  },
  textInput: {
    flex: 1,
    fontSize: 15,
    color: '#FFFFFF',
    maxHeight: 100,
    paddingVertical: 8,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  inputActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  inputButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  sendButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#A855F7',
  },
  sendButtonDisabled: {
    backgroundColor: 'rgba(255,255,255,0.1)',
  },
});
