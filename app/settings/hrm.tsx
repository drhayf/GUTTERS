/**
 * HRM (Hierarchical Reasoning Model) Settings Screen
 * 
 * High-fidelity configuration UI inspired by sapientinc/HRM architecture.
 * Uses React Native primitives with StyleSheet for reliable rendering.
 */
import { useState, useCallback, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  Pressable,
  Switch,
  Alert,
  StyleSheet,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAtom, useAtomValue, useSetAtom } from 'jotai';
import Slider from '@react-native-community/slider';
import {
  Brain,
  Zap,
  Target,
  Layers,
  Settings2,
  RotateCcw,
  ChevronDown,
  ChevronUp,
  Eye,
  Activity,
  Gauge,
} from '@tamagui/lucide-icons';
import type { ColorTokens } from '@tamagui/core';

// Helper to cast hex colors to Tamagui's expected type
const iconColor = (hex: string) => hex as unknown as ColorTokens;

import {
  hrmConfigAtom,
  initHrmConfigAtom,
  updateHrmConfigAtom,
  hrmCurrentPresetAtom,
  applyHrmPresetAtom,
  resetHrmConfigAtom,
  HRM_PRESETS,
  type HRMConfig,
  type HRMPresetKey,
  type ThinkingLevel,
} from '../../lib/state/hrm-atoms';

// ============================================================================
// Constants
// ============================================================================

const COLORS = {
  background: '#050505',
  card: '#111111',
  border: '#333333',
  borderActive: '#7C3AED',
  text: '#FFFFFF',
  textMuted: '#9CA3AF',
  purple: '#7C3AED',
  purpleDark: '#581C87',
  cyan: '#06B6D4',
  orange: '#EA580C',
  green: '#16A34A',
  pink: '#EC4899',
};

// ============================================================================
// Components
// ============================================================================

interface IconBoxProps {
  children: React.ReactNode;
  color?: string;
}

function IconBox({ children, color = COLORS.purple }: IconBoxProps) {
  return (
    <View style={[styles.iconBox, { backgroundColor: color }]}>
      {children}
    </View>
  );
}

interface CardProps {
  children: React.ReactNode;
  active?: boolean;
}

function Card({ children, active }: CardProps) {
  return (
    <View style={[styles.card, active && styles.cardActive]}>
      {children}
    </View>
  );
}

// ============================================================================
// Preset Selector
// ============================================================================

interface PresetSelectorProps {
  currentPreset: HRMPresetKey | 'custom';
  onSelectPreset: (preset: HRMPresetKey) => void;
}

function PresetSelector({ currentPreset, onSelectPreset }: PresetSelectorProps) {
  return (
    <Card>
      <View style={styles.sectionHeader}>
        <IconBox color={COLORS.cyan}>
          <Zap size={20} color="white" />
        </IconBox>
        <View style={styles.sectionHeaderText}>
          <Text style={styles.sectionTitle}>Quick Presets</Text>
          <Text style={styles.sectionSubtitle}>Choose a reasoning profile</Text>
        </View>
      </View>
      
      <View style={styles.presetsRow}>
        {(Object.entries(HRM_PRESETS) as [HRMPresetKey, typeof HRM_PRESETS.fast][]).map(([key, preset]) => (
          <Pressable key={key} onPress={() => onSelectPreset(key)}>
            <View style={[
              styles.presetChip,
              currentPreset === key && styles.presetChipActive,
            ]}>
              <Text style={[
                styles.presetChipText,
                currentPreset === key && styles.presetChipTextActive,
              ]}>
                {preset.name}
              </Text>
            </View>
          </Pressable>
        ))}
        
        {currentPreset === 'custom' && (
          <View style={[styles.presetChip, styles.presetChipCustom]}>
            <Text style={styles.presetChipTextActive}>✨ Custom</Text>
          </View>
        )}
      </View>
    </Card>
  );
}

// ============================================================================
// Toggle Section
// ============================================================================

interface ToggleSectionProps {
  enabled: boolean;
  onToggle: (enabled: boolean) => void;
  thinkingLevel: ThinkingLevel;
  onThinkingLevelChange: (level: ThinkingLevel) => void;
}

