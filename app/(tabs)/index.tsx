import { useEffect, useState, useCallback } from 'react';
import { Spinner } from 'tamagui';
import { StyleSheet, Pressable, View, Text, SafeAreaView, Modal, ScrollView } from 'react-native';
import { Link } from 'expo-router';
import { useAtom } from 'jotai';
import { apiClient } from '../../lib/api-client';
import { selectedModelAtom } from '../../lib/state/model-atom';
import { AVAILABLE_MODELS, type ModelId } from '../../lib/storage/model-storage';
import type { GameDefinition, GameDifficulty, GameStats } from '../../lib/games/types';
import { getGameStats } from '../../lib/games/storage';
import { pushOverlayAtom, createGameOverlay } from '../../lib/state/global-ui-atoms';
import { useSetAtom } from 'jotai';

interface SystemStatus {
  connected: boolean;
  version: string;
  model: string;
  hrmEnabled: boolean;
  agentCount: number;
}

export default function HomeScreen() {
  const [status, setStatus] = useState<SystemStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedModel, setSelectedModel] = useAtom(selectedModelAtom);
  const [showModelPicker, setShowModelPicker] = useState(false);
  
  // Games Lab state
  const [showGamesLab, setShowGamesLab] = useState(false);
  const [gameStats, setGameStats] = useState<GameStats | null>(null);
  const [selectedDifficulty, setSelectedDifficulty] = useState<GameDifficulty>('medium');
  
  // Global overlay for games
  const pushOverlay = useSetAtom(pushOverlayAtom);
  
  // Available games for testing
  const availableGames = [
    {
      id: 'reflex_tap',
      name: 'Reflex Tap',
      description: 'Test your reaction speed by tapping the target as fast as possible.',
      icon: '⚡',
      available: true,
    },
    {
      id: 'reflex_pattern',
      name: 'Pattern Match',
      description: 'Memorize and repeat the pattern sequence.',
      icon: '🔮',
      available: false, // Coming soon
    },
    {
      id: 'memory_flash',
      name: 'Memory Flash',
      description: 'Remember the briefly shown symbols.',
      icon: '💫',
      available: false,
    },
    {
      id: 'choice_speed',
      name: 'Speed Choice',
      description: 'Make quick decisions under pressure.',
      icon: '🎯',
      available: false,
    },
  ];
  
  const checkSystemStatus = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const health = await apiClient.healthCheck();
      const agentList = await apiClient.listAgents();
      
      setStatus({
        connected: health.status === 'healthy',
        version: health.version,
        model: health.models?.primary || 'unknown',
        hrmEnabled: health.hrm_enabled,
        agentCount: agentList.agents?.length || 0,
      });
    } catch (err) {
      console.log('[HomeScreen] Status check error:', err);
      setError('System offline');
      setStatus(null);
    } finally {
      setLoading(false);
    }
  }, []);
  
  // Load game stats when games lab opens
  const loadGameStats = useCallback(async () => {
    try {
      const stats = await getGameStats();
      setGameStats(stats);
    } catch (err) {
      console.error('[HomeScreen] Failed to load game stats:', err);
    }
  }, []);
  
  // Launch a game using global overlay
  const launchGame = useCallback((gameId: string) => {
    // Close the games lab modal first
    setShowGamesLab(false);
    
    // Small delay to let the modal close before showing game
    setTimeout(() => {
      const definition: GameDefinition = {
        type: gameId as GameDefinition['type'],
        id: `test_${gameId}_${Date.now()}`,
        difficulty: selectedDifficulty,
        timeoutMs: selectedDifficulty === 'easy' ? 5000 : selectedDifficulty === 'medium' ? 3000 : 2000,
      };
      
      // Push to global overlay system
      pushOverlay(createGameOverlay(definition));
      console.log('[HomeScreen] Launched game via global overlay:', gameId);
    }, 300);
  }, [selectedDifficulty, pushOverlay]);
  
  useEffect(() => {
    checkSystemStatus();
    const interval = setInterval(checkSystemStatus, 30000);
    return () => clearInterval(interval);
  }, [checkSystemStatus]);
  
  // Load stats when games lab opens
  useEffect(() => {
    if (showGamesLab) {
      loadGameStats();
    }
  }, [showGamesLab, loadGameStats]);

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.content}>
        <View style={styles.header}>
          <Text style={styles.title}>PROJECT SOVEREIGN</Text>
          <Text style={styles.subtitle}>The Collapse OS</Text>
        </View>
        
        <View style={styles.statusContainer}>
          {loading ? (
            <View style={styles.statusRow}>
              <Spinner size="small" color="#9333EA" />
              <Text style={styles.statusText}>Connecting...</Text>
            </View>
          ) : error ? (
            <Pressable onPress={checkSystemStatus}>
              <View style={styles.statusRow}>
                <View style={[styles.statusDot, styles.statusOffline]} />
                <Text style={styles.statusTextError}>{error}</Text>
                <Text style={styles.retryIcon}> ↻</Text>
              </View>
            </Pressable>
          ) : status ? (
            <View style={styles.statusInfo}>
              <View style={styles.statusRow}>
                <View style={[styles.statusDot, styles.statusOnline]} />
                <Text style={styles.statusText}>System Online</Text>
              </View>
              <View style={styles.statusDetails}>
                <Text style={styles.statusDetail}>v{status.version}</Text>
                <Text style={styles.statusDivider}>•</Text>
                <Text style={styles.statusDetail}>
                  {AVAILABLE_MODELS.find(m => m.id === selectedModel)?.name || selectedModel}
                </Text>
                {status.hrmEnabled && (
                  <>
                    <Text style={styles.statusDivider}>•</Text>
                    <Text style={styles.hrmBadge}>HRM</Text>
                  </>
                )}
              </View>
              <Text style={styles.agentCount}>
                {status.agentCount} agent{status.agentCount !== 1 ? 's' : ''} ready
              </Text>
            </View>
          ) : null}
        </View>
        
        {/* Model Selector */}
        <Pressable 
          style={styles.modelSelector}
          onPress={() => setShowModelPicker(true)}
        >
          <Text style={styles.modelLabel}>AI Model</Text>
          <View style={styles.modelValue}>
            <Text style={styles.modelName}>
              {AVAILABLE_MODELS.find(m => m.id === selectedModel)?.name || 'Select Model'}
            </Text>
            <Text style={styles.modelArrow}>▾</Text>
          </View>
        </Pressable>
        
        {/* Model Picker Modal */}
        <Modal
          visible={showModelPicker}
          transparent
          animationType="fade"
          onRequestClose={() => setShowModelPicker(false)}
        >
          <Pressable 
            style={styles.modalOverlay}
            onPress={() => setShowModelPicker(false)}
          >
            <View style={styles.modalContent}>
              <Text style={styles.modalTitle}>Select AI Model</Text>
              {AVAILABLE_MODELS.map((model) => (
                <Pressable
                  key={model.id}
                  style={[
                    styles.modelOption,
                    selectedModel === model.id && styles.modelOptionSelected
                  ]}
                  onPress={() => {
                    setSelectedModel(model.id as ModelId);
                    setShowModelPicker(false);
                  }}
                >
                  <View style={styles.modelOptionHeader}>
                    <Text style={[
                      styles.modelOptionName,
                      selectedModel === model.id && styles.modelOptionNameSelected
                    ]}>
                      {model.name}
                    </Text>
                    <Text style={styles.modelTier}>{model.tier}</Text>
                  </View>
                  <Text style={styles.modelDescription}>{model.description}</Text>
                </Pressable>
              ))}
            </View>
          </Pressable>
        </Modal>
        
        <View style={styles.main}>
          <Link href="/genesis" asChild>
            <Pressable 
              style={({ pressed }) => [
                styles.genesisButton,
                pressed && styles.genesisButtonPressed,
                (!status?.connected && !loading) && styles.genesisButtonDisabled
              ]}
            >
              <Text style={styles.genesisButtonText}>BEGIN GENESIS</Text>
              <Text style={styles.genesisButtonSubtext}>
                {status?.connected ? 'Initiate Digital Twin Profiling' : 'Waiting for system...'}
              </Text>
            </Pressable>
          </Link>
        </View>
        
        <View style={styles.features}>
          <View style={styles.featureRow}>
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>◈</Text>
              <Text style={styles.featureLabel}>AI-Native</Text>
            </View>
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>◎</Text>
              <Text style={styles.featureLabel}>Real-time</Text>
            </View>
            <View style={styles.featureItem}>
              <Text style={styles.featureIcon}>⬡</Text>
              <Text style={styles.featureLabel}>Sovereign</Text>
            </View>
          </View>
        </View>
        
        {/* Mini-Games Lab Button */}
        <Pressable 
          style={({ pressed }) => [
            styles.gamesLabButton,
            pressed && styles.gamesLabButtonPressed
          ]}
          onPress={() => setShowGamesLab(true)}
        >
          <Text style={styles.gamesLabIcon}>🎮</Text>
          <View style={styles.gamesLabText}>
            <Text style={styles.gamesLabTitle}>Mini-Games Lab</Text>
            <Text style={styles.gamesLabSubtitle}>Test & develop game components</Text>
          </View>
        </Pressable>
        
        {/* Games Lab Modal */}
        <Modal
          visible={showGamesLab}
          transparent
          animationType="slide"
          onRequestClose={() => setShowGamesLab(false)}
        >
          <View style={styles.gamesLabOverlay}>
            <View style={styles.gamesLabContent}>
              <View style={styles.gamesLabHeader}>
                <Text style={styles.gamesLabModalTitle}>🎮 Mini-Games Lab</Text>
                <Pressable onPress={() => setShowGamesLab(false)}>
                  <Text style={styles.closeButton}>✕</Text>
                </Pressable>
              </View>
              
              {/* Stats Summary */}
              {gameStats && gameStats.totalGames > 0 && (
                <View style={styles.statsContainer}>
                  <Text style={styles.statsTitle}>Your Stats</Text>
                  <View style={styles.statsRow}>
                    <View style={styles.statItem}>
                      <Text style={styles.statValue}>{gameStats.totalGames}</Text>
                      <Text style={styles.statLabel}>Games</Text>
                    </View>
                    <View style={styles.statItem}>
                      <Text style={styles.statValue}>{gameStats.successRate.toFixed(0)}%</Text>
                      <Text style={styles.statLabel}>Success</Text>
                    </View>
                    <View style={styles.statItem}>
                      <Text style={styles.statValue}>
                        {gameStats.averageReactionTime > 0 
                          ? `${gameStats.averageReactionTime.toFixed(0)}ms`
                          : '-'}
                      </Text>
                      <Text style={styles.statLabel}>Avg Time</Text>
                    </View>
                    <View style={styles.statItem}>
                      <Text style={styles.statValue}>
                        {gameStats.bestReactionTime > 0 && gameStats.bestReactionTime !== Infinity
                          ? `${gameStats.bestReactionTime.toFixed(0)}ms`
                          : '-'}
                      </Text>
                      <Text style={styles.statLabel}>Best</Text>
                    </View>
                  </View>
                </View>
              )}
              
              {/* Difficulty Selector */}
              <View style={styles.difficultySection}>
                <Text style={styles.difficultyLabel}>Difficulty</Text>
                <View style={styles.difficultyOptions}>
                  {(['easy', 'medium', 'hard'] as GameDifficulty[]).map((diff) => (
                    <Pressable
                      key={diff}
                      style={[
                        styles.difficultyOption,
                        selectedDifficulty === diff && styles.difficultyOptionSelected
                      ]}
                      onPress={() => setSelectedDifficulty(diff)}
                    >
                      <Text style={[
                        styles.difficultyText,
                        selectedDifficulty === diff && styles.difficultyTextSelected
                      ]}>
                        {diff.charAt(0).toUpperCase() + diff.slice(1)}
                      </Text>
                    </Pressable>
                  ))}
                </View>
              </View>
              
              {/* Games List */}
              <ScrollView style={styles.gamesList}>
                {availableGames.map((game) => (
                  <Pressable
                    key={game.id}
                    style={({ pressed }) => [
                      styles.gameCard,
                      !game.available && styles.gameCardDisabled,
                      pressed && game.available && styles.gameCardPressed
                    ]}
                    onPress={() => game.available && launchGame(game.id)}
                    disabled={!game.available}
                  >
                    <Text style={styles.gameIcon}>{game.icon}</Text>
                    <View style={styles.gameInfo}>
                      <Text style={[
                        styles.gameName,
                        !game.available && styles.gameNameDisabled
                      ]}>
                        {game.name}
                        {!game.available && ' (Coming Soon)'}
                      </Text>
                      <Text style={styles.gameDescription}>{game.description}</Text>
                    </View>
                    {game.available && (
                      <Text style={styles.playButton}>▶</Text>
                    )}
                  </Pressable>
                ))}
              </ScrollView>
              
              <Text style={styles.labNote}>
                Games here are for testing during development.{'\n'}
                In the full app, they appear during Genesis profiling.
              </Text>
            </View>
          </View>
        </Modal>
        
        {/* Settings Link */}
        <Link href={"/settings" as any} asChild>
          <Pressable style={styles.settingsButton}>
            <Text style={styles.settingsIcon}>⚙</Text>
            <Text style={styles.settingsText}>Settings</Text>
          </Pressable>
        </Link>
        
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            Build your sovereign identity through AI-native self-mastery
          </Text>
        </View>
      </View>
      
      {/* Games are now rendered via GlobalOverlayProvider */}
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#050505',
  },
  content: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 20,
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
  },
  title: {
    color: 'rgba(255, 255, 255, 0.9)',
    fontSize: 26,
    fontWeight: '200',
    letterSpacing: 6,
    textAlign: 'center',
  },
  subtitle: {
    color: 'rgba(147, 51, 234, 0.8)',
    fontSize: 14,
    fontWeight: '500',
    letterSpacing: 4,
    marginTop: 8,
  },
  statusContainer: {
    marginBottom: 40,
    padding: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(147, 51, 234, 0.2)',
    backgroundColor: 'rgba(147, 51, 234, 0.05)',
    minWidth: 280,
  },
  statusRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  statusInfo: {
    alignItems: 'center',
    gap: 8,
  },
  statusDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
  },
  statusOnline: {
    backgroundColor: '#22C55E',
  },
  statusOffline: {
    backgroundColor: '#EF4444',
  },
  statusText: {
    color: 'rgba(255, 255, 255, 0.7)',
    fontSize: 13,
    fontWeight: '500',
  },
  statusTextError: {
    color: 'rgba(239, 68, 68, 0.8)',
    fontSize: 13,
    fontWeight: '500',
  },
  retryIcon: {
    color: 'rgba(255, 255, 255, 0.5)',
    fontSize: 16,
  },
  statusDetails: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
  },
  statusDetail: {
    color: 'rgba(255, 255, 255, 0.4)',
    fontSize: 11,
  },
  statusDivider: {
    color: 'rgba(255, 255, 255, 0.2)',
    fontSize: 11,
  },
  hrmBadge: {
    color: '#9333EA',
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
  },
  agentCount: {
    color: 'rgba(255, 255, 255, 0.35)',
    fontSize: 10,
    marginTop: 4,
  },
  main: {
    alignItems: 'center',
    marginBottom: 40,
  },
  genesisButton: {
    backgroundColor: 'rgba(147, 51, 234, 0.15)',
    borderWidth: 1,
    borderColor: 'rgba(147, 51, 234, 0.4)',
    paddingVertical: 24,
    paddingHorizontal: 48,
    borderRadius: 16,
    alignItems: 'center',
  },
  genesisButtonPressed: {
    backgroundColor: 'rgba(147, 51, 234, 0.3)',
  },
  genesisButtonDisabled: {
    opacity: 0.5,
    borderColor: 'rgba(147, 51, 234, 0.2)',
  },
  genesisButtonText: {
    color: 'rgba(255, 255, 255, 0.95)',
    fontSize: 18,
    fontWeight: '600',
    letterSpacing: 4,
  },
  genesisButtonSubtext: {
    color: 'rgba(255, 255, 255, 0.5)',
    fontSize: 12,
    marginTop: 8,
  },
  features: {
    marginBottom: 40,
  },
  featureRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 40,
  },
  featureItem: {
    alignItems: 'center',
    gap: 4,
  },
  featureIcon: {
    color: 'rgba(147, 51, 234, 0.6)',
    fontSize: 24,
  },
  featureLabel: {
    color: 'rgba(255, 255, 255, 0.4)',
    fontSize: 11,
    fontWeight: '500',
    letterSpacing: 1,
  },
  footer: {
    marginTop: 20,
    paddingHorizontal: 40,
  },
  footerText: {
    color: 'rgba(255, 255, 255, 0.3)',
    fontSize: 12,
    textAlign: 'center',
  },
  // Model Selector styles
  modelSelector: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: 'rgba(147, 51, 234, 0.08)',
    borderWidth: 1,
    borderColor: 'rgba(147, 51, 234, 0.25)',
    borderRadius: 10,
    paddingVertical: 12,
    paddingHorizontal: 16,
    marginBottom: 24,
    minWidth: 260,
  },
  modelLabel: {
    color: 'rgba(255, 255, 255, 0.5)',
    fontSize: 12,
    fontWeight: '500',
  },
  modelValue: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  modelName: {
    color: 'rgba(255, 255, 255, 0.9)',
    fontSize: 13,
    fontWeight: '600',
  },
  modelArrow: {
    color: 'rgba(147, 51, 234, 0.7)',
    fontSize: 12,
  },
  // Modal styles
  modalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(0, 0, 0, 0.85)',
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  modalContent: {
    backgroundColor: '#0a0a0a',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(147, 51, 234, 0.3)',
    padding: 20,
    width: '100%',
    maxWidth: 340,
  },
  modalTitle: {
    color: 'rgba(255, 255, 255, 0.9)',
    fontSize: 18,
    fontWeight: '600',
    textAlign: 'center',
    marginBottom: 16,
    letterSpacing: 1,
  },
  modelOption: {
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 10,
    padding: 14,
    marginBottom: 10,
  },
  modelOptionSelected: {
    backgroundColor: 'rgba(147, 51, 234, 0.15)',
    borderColor: 'rgba(147, 51, 234, 0.5)',
  },
  modelOptionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  modelOptionName: {
    color: 'rgba(255, 255, 255, 0.85)',
    fontSize: 14,
    fontWeight: '600',
  },
  modelOptionNameSelected: {
    color: '#9333EA',
  },
  modelTier: {
    color: 'rgba(147, 51, 234, 0.7)',
    fontSize: 10,
    fontWeight: '700',
    letterSpacing: 1,
    textTransform: 'uppercase',
  },
  modelDescription: {
    color: 'rgba(255, 255, 255, 0.45)',
    fontSize: 11,
  },
  settingsButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    paddingVertical: 12,
    paddingHorizontal: 20,
    marginTop: 20,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(147, 51, 234, 0.3)',
    backgroundColor: 'rgba(147, 51, 234, 0.05)',
  },
  settingsIcon: {
    fontSize: 16,
    color: 'rgba(147, 51, 234, 0.7)',
  },
  settingsText: {
    color: 'rgba(255, 255, 255, 0.6)',
    fontSize: 13,
    fontWeight: '500',
    letterSpacing: 1,
  },
  
  // Games Lab styles
  gamesLabButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(6, 182, 212, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(6, 182, 212, 0.3)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 24,
    gap: 12,
    minWidth: 280,
  },
  gamesLabButtonPressed: {
    backgroundColor: 'rgba(6, 182, 212, 0.2)',
  },
  gamesLabIcon: {
    fontSize: 28,
  },
  gamesLabText: {
    flex: 1,
  },
  gamesLabTitle: {
    color: 'rgba(255, 255, 255, 0.9)',
    fontSize: 16,
    fontWeight: '600',
    letterSpacing: 1,
  },
  gamesLabSubtitle: {
    color: 'rgba(6, 182, 212, 0.7)',
    fontSize: 11,
    marginTop: 2,
  },
  gamesLabOverlay: {
    flex: 1,
    backgroundColor: 'rgba(5, 5, 5, 0.98)',
  },
  gamesLabContent: {
    flex: 1,
    padding: 20,
    paddingTop: 60,
  },
  gamesLabHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  gamesLabModalTitle: {
    color: 'rgba(255, 255, 255, 0.95)',
    fontSize: 22,
    fontWeight: '600',
    letterSpacing: 1,
  },
  closeButton: {
    color: 'rgba(255, 255, 255, 0.5)',
    fontSize: 24,
    padding: 8,
  },
  statsContainer: {
    backgroundColor: 'rgba(147, 51, 234, 0.1)',
    borderWidth: 1,
    borderColor: 'rgba(147, 51, 234, 0.3)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 20,
  },
  statsTitle: {
    color: 'rgba(255, 255, 255, 0.6)',
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 2,
    marginBottom: 12,
    textTransform: 'uppercase',
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    color: 'rgba(255, 255, 255, 0.95)',
    fontSize: 20,
    fontWeight: '700',
  },
  statLabel: {
    color: 'rgba(255, 255, 255, 0.5)',
    fontSize: 10,
    marginTop: 4,
    letterSpacing: 1,
  },
  difficultySection: {
    marginBottom: 20,
  },
  difficultyLabel: {
    color: 'rgba(255, 255, 255, 0.6)',
    fontSize: 12,
    fontWeight: '600',
    letterSpacing: 2,
    marginBottom: 10,
    textTransform: 'uppercase',
  },
  difficultyOptions: {
    flexDirection: 'row',
    gap: 10,
  },
  difficultyOption: {
    flex: 1,
    paddingVertical: 10,
    paddingHorizontal: 16,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.15)',
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    alignItems: 'center',
  },
  difficultyOptionSelected: {
    borderColor: 'rgba(6, 182, 212, 0.6)',
    backgroundColor: 'rgba(6, 182, 212, 0.15)',
  },
  difficultyText: {
    color: 'rgba(255, 255, 255, 0.6)',
    fontSize: 13,
    fontWeight: '500',
  },
  difficultyTextSelected: {
    color: 'rgba(6, 182, 212, 1)',
  },
  gamesList: {
    flex: 1,
  },
  gameCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.03)',
    borderWidth: 1,
    borderColor: 'rgba(255, 255, 255, 0.1)',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    gap: 14,
  },
  gameCardPressed: {
    backgroundColor: 'rgba(6, 182, 212, 0.1)',
    borderColor: 'rgba(6, 182, 212, 0.3)',
  },
  gameCardDisabled: {
    opacity: 0.5,
  },
  gameIcon: {
    fontSize: 32,
  },
  gameInfo: {
    flex: 1,
  },
  gameName: {
    color: 'rgba(255, 255, 255, 0.9)',
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 4,
  },
  gameNameDisabled: {
    color: 'rgba(255, 255, 255, 0.5)',
  },
  gameDescription: {
    color: 'rgba(255, 255, 255, 0.5)',
    fontSize: 12,
  },
  playButton: {
    color: 'rgba(6, 182, 212, 0.8)',
    fontSize: 20,
  },
  labNote: {
    color: 'rgba(255, 255, 255, 0.35)',
    fontSize: 11,
    textAlign: 'center',
    marginTop: 16,
    lineHeight: 18,
  },
  gameModalOverlay: {
    flex: 1,
    backgroundColor: 'rgba(5, 5, 5, 0.98)',
    justifyContent: 'center',
    alignItems: 'center',
  },
});
