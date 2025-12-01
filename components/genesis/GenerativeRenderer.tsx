import React, { useState, useRef, useEffect, useCallback } from 'react';
import { 
  StyleSheet, 
  Pressable, 
  Platform, 
  View, 
  TextInput,
  Keyboard,
  Dimensions,
  Modal,
  ScrollView,
} from 'react-native';
import { Text } from 'tamagui';
import Animated, {
  FadeIn,
  FadeOut,
  SlideInUp,
  SlideInRight,
  useAnimatedStyle,
  useSharedValue,
  withTiming,
  withSpring,
  withSequence,
  withRepeat,
  interpolate,
  Easing,
  runOnJS,
} from 'react-native-reanimated';
import type { 
  ComponentDefinition, 
  DigitalTwinData, 
  ActivationStep,
  EnergeticSignature,
  PsychologicalProfile,
} from '../../packages/ui/registry';
import { ReflexTapComponent } from './ReflexTapComponent';
import type { GameResult, GameDefinition, GameDifficulty } from '../../lib/games/types';
import { saveGameResult } from '../../lib/games/storage';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface GenerativeRendererProps {
  components: ComponentDefinition[];
  onInteract: (componentIndex: number, value: unknown) => void;
  onComplete?: () => void; // Called when user clicks "Continue" on completion screen
  phase?: string;
  skipTransition?: boolean; // Skip completion transition animation (for restored sessions)
}

// Phase color schemes - subtle and sophisticated
const phaseThemes: Record<string, { primary: string; secondary: string; accent: string }> = {
  awakening: { primary: '#A855F7', secondary: '#7C3AED', accent: '#C084FC' },
  excavation: { primary: '#F59E0B', secondary: '#D97706', accent: '#FBBF24' },
  mapping: { primary: '#06B6D4', secondary: '#0891B2', accent: '#22D3EE' },
  synthesis: { primary: '#8B5CF6', secondary: '#7C3AED', accent: '#A78BFA' },
  activation: { primary: '#EF4444', secondary: '#DC2626', accent: '#F87171' },
};

// ============================================================================
// SLEEK PROGRESS INDICATOR
// ============================================================================
interface ProgressIndicatorProps {
  current: number;
  total: number;
  phase: string;
}

function ProgressIndicator({ current, total, phase }: ProgressIndicatorProps) {
  const progress = useSharedValue(0);
  const theme = phaseThemes[phase] || phaseThemes.awakening;
  
  useEffect(() => {
    progress.value = withTiming((current / total) * 100, { 
      duration: 800, 
      easing: Easing.bezier(0.25, 0.1, 0.25, 1) 
    });
  }, [current, total]);
  
  const progressStyle = useAnimatedStyle(() => ({
    width: `${progress.value}%`,
  }));
  
  return (
    <View style={styles.progressContainer}>
      <View style={styles.progressHeader}>
        <Text style={[styles.phaseLabel, { color: theme.accent }]}>
          {phase.toUpperCase()}
        </Text>
        <Text style={styles.progressCount}>
          {current} of {total}
        </Text>
      </View>
      <View style={styles.progressTrack}>
        <Animated.View 
          style={[
            styles.progressFill, 
            progressStyle,
            { backgroundColor: theme.primary }
          ]} 
        />
      </View>
    </View>
  );
}

// ============================================================================
// ELEGANT QUESTION DISPLAY
// ============================================================================
interface QuestionDisplayProps {
  content: string;
  variant?: string;
}

function QuestionDisplay({ content, variant }: QuestionDisplayProps) {
  const getStyle = () => {
    switch (variant) {
      case 'insight':
        return styles.insightText;
      case 'label':
        return styles.labelText;
      default:
        return styles.questionText;
    }
  };
  
  return (
    <Animated.View 
      entering={FadeIn.duration(600)} 
      style={styles.questionContainer}
    >
      <Text style={getStyle()}>{content}</Text>
    </Animated.View>
  );
}

// ============================================================================
// PREMIUM INPUT FIELD
// ============================================================================
interface PremiumInputProps {
  placeholder?: string;
  minLength?: number;
  onSubmit: (value: string) => void;
  phase?: string;
}