function ToggleSection({ enabled, onToggle, thinkingLevel, onThinkingLevelChange }: ToggleSectionProps) {
  return (
    <Card active={enabled}>
      <View style={styles.toggleRow}>
        <View style={styles.toggleLeft}>
          <IconBox color={enabled ? COLORS.purple : '#374151'}>
            <Brain size={20} color="white" />
          </IconBox>
          <View style={styles.toggleText}>
            <Text style={styles.sectionTitle}>HRM Enabled</Text>
            <Text style={styles.sectionSubtitle}>Hierarchical Reasoning Model</Text>
          </View>
        </View>
        
        <Switch
          value={enabled}
          onValueChange={onToggle}
          trackColor={{ false: '#374151', true: COLORS.purple }}
          thumbColor="white"
        />
      </View>
      
      {enabled && (
        <View style={styles.thinkingLevelContainer}>
          <View style={styles.separator} />
          <Text style={styles.thinkingLevelLabel}>Thinking Level</Text>
          
          <View style={styles.thinkingLevelRow}>
            <Pressable style={{ flex: 1 }} onPress={() => onThinkingLevelChange('low')}>
              <View style={[
                styles.thinkingLevelOption,
                thinkingLevel === 'low' && styles.thinkingLevelOptionActive,
                thinkingLevel === 'low' && { backgroundColor: COLORS.cyan },
              ]}>
                <Zap size={20} color="white" />
                <Text style={styles.thinkingLevelOptionTitle}>Low</Text>
                <Text style={styles.thinkingLevelOptionDesc}>Fast, single-pass</Text>
              </View>
            </Pressable>
            
            <Pressable style={{ flex: 1 }} onPress={() => onThinkingLevelChange('high')}>
              <View style={[
                styles.thinkingLevelOption,
                thinkingLevel === 'high' && styles.thinkingLevelOptionActive,
                thinkingLevel === 'high' && { backgroundColor: COLORS.purple },
              ]}>
                <Brain size={20} color="white" />
                <Text style={styles.thinkingLevelOptionTitle}>High</Text>
                <Text style={styles.thinkingLevelOptionDesc}>Deep, multi-pass</Text>
              </View>
            </Pressable>
          </View>
        </View>
      )}
    </Card>
  );
}

// ============================================================================
// Slider Setting
// ============================================================================

interface SliderSettingProps {
  label: string;
  description: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (value: number) => void;
  formatValue?: (value: number) => string;
}

function SliderSetting({
  label,
  description,
  value,
  min,
  max,
  step,
  onChange,
  formatValue = (v) => v.toString(),
}: SliderSettingProps) {
  return (
    <View style={styles.sliderSetting}>
      <View style={styles.sliderHeader}>
        <View style={styles.sliderLabels}>
          <Text style={styles.sliderLabel}>{label}</Text>
          <Text style={styles.sliderDescription}>{description}</Text>
        </View>
        <View style={styles.sliderValueBadge}>
          <Text style={styles.sliderValue}>{formatValue(value)}</Text>
        </View>
      </View>
      
      <Slider
        value={value}
        minimumValue={min}
        maximumValue={max}
        step={step}
        onValueChange={onChange}
        minimumTrackTintColor={COLORS.purple}
        maximumTrackTintColor="#374151"
        thumbTintColor="white"
        style={styles.slider}
      />
    </View>
  );
}

// ============================================================================
// Advanced Settings
// ============================================================================

interface AdvancedSettingsProps {
  config: HRMConfig;
  onChange: (updates: Partial<HRMConfig>) => void;
  disabled: boolean;
}

