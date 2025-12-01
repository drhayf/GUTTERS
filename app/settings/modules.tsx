/**
 * Module Preferences Settings Screen
 * 
 * Comprehensive UI for managing enabled/disabled modules.
 * Features:
 * - Category-based grouping (Wisdom, Health, Life, System)
 * - Visual dependency indicators
 * - Preset configurations
 * - Beta/experimental badges
 * - Smooth toggle animations
 * 
 * Follows the Void Theme aesthetic with deep dark backgrounds
 * and accent colors matching the category system.
 */

import React, { useEffect, useState, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  Pressable,
  Switch,
  Platform,
  Alert,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Stack } from 'expo-router';
import { useAtom, useAtomValue, useSetAtom } from 'jotai';
import {
  ChevronDown,
  ChevronUp,
  Info,
  Sparkles,
  RefreshCw,
  AlertTriangle,
} from '@tamagui/lucide-icons';

import {
  modulePreferencesAtom,
  initModulePreferencesAtom,
  toggleModuleAtom,
  applyPresetAtom,
  resetModulePreferencesAtom,
  enabledModulesAtom,
  moduleCountsByCategoryAtom,
  MODULE_REGISTRY,
  MODULE_CATEGORIES,
  MODULE_PRESETS,
  getModulesByCategory,
  getDependenciesToEnable,
  getDependentsToDisable,
  type ModuleCategory,
  type ModuleDefinition,
  type PresetKey,
  type AgentCapability,
} from '../../lib/state/module-preferences-atoms';

// ============================================================================
// COMPONENTS
// ============================================================================

interface ModuleItemProps {
  module: ModuleDefinition;
  isEnabled: boolean;
  onToggle: () => void;
  dependenciesToEnable: AgentCapability[];
  dependentsToDisable: AgentCapability[];
}

function ModuleItem({
  module,
  isEnabled,
  onToggle,
  dependenciesToEnable,
  dependentsToDisable,
}: ModuleItemProps) {
  const [expanded, setExpanded] = useState(false);
  
  const handleToggle = useCallback(() => {
    // Show confirmation if there are dependencies/dependents
    if (!isEnabled && dependenciesToEnable.length > 0) {
      const deps = dependenciesToEnable
        .map(d => MODULE_REGISTRY[d].name)
        .join(', ');
      Alert.alert(
        'Enable Dependencies',
        `Enabling ${module.name} will also enable: ${deps}`,
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Enable All', onPress: onToggle },
        ]
      );
    } else if (isEnabled && dependentsToDisable.length > 0) {
      const deps = dependentsToDisable
        .map(d => MODULE_REGISTRY[d].name)
        .join(', ');
      Alert.alert(
        'Disable Dependents',
        `Disabling ${module.name} will also disable: ${deps}`,
        [
          { text: 'Cancel', style: 'cancel' },
          { text: 'Disable All', onPress: onToggle },
        ]
      );
    } else {
      onToggle();
    }
  }, [isEnabled, dependenciesToEnable, dependentsToDisable, module.name, onToggle]);
  
  const categoryColor = MODULE_CATEGORIES[module.category].color;
  
  return (
    <View style={styles.moduleItem}>
      <Pressable
        style={styles.moduleHeader}
        onPress={() => module.longDescription && setExpanded(!expanded)}
      >
        {/* Icon */}
        <View style={[styles.moduleIcon, { backgroundColor: `${categoryColor}20` }]}>
          <Text style={styles.moduleIconText}>{module.icon}</Text>
        </View>
        
        {/* Content */}
        <View style={styles.moduleContent}>
          <View style={styles.moduleTitleRow}>
            <Text style={styles.moduleName}>{module.name}</Text>
            {module.isBeta && (
              <View style={styles.betaBadge}>
                <Text style={styles.betaBadgeText}>BETA</Text>
              </View>
            )}
            {module.isCore && (
              <View style={styles.coreBadge}>
                <Text style={styles.coreBadgeText}>CORE</Text>
              </View>
            )}
          </View>
          <Text style={styles.moduleDescription}>{module.description}</Text>
          
          {/* Dependencies indicator */}
          {module.dependencies.length > 0 && (
            <Text style={styles.dependencyText}>
              Requires: {module.dependencies.map(d => MODULE_REGISTRY[d].name).join(', ')}
            </Text>
          )}
        </View>
        
        {/* Toggle or expand indicator */}
        <View style={styles.moduleActions}>
          {module.isCore ? (
            <View style={styles.lockedIndicator}>
              <Text style={styles.lockedText}>Always On</Text>
            </View>
          ) : (
            <Switch
              value={isEnabled}
              onValueChange={handleToggle}
              trackColor={{ false: '#333', true: `${categoryColor}60` }}
              thumbColor={isEnabled ? categoryColor : '#888'}
              ios_backgroundColor="#333"
            />
          )}
          
          {module.longDescription && (
            <Pressable
              style={styles.expandButton}
              onPress={() => setExpanded(!expanded)}
            >
              {expanded ? (
                <ChevronUp size={16} color="rgba(255,255,255,0.4)" />
              ) : (
                <ChevronDown size={16} color="rgba(255,255,255,0.4)" />
              )}
            </Pressable>
          )}
        </View>
      </Pressable>
      
      {/* Expanded description */}
      {expanded && module.longDescription && (
        <View style={styles.expandedContent}>
          <Text style={styles.longDescription}>{module.longDescription}</Text>
        </View>
      )}
    </View>
  );
}

