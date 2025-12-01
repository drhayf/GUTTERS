/**
 * GlobalOverlayProvider
 * 
 * Renders global overlays anywhere in the app.
 * Wrap your app with this provider to enable generative UI popups.
 */
import React, { useEffect, useCallback } from 'react';
import { Modal, View, StyleSheet, Pressable, Platform } from 'react-native';
import { Text } from 'tamagui';
import { useAtom, useAtomValue, useSetAtom } from 'jotai';
import Animated, { FadeIn, FadeOut, SlideInUp } from 'react-native-reanimated';

import { 
  activeOverlayAtom, 
  dismissOverlayAtom,
  type GlobalOverlay,
} from '../lib/state/global-ui-atoms';
import { ReflexTapComponent } from './genesis/ReflexTapComponent';
import { GenerativeRenderer } from './genesis/GenerativeRenderer';
import type { GameResult } from '../lib/games/types';
import { saveGameResult } from '../lib/games/storage';

interface GlobalOverlayProviderProps {
  children: React.ReactNode;
}

export function GlobalOverlayProvider({ children }: GlobalOverlayProviderProps) {
  const activeOverlay = useAtomValue(activeOverlayAtom);
  const dismissOverlay = useSetAtom(dismissOverlayAtom);
  
  // Handle game completion
  const handleGameComplete = useCallback(async (
    overlay: GlobalOverlay,
    partialResult: Omit<GameResult, 'gameId' | 'gameType' | 'timestamp' | 'phase'>
  ) => {
    if (!overlay.data.game) return;
    
    const fullResult: GameResult = {
      ...partialResult,
      gameId: overlay.data.game.id,
      gameType: overlay.data.game.type,
      timestamp: new Date(),
      phase: 'global', // Mark as triggered from global overlay
    };
    
    await saveGameResult(fullResult);
    console.log('[GlobalOverlay] Game completed:', fullResult.status);
    
    // Dismiss after delay to show result
    setTimeout(() => dismissOverlay(overlay.id), 1500);
  }, [dismissOverlay]);
  
  // Handle game timeout
  const handleGameTimeout = useCallback((overlay: GlobalOverlay) => {
    dismissOverlay(overlay.id);
  }, [dismissOverlay]);
  
  // Handle notification auto-close
  useEffect(() => {
    if (activeOverlay?.data.autoCloseMs) {
      const timer = setTimeout(() => {
        dismissOverlay(activeOverlay.id);
      }, activeOverlay.data.autoCloseMs);
      
      return () => clearTimeout(timer);
    }
  }, [activeOverlay, dismissOverlay]);
  
  // Render overlay content based on type
  const renderOverlayContent = (overlay: GlobalOverlay) => {
    switch (overlay.type) {
      case 'game':
      case 'challenge':
        if (!overlay.data.game) return null;
        return (
          <View style={styles.gameContainer}>
            {overlay.type === 'challenge' && overlay.data.title && (
              <Animated.View entering={SlideInUp.duration(300)} style={styles.challengeHeader}>
                <Text style={styles.challengeTitle}>{overlay.data.title}</Text>
              </Animated.View>
            )}
            <ReflexTapComponent
              definition={overlay.data.game}
              onComplete={(result) => handleGameComplete(overlay, result)}
              onTimeout={() => handleGameTimeout(overlay)}
              phase="global"
            />
          </View>
        );
        
      case 'notification':
        return (
          <Animated.View 
            entering={FadeIn.duration(300)}
            style={styles.notificationContainer}
          >
            <View style={styles.notificationCard}>
              {overlay.data.title && (
                <Text style={styles.notificationTitle}>{overlay.data.title}</Text>
              )}
              {overlay.data.message && (
                <Text style={styles.notificationMessage}>{overlay.data.message}</Text>
              )}
              {overlay.dismissible && (
                <Pressable 
                  style={styles.dismissButton}
                  onPress={() => dismissOverlay(overlay.id)}
                >
                  <Text style={styles.dismissText}>Dismiss</Text>
                </Pressable>
              )}
            </View>
          </Animated.View>
        );
        
      case 'insight':
        if (!overlay.data.components) return null;
        return (
          <Animated.View 
            entering={SlideInUp.duration(400)}
            style={styles.insightContainer}
          >
            <View style={styles.insightCard}>
              {overlay.data.title && (
                <Text style={styles.insightTitle}>{overlay.data.title}</Text>
              )}
              <GenerativeRenderer
                components={overlay.data.components}
                onInteract={(index, value) => {
                  console.log('[GlobalOverlay] Insight interaction:', index, value);
                  // Could emit an event or handle the interaction
                }}
              />
              {overlay.dismissible && (
                <Pressable 
                  style={styles.dismissButton}
                  onPress={() => dismissOverlay(overlay.id)}
                >
                  <Text style={styles.dismissText}>Continue</Text>
                </Pressable>
              )}
            </View>
          </Animated.View>
        );
        
      default:
        return null;
    }
  };
  
  return (
    <>
      {children}
      
      {/* Global Overlay Modal */}
      {activeOverlay && (
        <Modal
          visible={true}
          transparent={activeOverlay.type !== 'game' && activeOverlay.type !== 'challenge'}
          animationType="fade"
          onRequestClose={() => {
            if (activeOverlay.dismissible) {
              dismissOverlay(activeOverlay.id);
            }
          }}
          statusBarTranslucent
        >
          <View style={[
            styles.modalOverlay,
            (activeOverlay.type === 'game' || activeOverlay.type === 'challenge') && styles.gameOverlay
          ]}>
            {renderOverlayContent(activeOverlay)}
          </View>
        </Modal>
      )}
    </>
  );
}