function AdvancedSettings({ config, onChange, disabled }: AdvancedSettingsProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  
  if (disabled) return null;
  
  return (
    <Card>
      <Pressable onPress={() => setIsExpanded(!isExpanded)}>
        <View style={styles.advancedHeader}>
          <View style={styles.toggleLeft}>
            <IconBox color={COLORS.orange}>
              <Settings2 size={20} color="white" />
            </IconBox>
            <View style={styles.toggleText}>
              <Text style={styles.sectionTitle}>Advanced Settings</Text>
              <Text style={styles.sectionSubtitle}>Fine-tune reasoning parameters</Text>
            </View>
          </View>
          
          {isExpanded ? (
            <ChevronUp size={20} color={iconColor(COLORS.textMuted)} />
          ) : (
            <ChevronDown size={20} color={iconColor(COLORS.textMuted)} />
          )}
        </View>
      </Pressable>
      
      {isExpanded && (
        <View style={styles.advancedContent}>
          <View style={styles.separator} />
          
          {/* Hierarchical Processing */}
          <View style={styles.paramSection}>
            <View style={styles.paramSectionHeader}>
              <Layers size={16} color={iconColor(COLORS.purple)} />
              <Text style={styles.paramSectionTitle}>Hierarchical Processing</Text>
            </View>
            
            <SliderSetting
              label="H-Level Cycles"
              description="High-level planning iterations"
              value={config.hCycles}
              min={1}
              max={4}
              step={1}
              onChange={(v) => onChange({ hCycles: v })}
            />
            
            <SliderSetting
              label="L-Level Cycles"
              description="Low-level execution iterations"
              value={config.lCycles}
              min={1}
              max={4}
              step={1}
              onChange={(v) => onChange({ lCycles: v })}
            />
          </View>
          
          <View style={styles.separator} />
          
          {/* Adaptive Computation */}
          <View style={styles.paramSection}>
            <View style={styles.paramSectionHeader}>
              <Target size={16} color={iconColor(COLORS.cyan)} />
              <Text style={styles.paramSectionTitle}>Adaptive Computation</Text>
            </View>
            
            <SliderSetting
              label="Max Reasoning Depth"
              description="Maximum iterations before halting"
              value={config.maxReasoningDepth}
              min={1}
              max={16}
              step={1}
              onChange={(v) => onChange({ maxReasoningDepth: v })}
            />
            
            <SliderSetting
              label="Halt Threshold"
              description="Confidence level to stop early"
              value={config.haltThreshold}
              min={0.5}
              max={1.0}
              step={0.05}
              onChange={(v) => onChange({ haltThreshold: v })}
              formatValue={(v) => `${Math.round(v * 100)}%`}
            />
          </View>
          
          <View style={styles.separator} />
          
          {/* Candidate Generation */}
          <View style={styles.paramSection}>
            <View style={styles.paramSectionHeader}>
              <Activity size={16} color={iconColor(COLORS.green)} />
              <Text style={styles.paramSectionTitle}>Candidate Generation</Text>
            </View>
            
            <SliderSetting
              label="Candidate Count"
              description="Solutions to generate per cycle"
              value={config.candidateCount}
              min={2}
              max={8}
              step={1}
              onChange={(v) => onChange({ candidateCount: v })}
            />
            
            <SliderSetting
              label="Beam Size"
              description="Top candidates to keep"
              value={config.beamSize}
              min={1}
              max={5}
              step={1}
              onChange={(v) => onChange({ beamSize: v })}
            />
            
            <SliderSetting
              label="Score Threshold"
              description="Minimum viable candidate score"
              value={config.scoreThreshold}
              min={0.0}
              max={1.0}
              step={0.1}
              onChange={(v) => onChange({ scoreThreshold: v })}
              formatValue={(v) => `${Math.round(v * 100)}%`}
            />
          </View>
          
          <View style={styles.separator} />
          
          {/* Debug Options */}
          <View style={styles.paramSection}>
            <View style={styles.paramSectionHeader}>
              <Eye size={16} color={iconColor(COLORS.pink)} />
              <Text style={styles.paramSectionTitle}>Debug Options</Text>
            </View>
            
            <View style={styles.debugOption}>
              <View style={styles.debugOptionText}>
                <Text style={styles.debugOptionLabel}>Show Reasoning Trace</Text>
                <Text style={styles.debugOptionDesc}>Display step-by-step reasoning</Text>
              </View>
              <Switch
                value={config.showReasoningTrace}
                onValueChange={(v) => onChange({ showReasoningTrace: v })}
                trackColor={{ false: '#374151', true: COLORS.purple }}
                thumbColor="white"
              />
            </View>
            
            <View style={styles.debugOption}>
              <View style={styles.debugOptionText}>
                <Text style={styles.debugOptionLabel}>Verbose Logging</Text>
                <Text style={styles.debugOptionDesc}>Log detailed HRM operations</Text>
              </View>
              <Switch
                value={config.verboseLogging}
                onValueChange={(v) => onChange({ verboseLogging: v })}
                trackColor={{ false: '#374151', true: COLORS.purple }}
                thumbColor="white"
              />
            </View>
          </View>
        </View>
      )}
    </Card>
  );
}