function PremiumInput({ placeholder, minLength = 0, onSubmit, phase }: PremiumInputProps) {
  const [value, setValue] = useState('');
  const [isFocused, setIsFocused] = useState(false);
  const inputRef = useRef<TextInput>(null);
  const theme = phaseThemes[phase || 'awakening'] || phaseThemes.awakening;
  
  const focusAnimation = useSharedValue(0);
  const characterProgress = useSharedValue(0);
  
  useEffect(() => {
    focusAnimation.value = withSpring(isFocused ? 1 : 0, { damping: 15 });
  }, [isFocused]);
  
  useEffect(() => {
    const targetProgress = minLength > 0 ? Math.min(value.length / minLength, 1) : 1;
    characterProgress.value = withTiming(targetProgress, { duration: 200 });
  }, [value, minLength]);
  
  const isValid = value.length >= minLength;
  const remainingChars = Math.max(0, minLength - value.length);
  
  const handleSubmit = () => {
    if (isValid) {
      Keyboard.dismiss();
      onSubmit(value);
      setValue('');
    }
  };
  
  const containerStyle = useAnimatedStyle(() => ({
    borderColor: `rgba(${isFocused ? '168, 85, 247' : '255, 255, 255'}, ${interpolate(focusAnimation.value, [0, 1], [0.1, 0.3])})`,
  }));
  
  const progressBarStyle = useAnimatedStyle(() => ({
    width: `${characterProgress.value * 100}%`,
    backgroundColor: isValid ? theme.primary : 'rgba(255, 255, 255, 0.3)',
  }));
  
  return (
    <View style={styles.inputWrapper}>
      <Animated.View style={[styles.inputOuterContainer, containerStyle]}>
        <TextInput
          ref={inputRef}
          style={styles.premiumInput}
          multiline
          value={value}
          onChangeText={setValue}
          placeholder={placeholder || 'Share your thoughts...'}
          placeholderTextColor="rgba(255, 255, 255, 0.25)"
          onFocus={() => setIsFocused(true)}
          onBlur={() => setIsFocused(false)}
          selectionColor={theme.accent}
          keyboardAppearance="dark"
        />
        
        {/* Character progress bar at bottom of input */}
        <View style={styles.inputProgressTrack}>
          <Animated.View style={[styles.inputProgressFill, progressBarStyle]} />
        </View>
      </Animated.View>
      
      {/* Submit area */}
      <View style={styles.submitArea}>
        <Text style={styles.charCounter}>
          {remainingChars > 0 ? `${remainingChars} more` : '✓'}
        </Text>
        
        <Pressable
          onPress={handleSubmit}
          disabled={!isValid}
          style={({ pressed }) => [
            styles.submitButton,
            isValid && styles.submitButtonActive,
            isValid && { backgroundColor: theme.primary },
            pressed && isValid && styles.submitButtonPressed,
          ]}
        >
          <Text style={[
            styles.submitButtonText,
            !isValid && styles.submitButtonTextDisabled,
          ]}>
            {isValid ? 'Continue →' : '...'}
          </Text>
        </Pressable>
      </View>
    </View>
  );
}

// ============================================================================
// CHOICE CARDS
// ============================================================================
interface ChoiceCardsProps {
  options: string[];
  onSelect: (option: string) => void;
  phase?: string;
}

function ChoiceCards({ options, onSelect, phase }: ChoiceCardsProps) {
  const theme = phaseThemes[phase || 'awakening'] || phaseThemes.awakening;
  
  return (
    <View style={styles.choiceContainer}>
      {options.map((option, index) => (
        <Animated.View
          key={option}
          entering={FadeIn.duration(400).delay(index * 100)}
          style={styles.choiceCardWrapper}
        >
          <Pressable
            onPress={() => onSelect(option)}
            style={({ pressed }) => [
              styles.choiceCard,
              pressed && [styles.choiceCardPressed, { borderColor: theme.primary }],
            ]}
          >
            <Text style={styles.choiceText}>{option}</Text>
          </Pressable>
        </Animated.View>
      ))}
    </View>
  );
}

// ============================================================================
// REFLEX GAME WRAPPER
// ============================================================================
interface ReflexGameWrapperProps {
  definition: ComponentDefinition;
  phase?: string;
  onComplete: (result: GameResult) => void;
}

function ReflexGameWrapper({ definition, phase, onComplete }: ReflexGameWrapperProps) {
  const [showGame, setShowGame] = useState(true);
  
  const gameDefinition: GameDefinition = {
    type: 'reflex_tap',
    id: `reflex_${Date.now()}`,
    difficulty: ((definition as any).difficulty || 'medium') as GameDifficulty,
    timeoutMs: (definition as any).timeoutMs || 3000,
    config: (definition as any).config || {},
  };
  
  const handleComplete = useCallback(async (partialResult: Omit<GameResult, 'gameId' | 'gameType' | 'timestamp' | 'phase'>) => {
    const fullResult: GameResult = {
      ...partialResult,
      gameId: gameDefinition.id,
      gameType: 'reflex_tap',
      timestamp: new Date(),
      phase: phase || 'unknown',
    };
    await saveGameResult(fullResult);
    onComplete(fullResult);
    setTimeout(() => setShowGame(false), 1500);
  }, [phase, onComplete, gameDefinition.id]);
  
  if (!showGame) return null;
  
  return (
    <Modal visible={showGame} transparent animationType="fade">
      <View style={styles.gameModalOverlay}>
        <ReflexTapComponent
          definition={gameDefinition}
          onComplete={handleComplete}
          onTimeout={() => setShowGame(false)}
          phase={phase}
        />
      </View>
    </Modal>
  );
}