interface CategorySectionProps {
  category: ModuleCategory;
  modules: ModuleDefinition[];
  preferences: Record<string, { enabled: boolean }>;
  onToggle: (moduleId: AgentCapability) => void;
}

function CategorySection({
  category,
  modules,
  preferences,
  onToggle,
}: CategorySectionProps) {
  const [collapsed, setCollapsed] = useState(false);
  const categoryInfo = MODULE_CATEGORIES[category];
  const enabledCount = modules.filter(m => preferences[m.id]?.enabled).length;
  
  return (
    <View style={styles.categorySection}>
      {/* Category Header */}
      <Pressable
        style={styles.categoryHeader}
        onPress={() => setCollapsed(!collapsed)}
      >
        <View style={styles.categoryTitleRow}>
          <Text style={styles.categoryIcon}>{categoryInfo.icon}</Text>
          <View style={styles.categoryTitleContent}>
            <Text style={[styles.categoryTitle, { color: categoryInfo.color }]}>
              {categoryInfo.name}
            </Text>
            <Text style={styles.categorySubtitle}>
              {enabledCount} of {modules.length} enabled
            </Text>
          </View>
        </View>
        
        {collapsed ? (
          <ChevronDown size={20} color="rgba(255,255,255,0.4)" />
        ) : (
          <ChevronUp size={20} color="rgba(255,255,255,0.4)" />
        )}
      </Pressable>
      
      {/* Category Description */}
      {!collapsed && (
        <Text style={styles.categoryDescription}>{categoryInfo.description}</Text>
      )}
      
      {/* Modules */}
      {!collapsed && (
        <View style={styles.modulesContainer}>
          {modules.map(module => (
            <ModuleItem
              key={module.id}
              module={module}
              isEnabled={preferences[module.id]?.enabled ?? false}
              onToggle={() => onToggle(module.id)}
              dependenciesToEnable={getDependenciesToEnable(module.id, preferences as any)}
              dependentsToDisable={getDependentsToDisable(module.id, preferences as any)}
            />
          ))}
        </View>
      )}
    </View>
  );
}

interface PresetButtonProps {
  presetKey: PresetKey;
  isActive: boolean;
  onPress: () => void;
}

function PresetButton({ presetKey, isActive, onPress }: PresetButtonProps) {
  const preset = MODULE_PRESETS[presetKey];
  
  return (
    <Pressable
      style={[
        styles.presetButton,
        isActive && styles.presetButtonActive,
      ]}
      onPress={onPress}
    >
      <Text style={styles.presetIcon}>{preset.icon}</Text>
      <Text style={[
        styles.presetName,
        isActive && styles.presetNameActive,
      ]}>
        {preset.name}
      </Text>
    </Pressable>
  );
}

// ============================================================================
// MAIN SCREEN
// ============================================================================

