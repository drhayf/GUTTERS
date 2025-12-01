/**
 * Dashboard Screen - The Digital Twin Command Center
 * 
 * This is the main portal into the user's Digital Twin - a sci-fi inspired
 * command center that visualizes their identity and provides access to all
 * capabilities.
 * 
 * Features:
 * ━━━━━━━━━━
 * 1. Digital Twin Portal - Live synthesis visualization
 * 2. Identity Hexagon - Core traits in hexagonal display
 * 3. Module Grid - Quick access to all capabilities
 * 4. Live Indicators - Real-time metrics
 * 5. Quick Actions - Common agent commands
 * 6. Genesis CTA - If profile incomplete
 * 
 * Architecture:
 * ━━━━━━━━━━━━━━
 * - Pulls data from dashboard-atoms
 * - Integrates with module-preferences-atoms
 * - Syncs with backend for fresh Digital Twin data
 * - Uses GlobalAgentShell for agent interaction
 * 
 * @module Dashboard
 */

import React, { useEffect, useCallback, useState } from 'react';
import {
  View,
  StyleSheet,
  ScrollView,
  Pressable,
  RefreshControl,
  Platform,
  Dimensions,
} from 'react-native';
import { Text, Spinner } from 'tamagui';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useRouter, Link } from 'expo-router';
import { useAtom, useAtomValue, useSetAtom } from 'jotai';
import Animated, {
  FadeIn,
  FadeInDown,
  FadeInUp,
  SlideInRight,
  useSharedValue,
  useAnimatedStyle,
  withRepeat,
  withTiming,
  withSequence,
  Easing,
} from 'react-native-reanimated';
import { LinearGradient } from 'expo-linear-gradient';
import {
  Sparkles,
  ChevronRight,
  Play,
  Settings,
  RefreshCw,
  Target,
  Brain,
  Heart,
  Zap,
  Eye,
  BookOpen,
  DollarSign,
  Activity,
  Utensils,
} from '@tamagui/lucide-icons';

import {
  dashboardStateAtom,
  initDashboardAtom,
  updateDigitalTwinAtom,
  updateModuleCardsAtom,
  updateLiveIndicatorsAtom,
  digitalTwinAtom,
  liveIndicatorsAtom,
  moduleCardsAtom,
  isProfileCompleteAtom,
  synthesisConfidenceAtom,
  essenceStatementAtom,
  humanDesignTypeAtom,
  primaryArchetypeAtom,
  parseDigitalTwinFromAPI,
  generateLiveIndicators,
  type ModuleCard,
  type LiveIndicator,
  type DigitalTwinSummary,
} from '../../lib/state/dashboard-atoms';
import {
  modulePreferencesAtom,
  enabledModulesAtom,
  MODULE_REGISTRY,
  MODULE_CATEGORIES,
} from '../../lib/state/module-preferences-atoms';
import { apiClient, type ProfileSlot } from '../../lib/api-client';

const { width: SCREEN_WIDTH } = Dimensions.get('window');

// ============================================================================
// MINI PULSING BORDER (for small UI elements)
// ============================================================================

interface MiniPulsingBorderProps {
  color: string;
  intensity?: number;
  style?: any;
  children: React.ReactNode;
}

/**
 * Simple pulsing border for icons and small elements
 */
function MiniPulsingBorder({ color, intensity = 0.5, style, children }: MiniPulsingBorderProps) {
  const pulseValue = useSharedValue(0);
  
  React.useEffect(() => {
    pulseValue.value = withRepeat(
      withTiming(1, { duration: 2000 }),
      -1,
      true
    );
  }, []);
  
  const animatedStyle = useAnimatedStyle(() => ({
    shadowColor: color,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: (pulseValue.value * 0.5 + 0.3) * intensity,
    shadowRadius: pulseValue.value * 8 + 4,
    elevation: 8,
  }));
  
  return (
    <Animated.View style={[style, animatedStyle]}>
      {children}
    </Animated.View>
  );
}
const CARD_WIDTH = (SCREEN_WIDTH - 48) / 2;

// ============================================================================
// MODULE ICONS MAPPING
// ============================================================================