// ============================================================================
// SLIDER COMPONENT
// ============================================================================
interface SliderComponentProps {
  min?: number;
  max?: number;
  step?: number;
  labels?: Record<string, string>;
  onSelect: (value: number) => void;
  phase?: string;
}

function SliderComponent({ min = 1, max = 10, step = 1, labels, onSelect, phase }: SliderComponentProps) {
  const [value, setValue] = useState(Math.floor((min + max) / 2));
  const theme = phaseThemes[phase || 'awakening'] || phaseThemes.awakening;
  
  const handleChange = (newValue: number) => {
    setValue(newValue);
  };
  
  const handleConfirm = () => {
    onSelect(value);
  };
  
  // Generate tick marks
  const ticks: number[] = [];
  for (let i = min; i <= max; i += step) {
    ticks.push(i);
  }
  
  return (
    <View style={styles.sliderContainer}>
      {/* Labels */}
      {labels && (
        <View style={styles.sliderLabels}>
          <Text style={styles.sliderLabel}>{labels[String(min)] || String(min)}</Text>
          <Text style={styles.sliderLabel}>{labels[String(max)] || String(max)}</Text>
        </View>
      )}
      
      {/* Tick marks with selection */}
      <View style={styles.sliderTrack}>
        {ticks.map((tick) => (
          <Pressable
            key={tick}
            onPress={() => handleChange(tick)}
            style={[
              styles.sliderTick,
              tick === value && [styles.sliderTickSelected, { backgroundColor: theme.primary }],
            ]}
          >
            <Text style={[
              styles.sliderTickLabel,
              tick === value && styles.sliderTickLabelSelected,
            ]}>
              {tick}
            </Text>
          </Pressable>
        ))}
      </View>
      
      {/* Confirm button */}
      <Pressable
        onPress={handleConfirm}
        style={[styles.sliderConfirm, { backgroundColor: theme.primary }]}
      >
        <Text style={styles.sliderConfirmText}>Confirm</Text>
      </Pressable>
    </View>
  );
}

// ============================================================================
// CARD SELECTION COMPONENT
// ============================================================================
interface CardSelectionProps {
  cards: Array<{ title: string; value: string; description?: string }>;
  maxSelections?: number;
  onSelect: (values: string[]) => void;
  phase?: string;
}

function CardSelection({ cards, maxSelections = 1, onSelect, phase }: CardSelectionProps) {
  const [selected, setSelected] = useState<string[]>([]);
  const theme = phaseThemes[phase || 'awakening'] || phaseThemes.awakening;
  
  const handleToggle = (value: string) => {
    setSelected(prev => {
      if (prev.includes(value)) {
        return prev.filter(v => v !== value);
      } else if (maxSelections === 1) {
        return [value];
      } else if (prev.length < maxSelections) {
        return [...prev, value];
      }
      return prev;
    });
  };
  
  const handleConfirm = () => {
    if (selected.length > 0) {
      onSelect(selected);
    }
  };
  
  return (
    <View style={styles.cardSelectionContainer}>
      <View style={styles.cardsGrid}>
        {cards.map((card, index) => (
          <Animated.View
            key={card.value}
            entering={FadeIn.duration(400).delay(index * 100)}
          >
            <Pressable
              onPress={() => handleToggle(card.value)}
              style={[
                styles.selectionCard,
                selected.includes(card.value) && [
                  styles.selectionCardSelected,
                  { borderColor: theme.primary, backgroundColor: `${theme.primary}22` }
                ],
              ]}
            >
              <Text style={[
                styles.selectionCardTitle,
                selected.includes(card.value) && { color: theme.accent },
              ]}>
                {card.title}
              </Text>
              {card.description && (
                <Text style={styles.selectionCardDesc}>{card.description}</Text>
              )}
            </Pressable>
          </Animated.View>
        ))}
      </View>
      
      {selected.length > 0 && (
        <Pressable
          onPress={handleConfirm}
          style={[styles.cardConfirmButton, { backgroundColor: theme.primary }]}
        >
          <Text style={styles.cardConfirmText}>Continue →</Text>
        </Pressable>
      )}
    </View>
  );
}

// ============================================================================
// DIGITAL TWIN CARD - Displays the completed profile
// ============================================================================
interface DigitalTwinCardProps {
  digitalTwin: DigitalTwinData;
  phase?: string;
  onContinue?: () => void;
}