export default function ModulesScreen() {
  const [isLoading, setIsLoading] = useState(true);
  const [preferences, setPreferences] = useAtom(modulePreferencesAtom);
  const initPreferences = useSetAtom(initModulePreferencesAtom);
  const toggleModule = useSetAtom(toggleModuleAtom);
  const applyPreset = useSetAtom(applyPresetAtom);
  const resetPreferences = useSetAtom(resetModulePreferencesAtom);
  const enabledModules = useAtomValue(enabledModulesAtom);
  const moduleCounts = useAtomValue(moduleCountsByCategoryAtom);
  
  // Initialize on mount
  useEffect(() => {
    const init = async () => {
      await initPreferences();
      setIsLoading(false);
    };
    init();
  }, [initPreferences]);
  
  // Determine active preset
  const getActivePreset = useCallback((): PresetKey | null => {
    for (const [key, preset] of Object.entries(MODULE_PRESETS)) {
      const presetSet = new Set(preset.enabledModules);
      const enabledSet = new Set(enabledModules);
      
      // Check if enabled modules match preset exactly
      if (presetSet.size === enabledSet.size) {
        let matches = true;
        for (const mod of preset.enabledModules) {
          if (!enabledSet.has(mod)) {
            matches = false;
            break;
          }
        }
        if (matches) return key as PresetKey;
      }
    }
    return null;
  }, [enabledModules]);
  
  const handleReset = useCallback(() => {
    Alert.alert(
      'Reset to Defaults',
      'This will reset all module preferences to their default state.',
      [
        { text: 'Cancel', style: 'cancel' },
        { 
          text: 'Reset', 
          style: 'destructive',
          onPress: () => resetPreferences(),
        },
      ]
    );
  }, [resetPreferences]);
  
  const activePreset = getActivePreset();
  
  // Get modules by category
  const wisdomModules = getModulesByCategory('wisdom');
  const healthModules = getModulesByCategory('health');
  const lifeModules = getModulesByCategory('life');
  const systemModules = getModulesByCategory('system');
  
  if (isLoading) {
    return (
      <SafeAreaView style={styles.safeArea} edges={['bottom']}>
        <Stack.Screen options={{ title: 'Modules' }} />
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#A855F7" />
          <Text style={styles.loadingText}>Loading preferences...</Text>
        </View>
      </SafeAreaView>
    );
  }
  
  return (
    <SafeAreaView style={styles.safeArea} edges={['bottom']}>
      <Stack.Screen 
        options={{ 
          title: 'Modules',
          headerStyle: { backgroundColor: '#0A0A0A' },
          headerTintColor: '#FFFFFF',
        }} 
      />
      
      <ScrollView 
        style={styles.container} 
        contentContainerStyle={styles.contentContainer}
        showsVerticalScrollIndicator={false}
      >
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>Enabled Modules</Text>
          <Text style={styles.headerSubtitle}>
            {moduleCounts.total} modules active
          </Text>
        </View>
        
        {/* Stats Row */}
        <View style={styles.statsRow}>
          <View style={styles.statItem}>
            <Text style={[styles.statValue, { color: MODULE_CATEGORIES.wisdom.color }]}>
              {moduleCounts.wisdom}
            </Text>
            <Text style={styles.statLabel}>Wisdom</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={[styles.statValue, { color: MODULE_CATEGORIES.health.color }]}>
              {moduleCounts.health}
            </Text>
            <Text style={styles.statLabel}>Health</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={[styles.statValue, { color: MODULE_CATEGORIES.life.color }]}>
              {moduleCounts.life}
            </Text>
            <Text style={styles.statLabel}>Life</Text>
          </View>
          <View style={styles.statItem}>
            <Text style={[styles.statValue, { color: MODULE_CATEGORIES.system.color }]}>
              {moduleCounts.system}
            </Text>
            <Text style={styles.statLabel}>System</Text>
          </View>
        </View>
        
        {/* Presets */}
        <View style={styles.presetsSection}>
          <View style={styles.presetsTitleRow}>
            <Sparkles size={18} color="#A855F7" />
            <Text style={styles.presetsTitle}>Quick Presets</Text>
          </View>
          
          <ScrollView 
            horizontal 
            showsHorizontalScrollIndicator={false}
            contentContainerStyle={styles.presetsScroll}
          >
            {(Object.keys(MODULE_PRESETS) as PresetKey[]).map(key => (
              <PresetButton
                key={key}
                presetKey={key}
                isActive={activePreset === key}
                onPress={() => applyPreset(key)}
              />
            ))}
          </ScrollView>
        </View>
        
        {/* Info Banner */}
        <View style={styles.infoBanner}>
          <Info size={16} color="#06B6D4" />
          <Text style={styles.infoText}>
            Core modules cannot be disabled. Toggling a module may enable/disable its dependencies.
          </Text>
        </View>
        
        {/* Categories */}
        <View style={styles.categoriesContainer}>
          <CategorySection
            category="wisdom"
            modules={wisdomModules}
            preferences={preferences}
            onToggle={toggleModule}
          />
          
          <CategorySection
            category="health"
            modules={healthModules}
            preferences={preferences}
            onToggle={toggleModule}
          />
          
          <CategorySection
            category="life"
            modules={lifeModules}
            preferences={preferences}
            onToggle={toggleModule}
          />
          
          <CategorySection
            category="system"
            modules={systemModules}
            preferences={preferences}
            onToggle={toggleModule}
          />
        </View>
        
        {/* Reset Button */}
        <Pressable style={styles.resetButton} onPress={handleReset}>
          <RefreshCw size={18} color="#EF4444" />
          <Text style={styles.resetButtonText}>Reset to Defaults</Text>
        </Pressable>
        
        {/* Footer */}
        <View style={styles.footer}>
          <AlertTriangle size={14} color="rgba(255,255,255,0.3)" />
          <Text style={styles.footerText}>
            Beta modules may have limited functionality
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
    paddingBottom: 40,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
  },
  loadingText: {
    color: 'rgba(255,255,255,0.5)',
    fontSize: 14,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  
  // Header
  header: {
    padding: 16,
    paddingTop: 8,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: '700',
    color: '#FFFFFF',
    marginBottom: 4,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  headerSubtitle: {
    fontSize: 15,
    color: 'rgba(255,255,255,0.5)',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  
  // Stats Row
  statsRow: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    marginBottom: 20,
    gap: 12,
  },
  statItem: {
    flex: 1,
    backgroundColor: '#0A0A0A',
    borderRadius: 12,
    padding: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
  },
  statValue: {
    fontSize: 24,
    fontWeight: '700',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  statLabel: {
    fontSize: 11,
    color: 'rgba(255,255,255,0.5)',
    marginTop: 2,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  
  // Presets
  presetsSection: {
    marginHorizontal: 16,
    marginBottom: 16,
  },
  presetsTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  presetsTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: '#FFFFFF',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  presetsScroll: {
    gap: 8,
  },
  presetButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#0A0A0A',
    borderRadius: 20,
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
    gap: 6,
  },
  presetButtonActive: {
    backgroundColor: 'rgba(168, 85, 247, 0.15)',
    borderColor: '#A855F7',
  },
  presetIcon: {
    fontSize: 14,
  },
  presetName: {
    fontSize: 13,
    fontWeight: '500',
    color: 'rgba(255,255,255,0.7)',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  presetNameActive: {
    color: '#A855F7',
  },
  
  // Info Banner
  infoBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    marginHorizontal: 16,
    marginBottom: 20,
    padding: 12,
    backgroundColor: 'rgba(6, 182, 212, 0.1)',
    borderRadius: 10,
    borderWidth: 1,
    borderColor: 'rgba(6, 182, 212, 0.2)',
  },
  infoText: {
    flex: 1,
    fontSize: 13,
    color: 'rgba(255,255,255,0.7)',
    lineHeight: 18,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  
  // Categories
  categoriesContainer: {
    gap: 16,
    paddingHorizontal: 16,
  },
  categorySection: {
    backgroundColor: '#0A0A0A',
    borderRadius: 16,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.08)',
    overflow: 'hidden',
  },
  categoryHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 14,
  },
  categoryTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  categoryIcon: {
    fontSize: 24,
  },
  categoryTitleContent: {
    gap: 2,
  },
  categoryTitle: {
    fontSize: 16,
    fontWeight: '600',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  categorySubtitle: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.4)',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  categoryDescription: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.5)',
    paddingHorizontal: 14,
    paddingBottom: 12,
    lineHeight: 18,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  
  // Modules
  modulesContainer: {
    borderTopWidth: 1,
    borderTopColor: 'rgba(255,255,255,0.06)',
  },
  moduleItem: {
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.06)',
  },
  moduleHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 12,
    gap: 12,
  },
  moduleIcon: {
    width: 40,
    height: 40,
    borderRadius: 10,
    alignItems: 'center',
    justifyContent: 'center',
  },
  moduleIconText: {
    fontSize: 20,
  },
  moduleContent: {
    flex: 1,
    gap: 2,
  },
  moduleTitleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  moduleName: {
    fontSize: 15,
    fontWeight: '600',
    color: '#FFFFFF',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  betaBadge: {
    backgroundColor: 'rgba(245, 158, 11, 0.2)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  betaBadgeText: {
    fontSize: 9,
    fontWeight: '700',
    color: '#F59E0B',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  coreBadge: {
    backgroundColor: 'rgba(107, 114, 128, 0.2)',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
  },
  coreBadgeText: {
    fontSize: 9,
    fontWeight: '700',
    color: '#6B7280',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  moduleDescription: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.5)',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  dependencyText: {
    fontSize: 11,
    color: 'rgba(168, 85, 247, 0.7)',
    marginTop: 4,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  moduleActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  lockedIndicator: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    backgroundColor: 'rgba(107, 114, 128, 0.15)',
    borderRadius: 6,
  },
  lockedText: {
    fontSize: 11,
    color: 'rgba(255,255,255,0.4)',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  expandButton: {
    padding: 4,
  },
  expandedContent: {
    paddingHorizontal: 64,
    paddingBottom: 12,
  },
  longDescription: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.6)',
    lineHeight: 20,
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  
  // Reset Button
  resetButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 24,
    marginHorizontal: 16,
    padding: 14,
    backgroundColor: 'rgba(239, 68, 68, 0.1)',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: 'rgba(239, 68, 68, 0.2)',
  },
  resetButtonText: {
    fontSize: 15,
    fontWeight: '600',
    color: '#EF4444',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
  
  // Footer
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    marginTop: 24,
    padding: 16,
  },
  footerText: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.3)',
    fontFamily: Platform.OS === 'ios' ? 'Avenir Next' : undefined,
  },
});
