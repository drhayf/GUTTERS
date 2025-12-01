/**
 * Model Configuration Settings Screen
 * 
 * Allows users to configure which AI models to use for different purposes:
 * - Primary: Main conversation model
 * - Fast: Real-time pattern detection
 * - Synthesis: Deep insight generation
 * - Fallback: Backup when others fail
 */
import React from 'react';
import { ScrollView, StyleSheet, Pressable, View, Text } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useAtom, useSetAtom } from 'jotai';
import { ChevronLeft, Zap, Brain, Sparkles, Shield, Check } from '@tamagui/lucide-icons';
import { useRouter } from 'expo-router';

import {
  modelConfigAtom,
  primaryModelAtom,
  fastModelAtom,
  synthesisModelAtom,
  fallbackModelAtom,
  applyPresetAtom,
  AVAILABLE_MODELS,
  type ModelId,
  type ModelRole,
} from '../../lib/state/model-config-atoms';

// Role descriptions and icons
const MODEL_ROLES: Record<ModelRole, { 
  label: string; 
  description: string; 
  iconColor: string;
}> = {
  primary: {
    label: 'Primary Model',
    description: 'Main conversation model. Used for generating responses in the Genesis profiler.',
    iconColor: '#a855f7',
  },
  fast: {
    label: 'Fast Model',
    description: 'Real-time operations. Pattern detection, probe generation, quick analysis.',
    iconColor: '#22d3ee',
  },
  synthesis: {
    label: 'Synthesis Model',
    description: 'Deep insight generation. Complex reasoning and profile synthesis.',
    iconColor: '#f59e0b',
  },
  fallback: {
    label: 'Fallback Model',
    description: 'Backup model. Used when primary hits rate limits or fails.',
    iconColor: '#10b981',
  },
};

function RoleIcon({ role }: { role: ModelRole }) {
  const color = MODEL_ROLES[role].iconColor;
  switch (role) {
    case 'primary': return <Brain size={20} color={color as any} />;
    case 'fast': return <Zap size={20} color={color as any} />;
    case 'synthesis': return <Sparkles size={20} color={color as any} />;
    case 'fallback': return <Shield size={20} color={color as any} />;
  }
}

// Model selector component
function ModelSelector({ 
  role, 
  currentModel, 
  onSelect 
}: { 
  role: ModelRole; 
  currentModel: ModelId; 
  onSelect: (model: ModelId) => void;
}) {
  const roleInfo = MODEL_ROLES[role];
  
  return (
    <View style={styles.card}>
      <View style={styles.roleHeader}>
        <RoleIcon role={role} />
        <Text style={[styles.roleLabel, { color: roleInfo.iconColor }]}>
          {roleInfo.label}
        </Text>
      </View>
      
      <Text style={styles.description}>
        {roleInfo.description}
      </Text>
      
      <View style={styles.modelList}>
        {AVAILABLE_MODELS.map((model) => (
          <Pressable
            key={model.id}
            onPress={() => onSelect(model.id)}
          >
            <View
              style={[
                styles.modelRow,
                currentModel === model.id && styles.modelRowSelected
              ]}
            >
              <View style={[
                styles.radio,
                currentModel === model.id && styles.radioSelected
              ]}>
                {currentModel === model.id && <Check size={14} color="#fff" />}
              </View>
              
              <View style={styles.modelInfo}>
                <Text style={styles.modelName}>
                  {model.name}
                </Text>
                <Text style={styles.modelMeta}>
                  {model.tier} • {model.speed} • {model.quality} quality
                </Text>
              </View>
            </View>
          </Pressable>
        ))}
      </View>
    </View>
  );
}