function DigitalTwinCard({ digitalTwin, phase, onContinue }: DigitalTwinCardProps) {
  const theme = phaseThemes[phase || 'activation'] || phaseThemes.activation;
  const pulseAnim = useSharedValue(0);
  
  useEffect(() => {
    pulseAnim.value = withRepeat(
      withSequence(
        withTiming(1, { duration: 1500, easing: Easing.inOut(Easing.ease) }),
        withTiming(0, { duration: 1500, easing: Easing.inOut(Easing.ease) })
      ),
      -1,
      false
    );
  }, []);
  
  const glowStyle = useAnimatedStyle(() => ({
    shadowOpacity: interpolate(pulseAnim.value, [0, 1], [0.3, 0.7]),
    shadowRadius: interpolate(pulseAnim.value, [0, 1], [10, 25]),
  }));
  
  const { energetic_signature, psychological_profile, archetypes, summary } = digitalTwin;
  
  return (
    <Animated.View 
      entering={FadeIn.duration(800)} 
      style={[styles.twinCard, glowStyle, { shadowColor: theme.primary }]}
    >
      {/* Header with HD Type */}
      <View style={styles.twinHeader}>
        <Text style={[styles.twinTypeEmoji]}>
          {getHDTypeEmoji(energetic_signature?.hd_type)}
        </Text>
        <View style={styles.twinHeaderText}>
          <Text style={[styles.twinType, { color: theme.accent }]}>
            {energetic_signature?.hd_type || 'Unknown Type'}
          </Text>
          <Text style={styles.twinProfile}>
            {energetic_signature?.hd_profile || 'Profile Pending'}
          </Text>
        </View>
      </View>
      
      {/* Summary Message */}
      {summary && (
        <View style={styles.twinSummary}>
          <Text style={styles.twinSummaryText}>"{summary}"</Text>
        </View>
      )}
      
      {/* Key Insights Grid */}
      <View style={styles.twinInsightsGrid}>
        {/* Strategy */}
        <View style={styles.twinInsightItem}>
          <Text style={styles.twinInsightLabel}>Strategy</Text>
          <Text style={[styles.twinInsightValue, { color: theme.accent }]}>
            {energetic_signature?.hd_strategy || '—'}
          </Text>
        </View>
        
        {/* Authority */}
        <View style={styles.twinInsightItem}>
          <Text style={styles.twinInsightLabel}>Authority</Text>
          <Text style={[styles.twinInsightValue, { color: theme.accent }]}>
            {energetic_signature?.hd_authority || '—'}
          </Text>
        </View>
        
        {/* Cognitive Style */}
        {psychological_profile?.cognitive_style && (
          <View style={styles.twinInsightItem}>
            <Text style={styles.twinInsightLabel}>Cognition</Text>
            <Text style={[styles.twinInsightValue, { color: theme.accent }]}>
              {psychological_profile.cognitive_style}
            </Text>
          </View>
        )}
        
        {/* Primary Archetype */}
        {archetypes?.primary_archetypes?.[0] && (
          <View style={styles.twinInsightItem}>
            <Text style={styles.twinInsightLabel}>Archetype</Text>
            <Text style={[styles.twinInsightValue, { color: theme.accent }]}>
              {archetypes.primary_archetypes[0]}
            </Text>
          </View>
        )}
      </View>
      
      {/* Completion indicator */}
      <View style={styles.twinFooter}>
        <View style={[styles.completionBadge, { backgroundColor: `${theme.primary}33` }]}>
          <Text style={[styles.completionText, { color: theme.accent }]}>
            ✓ Digital Twin Complete
          </Text>
        </View>
      </View>
    </Animated.View>
  );
}

// Helper: Get emoji for HD type
function getHDTypeEmoji(hdType?: string): string {
  const typeMap: Record<string, string> = {
    'Generator': '⚡',
    'Manifesting Generator': '🔥',
    'Projector': '🎯',
    'Manifestor': '⚔️',
    'Reflector': '🌙',
  };
  return typeMap[hdType || ''] || '✨';
}

// ============================================================================
// ACTIVATION STEPS - Personalized action items
// ============================================================================
interface ActivationStepsProps {
  steps: ActivationStep[];
  phase?: string;
  onStepSelect?: (step: ActivationStep) => void;
}

function ActivationSteps({ steps, phase, onStepSelect }: ActivationStepsProps) {
  const theme = phaseThemes[phase || 'activation'] || phaseThemes.activation;
  
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return '#EF4444';
      case 'medium': return '#F59E0B';
      case 'low': return '#10B981';
      default: return theme.accent;
    }
  };
  
  return (
    <View style={styles.stepsContainer}>
      <Text style={styles.stepsTitle}>Your First Steps</Text>
      <Text style={styles.stepsSubtitle}>
        Personalized actions based on your profile
      </Text>
      
      <View style={styles.stepsList}>
        {steps.map((step, index) => (
          <Animated.View
            key={step.id}
            entering={SlideInRight.duration(400).delay(index * 150)}
          >
            <View style={styles.stepCard}>
              <View style={styles.stepIconContainer}>
                <Text style={styles.stepIcon}>{step.icon || '→'}</Text>
              </View>
              
              <View style={styles.stepContent}>
                <View style={styles.stepHeader}>
                  <Text style={styles.stepTitle}>{step.title}</Text>
                  <View style={[
                    styles.priorityBadge,
                    { backgroundColor: `${getPriorityColor(step.priority)}22` }
                  ]}>
                    <Text style={[
                      styles.priorityText,
                      { color: getPriorityColor(step.priority) }
                    ]}>
                      {step.priority}
                    </Text>
                  </View>
                </View>
                
                <Text style={styles.stepDescription}>{step.description}</Text>
                
                <View style={styles.stepMeta}>
                  <Text style={styles.stepCategory}>{step.category}</Text>
                  {step.estimated_time && (
                    <Text style={styles.stepTime}>⏱ {step.estimated_time}</Text>
                  )}
                </View>
              </View>
            </View>
          </Animated.View>
        ))}
      </View>
    </View>
  );
}