// ============================================================================
// Config Summary
// ============================================================================

interface ConfigSummaryProps {
  config: HRMConfig;
}

function ConfigSummary({ config }: ConfigSummaryProps) {
  if (!config.enabled) return null;
  
  return (
    <Card>
      <View style={styles.sectionHeader}>
        <IconBox color={COLORS.green}>
          <Gauge size={20} color="white" />
        </IconBox>
        <Text style={styles.sectionTitle}>Current Configuration</Text>
      </View>
      
      <View style={styles.configBadges}>
        <View style={styles.configBadge}>
          <Text style={styles.configBadgeText}>H-Cycles: {config.hCycles}</Text>
        </View>
        <View style={styles.configBadge}>
          <Text style={styles.configBadgeText}>L-Cycles: {config.lCycles}</Text>
        </View>
        <View style={styles.configBadge}>
          <Text style={styles.configBadgeText}>Depth: {config.maxReasoningDepth}</Text>
        </View>
        <View style={styles.configBadge}>
          <Text style={styles.configBadgeText}>Candidates: {config.candidateCount}</Text>
        </View>
        <View style={styles.configBadge}>
          <Text style={styles.configBadgeText}>Beam: {config.beamSize}</Text>
        </View>
      </View>
    </Card>
  );
}

// ============================================================================
// Main Screen
// ============================================================================

export default function HRMSettingsScreen() {
  const [config] = useAtom(hrmConfigAtom);
  const currentPreset = useAtomValue(hrmCurrentPresetAtom);
  const applyPreset = useSetAtom(applyHrmPresetAtom);
  const resetConfig = useSetAtom(resetHrmConfigAtom);
  const initConfig = useSetAtom(initHrmConfigAtom);
  const updateConfig = useSetAtom(updateHrmConfigAtom);
  
  useEffect(() => {
    initConfig();
  }, [initConfig]);
  
  const handleToggle = useCallback((enabled: boolean) => {
    updateConfig({ enabled });
  }, [updateConfig]);
  
  const handleThinkingLevelChange = useCallback((thinkingLevel: ThinkingLevel) => {
    updateConfig({ thinkingLevel });
  }, [updateConfig]);
  
  const handleConfigChange = useCallback((updates: Partial<HRMConfig>) => {
    updateConfig(updates);
  }, [updateConfig]);
  
  const handlePresetSelect = useCallback((preset: HRMPresetKey) => {
    applyPreset(preset);
  }, [applyPreset]);
  
  const handleReset = useCallback(() => {
    Alert.alert(
      'Reset to Defaults',
      'This will reset all HRM settings to their default values.',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Reset', style: 'destructive', onPress: () => resetConfig() },
      ]
    );
  }, [resetConfig]);
  
  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.content}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerIcon}>
            <Brain size={28} color="white" />
          </View>
          <View style={styles.headerText}>
            <Text style={styles.headerTitle}>Reasoning Engine</Text>
            <Text style={styles.headerSubtitle}>Hierarchical Reasoning Model (HRM)</Text>
          </View>
        </View>
        
        <Text style={styles.headerDescription}>
          Configure how the AI reasons about complex queries using a two-level
          hierarchical approach inspired by brain-like processing.
        </Text>
        
        {/* Sections */}
        <PresetSelector currentPreset={currentPreset} onSelectPreset={handlePresetSelect} />
        
        <ToggleSection
          enabled={config.enabled}
          onToggle={handleToggle}
          thinkingLevel={config.thinkingLevel}
          onThinkingLevelChange={handleThinkingLevelChange}
        />
        
        <AdvancedSettings
          config={config}
          onChange={handleConfigChange}
          disabled={!config.enabled}
        />
        
        <ConfigSummary config={config} />
        
        {/* Reset Button */}
        <Pressable onPress={handleReset} style={styles.resetButton}>
          <RotateCcw size={18} color={iconColor(COLORS.textMuted)} />
          <Text style={styles.resetButtonText}>Reset to Defaults</Text>
        </Pressable>
      </ScrollView>
    </SafeAreaView>
  );
}