const styles = StyleSheet.create({
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(5, 5, 5, 0.9)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  gameOverlay: {
    backgroundColor: '#050505',
  },
  gameContainer: {
    flex: 1,
    width: '100%',
  },
  challengeHeader: {
    position: 'absolute',
    top: 60,
    left: 0,
    right: 0,
    zIndex: 10,
    alignItems: 'center',
  },
  challengeTitle: {
    color: '#FFD700',
    fontSize: 18,
    fontWeight: '700',
    letterSpacing: 2,
    textTransform: 'uppercase',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  notificationContainer: {
    padding: 20,
    width: '100%',
    maxWidth: 340,
  },
  notificationCard: {
    backgroundColor: 'rgba(10, 10, 10, 0.98)',
    borderWidth: 1,
    borderColor: 'rgba(147, 51, 234, 0.4)',
    borderRadius: 16,
    padding: 24,
  },
  notificationTitle: {
    color: 'rgba(255, 255, 255, 0.95)',
    fontSize: 20,
    fontWeight: '600',
    marginBottom: 12,
    textAlign: 'center',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  notificationMessage: {
    color: 'rgba(255, 255, 255, 0.7)',
    fontSize: 15,
    lineHeight: 22,
    textAlign: 'center',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  insightContainer: {
    padding: 20,
    width: '100%',
    maxWidth: 400,
    maxHeight: '80%',
  },
  insightCard: {
    backgroundColor: 'rgba(10, 10, 10, 0.98)',
    borderWidth: 1,
    borderColor: 'rgba(6, 182, 212, 0.4)',
    borderRadius: 16,
    padding: 24,
  },
  insightTitle: {
    color: 'rgba(6, 182, 212, 0.9)',
    fontSize: 14,
    fontWeight: '600',
    letterSpacing: 2,
    marginBottom: 16,
    textTransform: 'uppercase',
    textAlign: 'center',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  dismissButton: {
    marginTop: 20,
    paddingVertical: 12,
    paddingHorizontal: 24,
    backgroundColor: 'rgba(147, 51, 234, 0.2)',
    borderWidth: 1,
    borderColor: 'rgba(147, 51, 234, 0.4)',
    borderRadius: 10,
    alignSelf: 'center',
  },
  dismissText: {
    color: 'rgba(255, 255, 255, 0.8)',
    fontSize: 14,
    fontWeight: '500',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
});