// ============================================================================
// COMPLETION TRANSITION - Animated celebration
// ============================================================================
interface CompletionTransitionProps {
  type?: 'dissolve' | 'expand' | 'reveal';
  phase?: string;
  onComplete?: () => void;
}

function CompletionTransition({ type = 'reveal', phase, onComplete }: CompletionTransitionProps) {
  const theme = phaseThemes[phase || 'activation'] || phaseThemes.activation;
  const scale = useSharedValue(0);
  const opacity = useSharedValue(1);
  const ringScale = useSharedValue(0);
  
  useEffect(() => {
    // Expanding ring effect
    ringScale.value = withSequence(
      withTiming(0, { duration: 0 }),
      withTiming(3, { duration: 1500, easing: Easing.out(Easing.cubic) })
    );
    
    // Center circle pulse
    scale.value = withSequence(
      withSpring(1.2, { damping: 8 }),
      withSpring(1, { damping: 12 })
    );
    
    // Fade out after animation - use setTimeout to safely call onComplete
    const timeout = setTimeout(() => {
      opacity.value = withTiming(0, { duration: 500 }, (finished) => {
        'worklet';
        if (finished && onComplete) {
          runOnJS(onComplete)();
        }
      });
    }, 2000);
    
    return () => clearTimeout(timeout);
  }, []);
  
  const circleStyle = useAnimatedStyle(() => ({
    transform: [{ scale: scale.value }],
    opacity: opacity.value,
  }));
  
  const ringStyle = useAnimatedStyle(() => ({
    transform: [{ scale: ringScale.value }],
    opacity: interpolate(ringScale.value, [0, 1, 3], [0.8, 0.3, 0]),
  }));
  
  return (
    <View style={styles.transitionContainer}>
      {/* Expanding ring */}
      <Animated.View style={[
        styles.transitionRing,
        ringStyle,
        { borderColor: theme.primary }
      ]} />
      
      {/* Center content */}
      <Animated.View style={[styles.transitionCenter, circleStyle]}>
        <Text style={styles.transitionEmoji}>✨</Text>
        <Text style={[styles.transitionTitle, { color: theme.accent }]}>
          Profile Complete
        </Text>
        <Text style={styles.transitionSubtitle}>
          Your Digital Twin awaits
        </Text>
      </Animated.View>
    </View>
  );
}