// ============================================================================
// Styles
// ============================================================================

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  scrollView: {
    flex: 1,
  },
  content: {
    padding: 16,
    paddingBottom: 32,
  },
  
  // Header
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 8,
  },
  headerIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    backgroundColor: COLORS.purple,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerText: {
    flex: 1,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.text,
  },
  headerSubtitle: {
    fontSize: 14,
    color: COLORS.textMuted,
  },
  headerDescription: {
    fontSize: 14,
    color: COLORS.textMuted,
    marginTop: 8,
    marginBottom: 20,
    lineHeight: 20,
  },
  
  // Card
  card: {
    backgroundColor: COLORS.card,
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  cardActive: {
    borderColor: COLORS.borderActive,
  },
  
  // Icon Box
  iconBox: {
    width: 36,
    height: 36,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  
  // Section Header
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    marginBottom: 12,
  },
  sectionHeaderText: {
    flex: 1,
  },
  sectionTitle: {
    fontSize: 17,
    fontWeight: '600',
    color: COLORS.text,
  },
  sectionSubtitle: {
    fontSize: 13,
    color: COLORS.textMuted,
    marginTop: 2,
  },
  
  // Presets
  presetsRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  presetChip: {
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: '#222222',
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  presetChipActive: {
    backgroundColor: COLORS.purple,
    borderColor: COLORS.purple,
  },
  presetChipCustom: {
    backgroundColor: COLORS.orange,
    borderColor: COLORS.orange,
  },
  presetChipText: {
    fontSize: 14,
    color: COLORS.text,
  },
  presetChipTextActive: {
    fontWeight: '600',
    color: 'white',
  },
  
  // Toggle
  toggleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  toggleLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    flex: 1,
  },
  toggleText: {
    flex: 1,
  },
  
  // Thinking Level
  thinkingLevelContainer: {
    marginTop: 16,
  },
  thinkingLevelLabel: {
    fontSize: 14,
    fontWeight: '500',
    color: COLORS.textMuted,
    marginBottom: 8,
  },
  thinkingLevelRow: {
    flexDirection: 'row',
    gap: 8,
  },
  thinkingLevelOption: {
    padding: 12,
    borderRadius: 8,
    backgroundColor: '#222222',
    borderWidth: 1,
    borderColor: COLORS.border,
    alignItems: 'center',
    gap: 4,
  },
  thinkingLevelOptionActive: {
    borderColor: 'transparent',
  },
  thinkingLevelOptionTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: 'white',
    marginTop: 4,
  },
  thinkingLevelOptionDesc: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.7)',
  },
  
  // Separator
  separator: {
    height: 1,
    backgroundColor: COLORS.border,
    marginVertical: 12,
  },
  
  // Slider Setting
  sliderSetting: {
    marginVertical: 8,
  },
  sliderHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  sliderLabels: {
    flex: 1,
  },
  sliderLabel: {
    fontSize: 15,
    fontWeight: '500',
    color: COLORS.text,
  },
  sliderDescription: {
    fontSize: 13,
    color: COLORS.textMuted,
    marginTop: 2,
  },
  sliderValueBadge: {
    backgroundColor: COLORS.purpleDark,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
    minWidth: 36,
    alignItems: 'center',
  },
  sliderValue: {
    fontSize: 14,
    fontWeight: '600',
    color: '#E9D5FF',
  },
  slider: {
    width: '100%',
    height: 40,
  },
  
  // Advanced
  advancedHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  advancedContent: {
    marginTop: 4,
  },
  paramSection: {
    marginTop: 4,
  },
  paramSectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 12,
  },
  paramSectionTitle: {
    fontSize: 15,
    fontWeight: '600',
    color: COLORS.text,
  },
  
  // Debug Options
  debugOption: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 8,
  },
  debugOptionText: {
    flex: 1,
  },
  debugOptionLabel: {
    fontSize: 15,
    color: COLORS.text,
  },
  debugOptionDesc: {
    fontSize: 13,
    color: COLORS.textMuted,
    marginTop: 2,
  },
  
  // Config Summary
  configBadges: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
  },
  configBadge: {
    backgroundColor: '#222222',
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 6,
  },
  configBadgeText: {
    fontSize: 13,
    color: COLORS.textMuted,
  },
  
  // Reset Button
  resetButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    padding: 14,
    borderRadius: 10,
    backgroundColor: '#222222',
    borderWidth: 1,
    borderColor: COLORS.border,
    marginTop: 8,
    marginBottom: 20,
  },
  resetButtonText: {
    fontSize: 15,
    color: COLORS.textMuted,
  },
});