const MODULE_ICONS: Record<string, React.ReactNode> = {
  profiling: <Target size={24} color="#A855F7" />,
  archetypes: <Brain size={24} color="#A855F7" />,
  human_design: <Sparkles size={24} color="#EC4899" />,
  gene_keys: <Zap size={24} color="#F59E0B" />,
  astrology: <Eye size={24} color="#6366F1" />,
  numerology: <Target size={24} color="#8B5CF6" />,
  vision: <Eye size={24} color="#06B6D4" />,
  food_analysis: <Utensils size={24} color="#10B981" />,
  health_metrics: <Activity size={24} color="#EF4444" />,
  finance: <DollarSign size={24} color="#F59E0B" />,
  journaling: <BookOpen size={24} color="#EC4899" />,
  synthesis: <Sparkles size={24} color="#A855F7" />,
  hrm_reasoning: <Brain size={24} color="#6366F1" />,
};

// ============================================================================
// IDENTITY HEXAGON COMPONENT
// ============================================================================

interface HexagonItemProps {
  label: string;
  value: string;
  color: string;
  delay?: number;
}

function HexagonItem({ label, value, color, delay = 0 }: HexagonItemProps) {
  return (
    <Animated.View
      entering={FadeInDown.delay(delay).duration(500)}
      style={styles.hexagonItem}
    >
      <View style={[styles.hexagonDot, { backgroundColor: color }]} />
      <Text style={styles.hexagonLabel}>{label}</Text>
      <Text style={[styles.hexagonValue, { color }]}>{value}</Text>
    </Animated.View>
  );
}

// ============================================================================
// LIVE INDICATOR COMPONENT
// ============================================================================

interface LiveIndicatorCardProps {
  indicator: LiveIndicator;
  index: number;
}

function LiveIndicatorCard({ indicator, index }: LiveIndicatorCardProps) {
  const pulseOpacity = useSharedValue(0.5);
  
  useEffect(() => {
    pulseOpacity.value = withRepeat(
      withSequence(
        withTiming(1, { duration: 1000, easing: Easing.inOut(Easing.ease) }),
        withTiming(0.5, { duration: 1000, easing: Easing.inOut(Easing.ease) })
      ),
      -1,
      true
    );
  }, []);
  
  const pulseStyle = useAnimatedStyle(() => ({
    opacity: pulseOpacity.value,
  }));
  
  return (
    <Animated.View
      entering={SlideInRight.delay(index * 100).duration(400)}
      style={styles.indicatorCard}
    >
      <Animated.View style={[styles.indicatorPulse, { backgroundColor: indicator.color }, pulseStyle]} />
      <Text style={styles.indicatorIcon}>{indicator.icon}</Text>
      <Text style={styles.indicatorValue}>{indicator.value}</Text>
      <Text style={styles.indicatorLabel}>{indicator.label}</Text>
    </Animated.View>
  );
}

// ============================================================================
// MODULE CARD COMPONENT
// ============================================================================

interface ModuleCardComponentProps {
  module: ModuleCard;
  index: number;
}

function ModuleCardComponent({ module, index }: ModuleCardComponentProps) {
  const router = useRouter();
  
  const handlePress = useCallback(() => {
    if (module.quickAction?.route) {
      router.push(module.quickAction.route as any);
    }
  }, [module, router]);
  
  return (
    <Animated.View
      entering={FadeInUp.delay(100 + index * 50).duration(400)}
    >
      <Pressable
        style={[
          styles.moduleCard,
          !module.enabled && styles.moduleCardDisabled,
        ]}
        onPress={handlePress}
        disabled={!module.enabled}
      >
        <View style={[styles.moduleIconContainer, { backgroundColor: `${module.color}20` }]}>
          {MODULE_ICONS[module.id] || <Sparkles size={24} color={module.color as any} />}
        </View>
        <Text style={styles.moduleCardName}>{module.name}</Text>
        <Text style={styles.moduleCardDescription} numberOfLines={2}>
          {module.description}
        </Text>
        {module.enabled && module.quickAction && (
          <View style={styles.moduleCardAction}>
            <Text style={[styles.moduleCardActionText, { color: module.color }]}>
              {module.quickAction.label}
            </Text>
            <ChevronRight size={14} color={module.color as any} />
          </View>
        )}
        {!module.enabled && (
          <View style={styles.moduleCardDisabledBadge}>
            <Text style={styles.moduleCardDisabledText}>Disabled</Text>
          </View>
        )}
      </Pressable>
    </Animated.View>
  );
}

// ============================================================================
// GENESIS CTA COMPONENT
// ============================================================================