// ============================================================================
// MAIN RENDERER
// ============================================================================
export function GenerativeRenderer({ components, onInteract, onComplete, phase = 'awakening', skipTransition = false }: GenerativeRendererProps) {
  const [showTransition, setShowTransition] = useState(false);
  
  // Parse components by type - handle both frontend and backend naming conventions
  const progressComp = components.find(c => c.type === 'progress');
  const textComps = components.filter(c => 
    c.type === 'text' || 
    c.type === 'insight_card'  // Backend may send insight_card, treat as styled text
  );
  const inputComp = components.find(c => c.type === 'input');
  
  // Handle multiple naming conventions for choices
  const choiceComp = components.find(c => 
    c.type === 'binary_choice' || 
    c.type === 'choice_card' || 
    c.type === 'choice'  // Backend sends this
  );
  
  // Handle slider component
  const sliderComp = components.find(c => c.type === 'slider');
  
  // Handle card selection (backend sends 'cards')
  const cardsComp = components.find(c => c.type === 'cards');
  
  // Handle game components
  const gameComp = components.find(c => c.type === 'reflex_tap' || c.type === 'game');
  
  // Handle completion components (Digital Twin delivery)
  const digitalTwinComp = components.find(c => c.type === 'digital_twin_card');
  const activationStepsComp = components.find(c => c.type === 'activation_steps');
  const completionTransitionComp = components.find(c => c.type === 'completion_transition');
  
  // Check if this is a completion screen
  const isCompletionScreen = !!(digitalTwinComp || activationStepsComp || completionTransitionComp);
  
  // Show transition animation when completion screen first appears (unless skipped)
  useEffect(() => {
    if (completionTransitionComp && !showTransition && !skipTransition) {
      setShowTransition(true);
    }
  }, [completionTransitionComp, skipTransition]);
  
  // If we're in completion mode, render the completion UI
  if (isCompletionScreen) {
    return (
      <View style={styles.container}>
        {/* Transition animation overlay - skip for restored sessions */}
        {showTransition && !skipTransition && (
          <Modal visible transparent animationType="none">
            <View style={styles.transitionOverlay}>
              <CompletionTransition
                type={completionTransitionComp?.transition_type || 'reveal'}
                phase={phase}
                onComplete={() => setShowTransition(false)}
              />
            </View>
          </Modal>
        )}
        
        {/* Main completion content - show immediately if skipTransition */}
        {(!showTransition || skipTransition) && (
          <ScrollView 
            style={styles.completionScroll}
            contentContainerStyle={styles.completionContent}
            showsVerticalScrollIndicator={true}
            scrollEventThrottle={16}
            bounces={true}
            alwaysBounceVertical={true}
            keyboardShouldPersistTaps="handled"
            keyboardDismissMode="on-drag"
            nestedScrollEnabled={true}
            scrollEnabled={true}
          >
            {/* Progress at top */}
            {progressComp && (
              <ProgressIndicator
                current={(progressComp as any).props?.questionIndex || progressComp.current || 1}
                total={(progressComp as any).props?.totalQuestions || progressComp.total || 5}
                phase={(progressComp as any).props?.phase || phase}
              />
            )}
            
            {/* Text/Message */}
            {textComps.map((comp, index) => (
              <QuestionDisplay
                key={index}
                content={(comp as any).props?.content || comp.content || ''}
                variant={(comp as any).props?.variant || comp.variant}
              />
            ))}
            
            {/* Digital Twin Card */}
            {digitalTwinComp?.digital_twin && (
              <DigitalTwinCard
                digitalTwin={digitalTwinComp.digital_twin}
                phase={phase}
              />
            )}
            
            {/* Activation Steps - display only, no interaction */}
            {activationStepsComp?.steps && (
              <ActivationSteps
                steps={activationStepsComp.steps}
                phase={phase}
              />
            )}
            
            {/* Continue to Dashboard Button */}
            <Animated.View entering={FadeIn.duration(600).delay(800)}>
              <Pressable
                style={({ pressed }) => [
                  styles.continueButton,
                  pressed && styles.continueButtonPressed,
                ]}
                onPress={onComplete}
              >
                <Text style={styles.continueButtonText}>Continue to Dashboard →</Text>
              </Pressable>
            </Animated.View>
          </ScrollView>
        )}
      </View>
    );
  }
  
  // Regular profiling UI
  return (
    <View style={styles.container}>
      {/* Fixed top section: Progress */}
      <View style={styles.topSection}>
        {progressComp && (
          <ProgressIndicator
            current={(progressComp as any).props?.questionIndex || progressComp.current || 1}
            total={(progressComp as any).props?.totalQuestions || progressComp.total || 5}
            phase={(progressComp as any).props?.phase || phase}
          />
        )}
      </View>
      
      {/* Flexible middle: Question/Text - takes remaining space */}
      <View style={styles.middleSection}>
        <View style={styles.contentArea}>
          {textComps.map((comp, index) => (
            <QuestionDisplay
              key={index}
              content={(comp as any).props?.content || comp.content || ''}
              variant={(comp as any).props?.variant || comp.variant}
            />
          ))}
        </View>
      </View>
      
      {/* Fixed bottom section: Input/Choices/Slider */}
      <View style={styles.bottomSection}>
        {inputComp && (
          <PremiumInput
            placeholder={(inputComp as any).props?.placeholder || inputComp.placeholder}
            minLength={(inputComp as any).props?.minLength || inputComp.minLength}
            onSubmit={(value) => onInteract(components.indexOf(inputComp), value)}
            phase={phase}
          />
        )}
        
        {choiceComp && (
          <ChoiceCards
            options={
              (choiceComp as any).props?.options?.map?.((o: any) => 
                typeof o === 'string' ? o : o.label || o.value
              ) || 
              choiceComp.options || 
              []
            }
            onSelect={(option) => onInteract(components.indexOf(choiceComp), option)}
            phase={phase}
          />
        )}
        
        {sliderComp && (
          <SliderComponent
            min={(sliderComp as any).props?.min || sliderComp.min || 1}
            max={(sliderComp as any).props?.max || sliderComp.max || 10}
            step={(sliderComp as any).props?.step || 1}
            labels={(sliderComp as any).props?.labels || {}}
            onSelect={(value) => onInteract(components.indexOf(sliderComp), value)}
            phase={phase}
          />
        )}
        
        {cardsComp && (
          <CardSelection
            cards={
              (cardsComp as any).props?.cards || 
              cardsComp.options?.map?.((o: string) => ({ title: o, value: o })) || 
              []
            }
            maxSelections={(cardsComp as any).props?.maxSelections || 1}
            onSelect={(values) => onInteract(components.indexOf(cardsComp), values)}
            phase={phase}
          />
        )}
        
        {gameComp && (
          <ReflexGameWrapper
            definition={gameComp}
            phase={phase}
            onComplete={(result) => onInteract(components.indexOf(gameComp), result)}
          />
        )}
      </View>
    </View>
  );
}

