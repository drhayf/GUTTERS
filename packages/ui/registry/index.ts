import React from 'react';

export type ComponentType = 
  | 'text'
  | 'input'
  | 'slider'
  | 'binary_choice'
  | 'choice_card'
  | 'choice'          // Backend sends this for choice options
  | 'cards'           // Backend sends this for card selection
  | 'probe'           // Backend sends this for hypothesis probing
  | 'progress'
  | 'visualization'
  | 'image'
  | 'video'
  | 'audio'
  | 'chart'
  | 'mandala'
  | 'breath_timer'
  // Game components
  | 'game'
  | 'reflex_tap'
  | 'reflex_pattern'
  | 'memory_flash'
  | 'choice_speed'
  // Completion/Digital Twin components
  | 'digital_twin_card'     // Displays the completed Digital Twin profile
  | 'activation_steps'       // Shows personalized first steps based on profile
  | 'completion_transition'; // Animated transition when profiling completes

// ============================================================================
// DIGITAL TWIN DATA STRUCTURES
// ============================================================================

/**
 * Energetic signature derived from Human Design calculation
 */
export interface EnergeticSignature {
  hd_type?: string;              // Generator, Projector, Manifestor, Reflector, Manifesting Generator
  hd_strategy?: string;          // To Respond, Wait for Invitation, etc.
  hd_authority?: string;         // Emotional, Sacral, Splenic, etc.
  hd_profile?: string;           // 1/3, 2/4, etc.
  dominant_centers?: string[];   // Defined centers
  open_centers?: string[];       // Undefined/open centers
}

/**
 * Biological markers from birth data
 */
export interface BiologicalMarkers {
  circadian_tendency?: string;   // Morning Lark, Night Owl, etc.
  seasonal_birth?: string;       // Winter, Spring, Summer, Fall
  elemental_balance?: string;    // Fire, Water, Earth, Air dominance
}

/**
 * Psychological profile from Jungian and cognitive analysis
 */
export interface PsychologicalProfile {
  jungian_functions?: string[];  // Dominant cognitive functions
  cognitive_style?: string;      // How they process information
  decision_making?: string;      // Thinking vs Feeling orientation
  energy_direction?: string;     // Introversion vs Extroversion
  shadow_aspects?: string[];     // Areas for growth
}

/**
 * Archetypal patterns detected during profiling
 */
export interface ArchetypeData {
  primary_archetypes?: string[];  // Main archetypal patterns
  shadow_archetypes?: string[];   // Unconscious patterns
  mythic_resonance?: string;      // Mythological themes
}

/**
 * Insights gathered during the profiling session
 */
export interface SessionInsight {
  category: string;              // What domain this insight relates to
  content: string;               // The actual insight
  confidence: number;            // 0.0 - 1.0
  source: string;                // How this was detected
}

/**
 * Complete Digital Twin data structure
 * This is the culmination of the Genesis profiling process
 */
export interface DigitalTwinData {
  energetic_signature?: EnergeticSignature;
  biological_markers?: BiologicalMarkers;
  psychological_profile?: PsychologicalProfile;
  archetypes?: ArchetypeData;
  session_insights?: SessionInsight[];
  completion_percentage?: number;
  created_at?: string;
  summary?: string;              // AI-generated summary message
}

/**
 * A single activation step for the user to take
 */
export interface ActivationStep {
  id: string;                    // Unique identifier
  title: string;                 // Short action title
  description: string;           // Detailed guidance
  icon?: string;                 // Emoji or icon name
  priority: 'high' | 'medium' | 'low';
  category: string;              // Domain: energy, health, purpose, etc.
  estimated_time?: string;       // "5 min", "1 hour", etc.
}

export interface ComponentDefinition {
  type: ComponentType;
  content?: string;
  variant?: string;
  options?: string[];
  min?: number;
  max?: number;
  value?: number;
  label?: string;
  placeholder?: string;
  minLength?: number;
  current?: number;
  total?: number;
  phase?: string;
  src?: string;
  data?: Record<string, unknown>;
  // Game-specific fields
  difficulty?: 'easy' | 'medium' | 'hard';
  timeoutMs?: number;
  config?: Record<string, unknown>;
  // Digital Twin / Completion fields
  digital_twin?: DigitalTwinData;
  steps?: ActivationStep[];
  transition_type?: 'dissolve' | 'expand' | 'reveal';
}

export interface VisualsConfig {
  pulse_color?: 'cyan' | 'purple' | 'gold' | 'red' | 'green';
  background_intensity?: number;
  theme?: string;
  animation?: string;
  color?: string;
}

export interface GenesisPayload {
  type: string;
  phase?: string;
  visuals?: VisualsConfig;
  components?: ComponentDefinition[];
  interpretationSeed?: string;
  calculation?: Record<string, unknown>;
  correlations?: string[];
  method?: string;
  confidence?: number;
}

export type ComponentRenderer = React.ComponentType<{
  definition: ComponentDefinition;
  onInteract?: (value: unknown) => void;
}>;

class ComponentRegistry {
  private registry: Map<ComponentType, ComponentRenderer> = new Map();
  
  register(type: ComponentType, component: ComponentRenderer): void {
    this.registry.set(type, component);
  }
  
  get(type: ComponentType): ComponentRenderer | undefined {
    return this.registry.get(type);
  }
  
  has(type: ComponentType): boolean {
    return this.registry.has(type);
  }
  
  getAll(): Map<ComponentType, ComponentRenderer> {
    return new Map(this.registry);
  }
  
  unregister(type: ComponentType): boolean {
    return this.registry.delete(type);
  }
}

export const componentRegistry = new ComponentRegistry();

export { ComponentRegistry };