function GenesisCTA() {
  const router = useRouter();
  
  return (
    <Animated.View entering={FadeIn.delay(200).duration(600)}>
      <Pressable
        style={styles.genesisCTA}
        onPress={() => router.push('/genesis')}
      >
        <LinearGradient
          colors={['rgba(168, 85, 247, 0.2)', 'rgba(236, 72, 153, 0.2)']}
          start={{ x: 0, y: 0 }}
          end={{ x: 1, y: 1 }}
          style={styles.genesisCTAGradient}
        >
          <View style={styles.genesisCTAContent}>
            <View style={styles.genesisCTAIcon}>
              <MiniPulsingBorder color="#A855F7" intensity={0.7} style={styles.genesisCTAPulse}>
                <Sparkles size={32} color="#A855F7" />
              </MiniPulsingBorder>
            </View>
            <View style={styles.genesisCTAText}>
              <Text style={styles.genesisCTATitle}>Begin Genesis</Text>
              <Text style={styles.genesisCTASubtitle}>
                Create your Digital Twin through guided self-discovery
              </Text>
            </View>
            <ChevronRight size={24} color="#A855F7" />
          </View>
        </LinearGradient>
      </Pressable>
    </Animated.View>
  );
}

// ============================================================================
// MAIN DASHBOARD SCREEN
// ============================================================================

