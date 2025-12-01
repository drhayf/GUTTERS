/**
 * ReflexTapComponent
 * 
 * A surprise mini-game that tests the user's reaction time.
 * Displays a target that must be tapped as quickly as possible.
 * Auto-dismisses after timeout if not tapped.
 */
import React, { useEffect, useState, useRef, useCallback } from 'react';
import { StyleSheet, View, Pressable, Dimensions, Platform } from 'react-native';
import { Text } from 'tamagui';
import Animated, {
  useSharedValue,
  useAnimatedStyle,
  withTiming,
  withSpring,
  withSequence,
  withRepeat,
  runOnJS,
  Easing,
  FadeIn,
  FadeOut,
  ZoomIn,
  ZoomOut,
} from 'react-native-reanimated';
import type { GameComponentProps, GameResult, GameResultStatus } from '../../lib/games/types';
import { calculateReflexScore, getDifficultySettings } from '../../lib/games/types';

const { width: SCREEN_WIDTH, height: SCREEN_HEIGHT } = Dimensions.get('window');

interface ReflexTapProps extends GameComponentProps {
  // Additional props specific to reflex tap
}

export function ReflexTapComponent({ 
  definition, 
  onComplete, 
  onTimeout,
  phase 
}: ReflexTapProps) {
  const [gameState, setGameState] = useState<'waiting' | 'ready' | 'tapped' | 'missed'>('waiting');
  const [targetPosition, setTargetPosition] = useState({ x: 0, y: 0 });
  const [countdown, setCountdown] = useState<number | null>(null);
  const [resultText, setResultText] = useState<string | null>(null);
  
  const startTimeRef = useRef<number>(0);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const appearTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const countdownIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  
  // Animation values
  const targetScale = useSharedValue(0);
  const targetOpacity = useSharedValue(0);
  const pulseScale = useSharedValue(1);
  const overlayOpacity = useSharedValue(0);
  const timerWidth = useSharedValue(100);
  
  const difficultySettings = getDifficultySettings(definition.difficulty);
  const targetSize = difficultySettings.targetSize;
  const timeoutMs = definition.timeoutMs || difficultySettings.timeoutMs;
  
  // Generate random position for target
  const generatePosition = useCallback(() => {
    const padding = 60;
    const x = padding + Math.random() * (SCREEN_WIDTH - targetSize - padding * 2);
    const y = 150 + Math.random() * (SCREEN_HEIGHT - targetSize - 350);
    return { x, y };
  }, [targetSize]);
  
  // Start the game
  useEffect(() => {
    // Fade in overlay
    overlayOpacity.value = withTiming(1, { duration: 200 });
    
    // Random delay before showing target (element of surprise)
    const [minDelay, maxDelay] = difficultySettings.delayRangeMs;
    const delay = minDelay + Math.random() * (maxDelay - minDelay);
    
    // Show countdown
    setCountdown(3);
    
    const startCountdown = () => {
      let count = 3;
      countdownIntervalRef.current = setInterval(() => {
        count--;
        if (count > 0) {
          setCountdown(count);
        } else {
          setCountdown(null);
          if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current);
          
          // After countdown, wait random delay then show target
          appearTimeoutRef.current = setTimeout(() => {
            showTarget();
          }, delay);
        }
      }, 400);
    };
    
    setTimeout(startCountdown, 300);
    
    return () => {
      if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current);
      if (timeoutRef.current) clearTimeout(timeoutRef.current);
      if (appearTimeoutRef.current) clearTimeout(appearTimeoutRef.current);
    };
  }, []);
  
  const showTarget = useCallback(() => {
    const pos = generatePosition();
    setTargetPosition(pos);
    setGameState('ready');
    startTimeRef.current = Date.now();
    
    // Animate target appearing
    targetScale.value = withSpring(1, { damping: 8, stiffness: 150 });
    targetOpacity.value = withTiming(1, { duration: 100 });
    
    // Pulse animation
    pulseScale.value = withRepeat(
      withSequence(
        withTiming(1.2, { duration: 300 }),
        withTiming(1, { duration: 300 })
      ),
      -1,
      true
    );
    
    // Timer bar animation
    timerWidth.value = withTiming(0, { 
      duration: timeoutMs, 
      easing: Easing.linear 
    });
    
    // Set timeout for miss
    timeoutRef.current = setTimeout(() => {
      handleMiss();
    }, timeoutMs);
  }, [generatePosition, timeoutMs]);
  
  const handleTap = useCallback(() => {
    if (gameState !== 'ready') return;
    
    // Clear timeout
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    
    const reactionTime = Date.now() - startTimeRef.current;
    const score = calculateReflexScore(reactionTime);
    
    setGameState('tapped');
    setResultText(`${reactionTime}ms - ${score >= 85 ? '⚡ Lightning!' : score >= 60 ? '✓ Good' : '→ OK'}`);
    
    // Animate success
    targetScale.value = withSequence(
      withSpring(1.3, { damping: 5 }),
      withTiming(0, { duration: 200 })
    );
    
    // Complete after animation
    setTimeout(() => {
      onComplete({
        status: 'success',
        reactionTimeMs: reactionTime,
        score,
      });
    }, 800);
  }, [gameState, onComplete]);
  
  const handleMiss = useCallback(() => {
    setGameState('missed');
    setResultText('Missed! ✗');
    
    // Animate miss
    targetScale.value = withTiming(0, { duration: 200 });
    targetOpacity.value = withTiming(0, { duration: 200 });
    
    // Complete after animation
    setTimeout(() => {
      onComplete({
        status: 'timeout',
        reactionTimeMs: null,
        score: 0,
      });
      onTimeout();
    }, 800);
  }, [onComplete, onTimeout]);
  
  // Animated styles
  const targetStyle = useAnimatedStyle(() => ({
    transform: [{ scale: targetScale.value }],
    opacity: targetOpacity.value,
  }));
  
  const pulseStyle = useAnimatedStyle(() => ({
    transform: [{ scale: pulseScale.value }],
  }));
  
  const overlayStyle = useAnimatedStyle(() => ({
    opacity: overlayOpacity.value,
  }));
  
  const timerStyle = useAnimatedStyle(() => ({
    width: `${timerWidth.value}%`,
  }));
  
  return (
    <Animated.View style={[styles.overlay, overlayStyle]}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.title}>⚡ REFLEX TEST</Text>
        <Text style={styles.subtitle}>
          {gameState === 'waiting' && 'Get ready...'}
          {gameState === 'ready' && 'TAP NOW!'}
          {gameState === 'tapped' && 'Nice!'}
          {gameState === 'missed' && 'Too slow!'}
        </Text>
      </View>
      
      {/* Timer bar */}
      {gameState === 'ready' && (
        <View style={styles.timerContainer}>
          <Animated.View style={[styles.timerBar, timerStyle]} />
        </View>
      )}
      
      {/* Countdown */}
      {countdown !== null && (
        <Animated.View 
          entering={ZoomIn.duration(200)}
          exiting={ZoomOut.duration(150)}
          style={styles.countdownContainer}
        >
          <Text style={styles.countdownText}>{countdown}</Text>
        </Animated.View>
      )}
      
      {/* Target */}
      {gameState !== 'waiting' && gameState !== 'missed' && (
        <Animated.View
          style={[
            styles.targetContainer,
            targetStyle,
            { left: targetPosition.x, top: targetPosition.y },
          ]}
        >
          <Animated.View style={pulseStyle}>
            <Pressable
              onPress={handleTap}
              style={({ pressed }) => [
                styles.target,
                { 
                  width: targetSize, 
                  height: targetSize,
                  borderRadius: targetSize / 2,
                },
                pressed && styles.targetPressed,
              ]}
            >
              <Text style={styles.targetText}>TAP</Text>
            </Pressable>
          </Animated.View>
        </Animated.View>
      )}
      
      {/* Result text */}
      {resultText && (
        <Animated.View 
          entering={FadeIn.duration(200)}
          style={styles.resultContainer}
        >
          <Text style={[
            styles.resultText,
            gameState === 'tapped' && styles.resultSuccess,
            gameState === 'missed' && styles.resultMissed,
          ]}>
            {resultText}
          </Text>
        </Animated.View>
      )}
      
      {/* Difficulty indicator */}
      <View style={styles.difficultyBadge}>
        <Text style={styles.difficultyText}>
          {definition.difficulty.toUpperCase()}
        </Text>
      </View>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  overlay: {
    ...StyleSheet.absoluteFillObject,
    backgroundColor: 'rgba(5, 5, 5, 0.95)',
    zIndex: 1000,
  },
  header: {
    alignItems: 'center',
    paddingTop: 100,
    paddingBottom: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: '700',
    color: '#FBBF24',
    letterSpacing: 4,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  subtitle: {
    fontSize: 18,
    color: 'rgba(255, 255, 255, 0.7)',
    marginTop: 8,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  timerContainer: {
    height: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    marginHorizontal: 40,
    marginTop: 20,
    borderRadius: 2,
    overflow: 'hidden',
  },
  timerBar: {
    height: '100%',
    backgroundColor: '#EF4444',
    borderRadius: 2,
  },
  countdownContainer: {
    position: 'absolute',
    top: '40%',
    left: 0,
    right: 0,
    alignItems: 'center',
  },
  countdownText: {
    fontSize: 120,
    fontWeight: '200',
    color: 'rgba(255, 255, 255, 0.3)',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  targetContainer: {
    position: 'absolute',
  },
  target: {
    backgroundColor: '#10B981',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#10B981',
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.8,
    shadowRadius: 20,
    elevation: 10,
    borderWidth: 3,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  targetPressed: {
    backgroundColor: '#059669',
    transform: [{ scale: 0.95 }],
  },
  targetText: {
    color: 'white',
    fontSize: 14,
    fontWeight: '700',
    letterSpacing: 2,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  resultContainer: {
    position: 'absolute',
    top: '50%',
    left: 0,
    right: 0,
    alignItems: 'center',
  },
  resultText: {
    fontSize: 32,
    fontWeight: '600',
    color: 'white',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  resultSuccess: {
    color: '#10B981',
  },
  resultMissed: {
    color: '#EF4444',
  },
  difficultyBadge: {
    position: 'absolute',
    bottom: 100,
    left: 0,
    right: 0,
    alignItems: 'center',
  },
  difficultyText: {
    fontSize: 12,
    fontWeight: '600',
    color: 'rgba(255, 255, 255, 0.3)',
    letterSpacing: 2,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
});