export default function ModelSettingsScreen() {
  const router = useRouter();
  const [config] = useAtom(modelConfigAtom);
  const [primaryModel, setPrimaryModel] = useAtom(primaryModelAtom);
  const [fastModel, setFastModel] = useAtom(fastModelAtom);
  const [synthesisModel, setSynthesisModel] = useAtom(synthesisModelAtom);
  const [fallbackModel, setFallbackModel] = useAtom(fallbackModelAtom);
  const applyPreset = useSetAtom(applyPresetAtom);
  
  return (
    <SafeAreaView style={styles.safeArea} edges={['bottom']}>
      {/* Header */}
      <View style={styles.header}>
        <Pressable
          onPress={() => router.back()}
          style={styles.backButton}
        >
          <ChevronLeft size={24} color="#fff" />
        </Pressable>
        <Text style={styles.headerTitle}>Model Configuration</Text>
      </View>
      
      <ScrollView style={styles.container}>
        <View style={styles.content}>
          {/* Presets */}
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>Quick Presets</Text>
            
            <View style={styles.presetRow}>
              <Pressable
                style={styles.presetButton}
                onPress={() => applyPreset('default')}
              >
                <Text style={styles.presetButtonText}>Balanced</Text>
              </Pressable>
              <Pressable
                style={styles.presetButton}
                onPress={() => applyPreset('performance')}
              >
                <Text style={styles.presetButtonText}>Performance</Text>
              </Pressable>
              <Pressable
                style={styles.presetButton}
                onPress={() => applyPreset('economy')}
              >
                <Text style={styles.presetButtonText}>Economy</Text>
              </Pressable>
            </View>
            
            <Text style={styles.presetDescription}>
              • Balanced: Reliable defaults for everyday use{'\n'}
              • Performance: Best models for highest quality{'\n'}
              • Economy: Fastest/cheapest for high volume
            </Text>
          </View>
          
          <View style={styles.separator} />
          
          {/* Model Selectors */}
          <ModelSelector
            role="primary"
            currentModel={primaryModel}
            onSelect={setPrimaryModel}
          />
          
          <ModelSelector
            role="fast"
            currentModel={fastModel}
            onSelect={setFastModel}
          />
          
          <ModelSelector
            role="synthesis"
            currentModel={synthesisModel}
            onSelect={setSynthesisModel}
          />
          
          <ModelSelector
            role="fallback"
            currentModel={fallbackModel}
            onSelect={setFallbackModel}
          />
          
          <View style={styles.separator} />
          
          {/* Current Config Summary */}
          <View style={styles.summaryCard}>
            <Text style={styles.configSummary}>
              Current Configuration:{'\n'}
              Primary: {primaryModel}{'\n'}
              Fast: {fastModel}{'\n'}
              Synthesis: {synthesisModel}{'\n'}
              Fallback: {fallbackModel}{'\n'}
              Last updated: {new Date(config.updatedAt).toLocaleString()}
            </Text>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: '#050505',
  },
  container: {
    flex: 1,
  },
  content: {
    padding: 16,
    gap: 16,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    gap: 12,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.1)',
  },
  backButton: {
    padding: 8,
  },
  card: {
    backgroundColor: 'rgba(255,255,255,0.05)',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.1)',
    marginBottom: 12,
  },
  roleHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginBottom: 8,
  },
  modelList: {
    marginTop: 12,
    gap: 8,
  },
  modelRow: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 10,
    borderRadius: 8,
    gap: 12,
  },
  modelRowSelected: {
    backgroundColor: 'rgba(168, 85, 247, 0.2)',
  },
  modelInfo: {
    flex: 1,
  },
  presetRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginTop: 12,
  },
  presetButton: {
    backgroundColor: '#a855f7',
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 8,
  },
  presetButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 14,
  },
  summaryCard: {
    backgroundColor: 'rgba(255,255,255,0.03)',
    borderRadius: 8,
    padding: 12,
    marginTop: 8,
  },
  separator: {
    height: 1,
    backgroundColor: 'rgba(255,255,255,0.1)',
    marginVertical: 8,
  },
  radio: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 2,
    borderColor: 'rgba(255,255,255,0.3)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioSelected: {
    backgroundColor: '#a855f7',
    borderColor: '#a855f7',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#fff',
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#fff',
  },
  roleLabel: {
    fontSize: 16,
    fontWeight: '600',
  },
  description: {
    fontSize: 13,
    color: 'rgba(255,255,255,0.6)',
    marginTop: 4,
  },
  modelName: {
    fontSize: 15,
    fontWeight: '500',
    color: '#fff',
  },
  modelMeta: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.5)',
    marginTop: 2,
  },
  presetDescription: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.6)',
    marginTop: 12,
    lineHeight: 18,
  },
  configSummary: {
    fontSize: 12,
    color: 'rgba(255,255,255,0.7)',
    fontFamily: 'monospace',
    lineHeight: 18,
  },
});