export default function DashboardScreen() {
  const router = useRouter();
  const [isRefreshing, setIsRefreshing] = useState(false);
  
  // Dashboard state
  const dashboardState = useAtomValue(dashboardStateAtom);
  const initDashboard = useSetAtom(initDashboardAtom);
  const updateDigitalTwin = useSetAtom(updateDigitalTwinAtom);
  const updateModuleCards = useSetAtom(updateModuleCardsAtom);
  const updateLiveIndicators = useSetAtom(updateLiveIndicatorsAtom);
  
  // Derived state
  const digitalTwin = useAtomValue(digitalTwinAtom);
  const liveIndicators = useAtomValue(liveIndicatorsAtom);
  const moduleCards = useAtomValue(moduleCardsAtom);
  const isProfileComplete = useAtomValue(isProfileCompleteAtom);
  const synthesisConfidence = useAtomValue(synthesisConfidenceAtom);
  const essence = useAtomValue(essenceStatementAtom);
  const hdType = useAtomValue(humanDesignTypeAtom);
  const primaryArchetype = useAtomValue(primaryArchetypeAtom);
  
  // Module preferences
  const modulePreferences = useAtomValue(modulePreferencesAtom);
  const enabledModules = useAtomValue(enabledModulesAtom);
  
  // Load dashboard data
  const loadDashboardData = useCallback(async () => {
    try {
      // 1. Initialize dashboard from cache
      await initDashboard();
      
      // 2. Try to fetch latest Digital Twin from API
      try {
        const profileList = await apiClient.listProfiles();
        const completedProfile = profileList.profiles.find(
          (p: ProfileSlot) => p.status === 'completed'
        );
        
        if (completedProfile) {
          const loadResponse = await apiClient.loadProfile(completedProfile.slot_id);
          if (loadResponse.digital_twin) {
            const parsedTwin = parseDigitalTwinFromAPI(loadResponse.digital_twin);
            await updateDigitalTwin(parsedTwin);
            
            // Update live indicators
            const indicators = generateLiveIndicators(parsedTwin);
            updateLiveIndicators(indicators);
          }
        }
      } catch (apiError) {
        console.log('[Dashboard] API fetch failed, using cached data:', apiError);
      }
      
      // 3. Build module cards from preferences
      const cards: ModuleCard[] = Object.entries(MODULE_REGISTRY)
        .filter(([id]) => id !== 'profiling' && id !== 'synthesis') // Hide system modules
        .map(([id, module]) => ({
          id: module.id,
          name: module.name,
          icon: module.icon,
          description: module.description,
          color: MODULE_CATEGORIES[module.category].color,
          enabled: modulePreferences[module.id]?.enabled ?? false,
          hasData: false, // TODO: Check if module has user data
          quickAction: getModuleQuickAction(module.id),
        }));
      
      updateModuleCards(cards);
      
    } catch (error) {
      console.error('[Dashboard] Load error:', error);
    }
  }, [initDashboard, updateDigitalTwin, updateModuleCards, updateLiveIndicators, modulePreferences]);
  
  // Get quick action for module
  const getModuleQuickAction = (moduleId: string): { label: string; route: string } | undefined => {
    switch (moduleId) {
      case 'human_design':
        return { label: 'View Chart', route: '/modules/human-design' };
      case 'archetypes':
        return { label: 'Explore', route: '/modules/archetypes' };
      case 'food_analysis':
        return { label: 'Scan Food', route: '/modules/nutrition' };
      case 'journaling':
        return { label: 'New Entry', route: '/modules/journal' };
      case 'finance':
        return { label: 'Track', route: '/modules/finance' };
      case 'health_metrics':
        return { label: 'Log', route: '/modules/health' };
      default:
        return undefined;
    }
  };
  
  // Initial load
  useEffect(() => {
    loadDashboardData();
  }, []);
  
  // Refresh handler
  const handleRefresh = useCallback(async () => {
    setIsRefreshing(true);
    await loadDashboardData();
    setIsRefreshing(false);
  }, [loadDashboardData]);
  
  // Loading state
  if (dashboardState.isLoading && !digitalTwin) {
    return (
      <SafeAreaView style={styles.safeArea}>
        <View style={styles.loadingContainer}>
          <Spinner size="large" color="$purple10" />
          <Text style={styles.loadingText}>Initializing Dashboard...</Text>
        </View>
      </SafeAreaView>
    );
  }
  
  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <ScrollView
        style={styles.container}
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={isRefreshing}
            onRefresh={handleRefresh}
            tintColor="#A855F7"
            colors={['#A855F7']}
          />
        }
      >
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerLeft}>
            <Text style={styles.headerTitle}>Sovereign</Text>
            <Text style={styles.headerSubtitle}>Digital Twin Portal</Text>
          </View>
          <Pressable
            style={styles.settingsButton}
            onPress={() => router.push('/settings')}
          >
            <Settings size={22} color="rgba(255,255,255,0.7)" />
          </Pressable>
        </View>
        
        {/* Genesis CTA if profile incomplete */}
        {!isProfileComplete && <GenesisCTA />}
        
        {/* Digital Twin Portal */}
        {isProfileComplete && digitalTwin && (
          <Animated.View entering={FadeIn.delay(100).duration(600)}>
            <View style={styles.portalContainer}>
              <LinearGradient
                colors={['rgba(168, 85, 247, 0.1)', 'rgba(6, 182, 212, 0.1)']}
                start={{ x: 0, y: 0 }}
                end={{ x: 1, y: 1 }}
                style={styles.portalGradient}
              >
                {/* Essence Statement */}
                <View style={styles.essenceContainer}>
                  <MiniPulsingBorder color="#A855F7" intensity={0.5} style={styles.essencePulse}>
                    <Sparkles size={28} color="#A855F7" />
                  </MiniPulsingBorder>
                  <Text style={styles.essenceText}>{essence}</Text>
                </View>
                
                {/* Identity Hexagon */}
                <View style={styles.hexagonContainer}>
                  {hdType && (
                    <HexagonItem
                      label="HD Type"
                      value={hdType}
                      color="#EC4899"
                      delay={100}
                    />
                  )}
                  {primaryArchetype && (
                    <HexagonItem
                      label="Archetype"
                      value={primaryArchetype}
                      color="#A855F7"
                      delay={200}
                    />
                  )}
                  {digitalTwin.humanDesign?.strategy && (
                    <HexagonItem
                      label="Strategy"
                      value={digitalTwin.humanDesign.strategy}
                      color="#06B6D4"
                      delay={300}
                    />
                  )}
                  {digitalTwin.humanDesign?.authority && (
                    <HexagonItem
                      label="Authority"
                      value={digitalTwin.humanDesign.authority}
                      color="#10B981"
                      delay={400}
                    />
                  )}
                </View>
                
                {/* Synthesis Confidence */}
                <View style={styles.confidenceContainer}>
                  <View style={styles.confidenceBar}>
                    <View 
                      style={[
                        styles.confidenceFill, 
                        { width: `${synthesisConfidence}%` }
                      ]} 
                    />
                  </View>
                  <Text style={styles.confidenceText}>
                    {synthesisConfidence}% Understanding
                  </Text>
                </View>
              </LinearGradient>
            </View>
          </Animated.View>
        )}
        
        {/* Live Indicators */}
        {liveIndicators.length > 0 && (
          <View style={styles.indicatorsSection}>
            <Text style={styles.sectionTitle}>Live Synthesis</Text>
            <ScrollView
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.indicatorsScroll}
            >
              {liveIndicators.map((indicator, index) => (
                <LiveIndicatorCard
                  key={indicator.id}
                  indicator={indicator}
                  index={index}
                />
              ))}
            </ScrollView>
          </View>
        )}
        
        {/* Modules Grid */}
        <View style={styles.modulesSection}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Modules</Text>
            <Link href="/settings/modules" asChild>
              <Pressable style={styles.sectionAction}>
                <Text style={styles.sectionActionText}>Manage</Text>
                <ChevronRight size={16} color="#A855F7" />
              </Pressable>
            </Link>
          </View>
          
          <View style={styles.modulesGrid}>
            {moduleCards
              .filter(m => m.enabled)
              .slice(0, 6)
              .map((module, index) => (
                <ModuleCardComponent
                  key={module.id}
                  module={module}
                  index={index}
                />
              ))}
          </View>
          
          {moduleCards.filter(m => m.enabled).length === 0 && (
            <View style={styles.emptyModules}>
              <Text style={styles.emptyModulesText}>
                No modules enabled. Enable modules in settings.
              </Text>
              <Link href="/settings/modules" asChild>
                <Pressable style={styles.enableModulesButton}>
                  <Text style={styles.enableModulesText}>Enable Modules</Text>
                </Pressable>
              </Link>
            </View>
          )}
        </View>
        
        {/* Quick Actions */}
        <View style={styles.quickActionsSection}>
          <Text style={styles.sectionTitle}>Quick Actions</Text>
          <View style={styles.quickActionsGrid}>
            <Pressable
              style={styles.quickActionCard}
              onPress={() => router.push('/genesis')}
            >
              <View style={[styles.quickActionIcon, { backgroundColor: 'rgba(168, 85, 247, 0.2)' }]}>
                <Play size={20} color="#A855F7" />
              </View>
              <Text style={styles.quickActionLabel}>
                {isProfileComplete ? 'Refine Profile' : 'Start Genesis'}
              </Text>
            </Pressable>
            
            <Pressable
              style={styles.quickActionCard}
              onPress={handleRefresh}
            >
              <View style={[styles.quickActionIcon, { backgroundColor: 'rgba(6, 182, 212, 0.2)' }]}>
                <RefreshCw size={20} color="#06B6D4" />
              </View>
              <Text style={styles.quickActionLabel}>Refresh</Text>
            </Pressable>
            
            <Pressable
              style={styles.quickActionCard}
              onPress={() => router.push('/settings')}
            >
              <View style={[styles.quickActionIcon, { backgroundColor: 'rgba(107, 114, 128, 0.2)' }]}>
                <Settings size={20} color="#6B7280" />
              </View>
              <Text style={styles.quickActionLabel}>Settings</Text>
            </Pressable>
          </View>
        </View>
        
        {/* Footer */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            Tap the floating button to chat with Sovereign
          </Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

// ============================================================================
// STYLES
// ============================================================================

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#050505',
  },
  container: {
    flex: 1,
    backgroundColor: '#050505',
  },
  contentContainer: {
    paddingBottom: 120, // Space for FAB
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
  },
  loadingText: {
    fontSize: 16,
    color: 'rgba(255,255,255,0.5)',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  
  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 16,
  },
  headerLeft: {
    gap: 2,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#FFFFFF',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  headerSubtitle: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.5)',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  settingsButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: 'rgba(255,255,255,0.1)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  
  // Genesis CTA
  genesisCTA: {
    marginHorizontal: 16,
    marginBottom: 20,
    borderRadius: 20,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(168, 85, 247, 0.3)',
  },
  genesisCTAGradient: {
    padding: 20,
  },
  genesisCTAContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
  },
  genesisCTAIcon: {
    width: 60,
    height: 60,
  },
  genesisCTAPulse: {
    width: 60,
    height: 60,
    borderRadius: 30,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(168, 85, 247, 0.2)',
  },
  genesisCTAText: {
    flex: 1,
    gap: 4,
  },
  genesisCTATitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#FFFFFF',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  genesisCTASubtitle: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.6)',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  
  // Portal
  portalContainer: {
    marginHorizontal: 16,
    marginBottom: 20,
    borderRadius: 20,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(168, 85, 247, 0.2)',
  },
  portalGradient: {
    padding: 20,
  },
  
  // Essence
  essenceContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 20,
  },
  essencePulse: {
    width: 50,
    height: 50,
    borderRadius: 25,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(168, 85, 247, 0.2)',
  },
  essenceText: {
    flex: 1,
    fontSize: 16,
    fontWeight: '500',
    color: '#FFFFFF',
    fontStyle: 'italic',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  
  // Hexagon
  hexagonContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    marginBottom: 20,
  },
  hexagonItem: {
    width: (SCREEN_WIDTH - 80) / 2,
    padding: 12,
    backgroundColor: 'rgba(0,0,0,0.3)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
  },
  hexagonDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    marginBottom: 6,
  },
  hexagonLabel: {
    fontSize: 11,
    color: 'rgba(255,255,255,0.5)',
    marginBottom: 2,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  hexagonValue: {
    fontSize: 15,
    fontWeight: '600',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  
  // Confidence
  confidenceContainer: {
    gap: 8,
  },
  confidenceBar: {
    height: 6,
    backgroundColor: 'rgba(255,255,255,0.1)',
    borderRadius: 3,
    overflow: 'hidden',
  },
  confidenceFill: {
    height: '100%',
    backgroundColor: '#A855F7',
    borderRadius: 3,
  },
  confidenceText: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.5)',
    textAlign: 'center',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  
  // Indicators
  indicatorsSection: {
    marginBottom: 24,
  },
  indicatorsScroll: {
    paddingHorizontal: 16,
    gap: 12,
  },
  indicatorCard: {
    width: 100,
    padding: 14,
    backgroundColor: '#0A0A0A',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
    alignItems: 'center',
    overflow: 'hidden',
  },
  indicatorPulse: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 3,
  },
  indicatorIcon: {
    fontSize: 20,
    marginBottom: 8,
  },
  indicatorValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  indicatorLabel: {
    fontSize: 11,
    color: 'rgba(255,255,255,0.5)',
    marginTop: 4,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  
  // Section
  sectionTitle: {
    fontSize: 18,
    fontWeight: '700',
    color: '#FFFFFF',
    paddingHorizontal: 16,
    marginBottom: 12,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingRight: 16,
    marginBottom: 12,
  },
  sectionAction: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  sectionActionText: {
    fontSize: 14,
    color: '#A855F7',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  
  // Modules
  modulesSection: {
    marginBottom: 24,
  },
  modulesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 16,
    gap: 12,
  },
  moduleCard: {
    width: CARD_WIDTH,
    padding: 16,
    backgroundColor: '#0A0A0A',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
    gap: 10,
  },
  moduleCardDisabled: {
    opacity: 0.5,
  },
  moduleIconContainer: {
    width: 44,
    height: 44,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  moduleCardName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#FFFFFF',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  moduleCardDescription: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.5)',
    lineHeight: 16,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  moduleCardAction: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    marginTop: 4,
  },
  moduleCardActionText: {
    fontSize: 13,
    fontWeight: '500',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  moduleCardDisabledBadge: {
    position: 'absolute',
    top: 8,
    right: 8,
    paddingHorizontal: 8,
    paddingVertical: 4,
    backgroundColor: 'rgba(107, 114, 128, 0.3)',
    borderRadius: 8,
  },
  moduleCardDisabledText: {
    fontSize: 10,
    color: 'rgba(255,255,255,0.4)',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  emptyModules: {
    alignItems: 'center',
    paddingVertical: 32,
    paddingHorizontal: 16,
    gap: 16,
  },
  emptyModulesText: {
    fontSize: 14,
    color: 'rgba(255,255,255,0.5)',
    textAlign: 'center',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  enableModulesButton: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    backgroundColor: 'rgba(168, 85, 247, 0.2)',
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#A855F7',
  },
  enableModulesText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#A855F7',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  
  // Quick Actions
  quickActionsSection: {
    marginBottom: 24,
  },
  quickActionsGrid: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    gap: 12,
  },
  quickActionCard: {
    flex: 1,
    alignItems: 'center',
    padding: 16,
    backgroundColor: '#0A0A0A',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
    gap: 10,
  },
  quickActionIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    alignItems: 'center',
    justifyContent: 'center',
  },
  quickActionLabel: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.7)',
    textAlign: 'center',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  
  // Footer
  footer: {
    alignItems: 'center',
    paddingVertical: 16,
  },
  footerText: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.3)',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
});