// ============================================================================
// STYLES
// ============================================================================
const styles = StyleSheet.create({
  container: {
    flex: 1,
    paddingHorizontal: 20,
  },
  
  // Fixed sections for stable layout
  topSection: {
    // Progress bar - fixed height
    paddingTop: 8,
  },
  middleSection: {
    flex: 1,
    justifyContent: 'center',
  },
  bottomSection: {
    // Input/choices - content-sized
    paddingBottom: 16,
  },
  
  // Progress Indicator
  progressContainer: {
    marginBottom: 20,
  },
  progressHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  phaseLabel: {
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 2,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  progressCount: {
    fontSize: 10,
    color: 'rgba(255, 255, 255, 0.35)',
    fontWeight: '500',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  progressTrack: {
    height: 2,
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    borderRadius: 1,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    borderRadius: 1,
  },
  
  // Content Area (Questions)
  contentArea: {
    paddingHorizontal: 8,
  },
  questionContainer: {
    // Centered by parent
  },
  questionText: {
    fontSize: 24,
    fontWeight: '300',
    color: 'rgba(255, 255, 255, 0.92)',
    lineHeight: 36,
    textAlign: 'center',
    letterSpacing: 0.2,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  insightText: {
    fontSize: 16,
    fontWeight: '400',
    fontStyle: 'italic',
    color: 'rgba(255, 255, 255, 0.7)',
    lineHeight: 26,
    textAlign: 'center',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  labelText: {
    fontSize: 12,
    fontWeight: '600',
    color: 'rgba(255, 255, 255, 0.5)',
    letterSpacing: 1.5,
    textTransform: 'uppercase',
    textAlign: 'center',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  
  // Interaction Area
  interactionArea: {
    paddingBottom: 16,
  },
  
  // Premium Input
  inputWrapper: {
    gap: 12,
  },
  inputOuterContainer: {
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderWidth: 1,
    borderRadius: 16,
    overflow: 'hidden',
  },
  premiumInput: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '400',
    padding: 16,
    minHeight: 100,
    maxHeight: 140,
    textAlignVertical: 'top',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  inputProgressTrack: {
    height: 2,
    backgroundColor: 'rgba(255, 255, 255, 0.04)',
  },
  inputProgressFill: {
    height: '100%',
  },
  
  // Submit Area
  submitArea: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  charCounter: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.3)',
    fontWeight: '500',
    marginLeft: 4,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  submitButton: {
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.06)',
  },
  submitButtonActive: {
    // Background set dynamically
  },
  submitButtonPressed: {
    opacity: 0.85,
    transform: [{ scale: 0.98 }],
  },
  submitButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
    letterSpacing: 0.3,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  submitButtonTextDisabled: {
    color: 'rgba(255, 255, 255, 0.25)',
  },
  
  // Choice Cards
  choiceContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    justifyContent: 'center',
  },
  choiceCardWrapper: {
    width: (SCREEN_WIDTH - 52) / 2,
  },
  choiceCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.04)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    paddingVertical: 24,
    paddingHorizontal: 16,
    borderRadius: 16,
    alignItems: 'center',
  },
  choiceCardPressed: {
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
  },
  choiceText: {
    fontSize: 15,
    fontWeight: '500',
    color: 'rgba(255, 255, 255, 0.85)',
    textAlign: 'center',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  
  // Game Modal
  gameModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(5, 5, 5, 0.95)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  
  // Slider Component
  sliderContainer: {
    paddingVertical: 16,
  },
  sliderLabels: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 12,
  },
  sliderLabel: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.5)',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  sliderTrack: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 8,
    marginBottom: 16,
  },
  sliderTick: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: 'rgba(255, 255, 255, 0.08)',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
  },
  sliderTickSelected: {
    borderWidth: 2,
  },
  sliderTickLabel: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.6)',
    fontWeight: '500',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  sliderTickLabelSelected: {
    color: '#FFFFFF',
    fontWeight: '700',
  },
  sliderConfirm: {
    paddingVertical: 12,
    paddingHorizontal: 32,
    borderRadius: 20,
    alignSelf: 'center',
  },
  sliderConfirmText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  
  // Card Selection Component
  cardSelectionContainer: {
    paddingVertical: 8,
  },
  cardsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    justifyContent: 'center',
    marginBottom: 16,
  },
  selectionCard: {
    width: (SCREEN_WIDTH - 52) / 2,
    backgroundColor: 'rgba(255, 255, 255, 0.04)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.08)',
    paddingVertical: 20,
    paddingHorizontal: 16,
    borderRadius: 16,
  },
  selectionCardSelected: {
    borderWidth: 2,
  },
  selectionCardTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: 'rgba(255, 255, 255, 0.85)',
    textAlign: 'center',
    marginBottom: 4,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  selectionCardDesc: {
    fontSize: 12,
    color: 'rgba(255, 255, 255, 0.5)',
    textAlign: 'center',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  cardConfirmButton: {
    paddingVertical: 12,
    paddingHorizontal: 32,
    borderRadius: 20,
    alignSelf: 'center',
  },
  cardConfirmText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#FFFFFF',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  
  // ============================================================================
  // COMPLETION UI STYLES
  // ============================================================================
  
  // Completion scroll container
  completionScroll: {
    flex: 1,
  },
  completionContent: {
    paddingTop: 20,
    paddingBottom: 60, // Extra padding for footer and safe scrolling
    paddingHorizontal: 4, // Small horizontal padding to prevent edge clipping
    gap: 24,
  },
  
  // Transition overlay
  transitionOverlay: {
    flex: 1,
    backgroundColor: 'rgba(5, 5, 5, 0.98)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  transitionContainer: {
    width: SCREEN_WIDTH,
    height: SCREEN_WIDTH,
    justifyContent: 'center',
    alignItems: 'center',
  },
  transitionRing: {
    position: 'absolute',
    width: 150,
    height: 150,
    borderRadius: 75,
    borderWidth: 2,
  },
  transitionCenter: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  transitionEmoji: {
    fontSize: 48,
    marginBottom: 16,
  },
  transitionTitle: {
    fontSize: 28,
    fontWeight: '600',
    marginBottom: 8,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  transitionSubtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.6)',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  
  // Digital Twin Card
  twinCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderRadius: 20,
    padding: 24,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    shadowOffset: { width: 0, height: 4 },
  },
  twinHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
    gap: 16,
  },
  twinTypeEmoji: {
    fontSize: 48,
  },
  twinHeaderText: {
    flex: 1,
  },
  twinType: {
    fontSize: 24,
    fontWeight: '700',
    marginBottom: 4,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  twinProfile: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.5)',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  twinSummary: {
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
  },
  twinSummaryText: {
    fontSize: 15,
    fontStyle: 'italic',
    color: 'rgba(255, 255, 255, 0.7)',
    lineHeight: 24,
    textAlign: 'center',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  twinInsightsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 20,
  },
  twinInsightItem: {
    width: (SCREEN_WIDTH - 88) / 2,
    backgroundColor: 'rgba(255, 255, 255, 0.02)',
    borderRadius: 12,
    padding: 12,
    alignItems: 'center',
  },
  twinInsightLabel: {
    fontSize: 11,
    fontWeight: '600',
    color: 'rgba(255, 255, 255, 0.4)',
    letterSpacing: 1,
    textTransform: 'uppercase',
    marginBottom: 6,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  twinInsightValue: {
    fontSize: 14,
    fontWeight: '600',
    textAlign: 'center',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  twinFooter: {
    alignItems: 'center',
  },
  completionBadge: {
    paddingVertical: 8,
    paddingHorizontal: 16,
    borderRadius: 20,
  },
  completionText: {
    fontSize: 13,
    fontWeight: '600',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  
  // Activation Steps
  stepsContainer: {
    marginTop: 8,
  },
  stepsTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: 'rgba(255, 255, 255, 0.9)',
    marginBottom: 4,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  stepsSubtitle: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.5)',
    marginBottom: 16,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  stepsList: {
    // No maxHeight - let parent ScrollView handle scrolling
  },
  stepCard: {
    flexDirection: 'row',
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.06)',
  },
  stepCardPressed: {
    backgroundColor: 'rgba(255, 255, 255, 0.06)',
  },
  stepIconContainer: {
    width: 44,
    height: 44,
    borderRadius: 12,
    backgroundColor: 'rgba(255, 255, 255, 0.05)',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 14,
  },
  stepIcon: {
    fontSize: 20,
  },
  stepContent: {
    flex: 1,
  },
  stepHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 6,
  },
  stepTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: 'rgba(255, 255, 255, 0.9)',
    flex: 1,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  priorityBadge: {
    paddingVertical: 3,
    paddingHorizontal: 8,
    borderRadius: 10,
  },
  priorityText: {
    fontSize: 10,
    fontWeight: '700',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  stepDescription: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.6)',
    lineHeight: 20,
    marginBottom: 8,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  stepMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  stepCategory: {
    fontSize: 11,
    fontWeight: '600',
    color: 'rgba(255, 255, 255, 0.4)',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  stepTime: {
    fontSize: 11,
    color: 'rgba(255, 255, 255, 0.4)',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  
  // Continue Button (Completion Screen)
  continueButton: {
    backgroundColor: '#9333EA',
    paddingVertical: 18,
    paddingHorizontal: 32,
    borderRadius: 16,
    alignItems: 'center',
    marginTop: 16,
    marginBottom: 20,
    shadowColor: '#9333EA',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 4,
  },
  continueButtonPressed: {
    opacity: 0.85,
    transform: [{ scale: 0.98 }],
  },
  continueButtonText: {
    color: '#FFFFFF',
    fontSize: 16,
    fontWeight: '600',
    letterSpacing: 0.5,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
});
