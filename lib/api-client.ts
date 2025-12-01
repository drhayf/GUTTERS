import { Platform } from 'react-native';
import Constants from 'expo-constants';
import EventSource from 'react-native-sse';
import { API_CONFIG } from './constants';
import type { AgentInput, AgentOutput } from './agents/base-agent';
import { logger, logApiRequest, logApiResponse, logStreamEvent } from './utils/error-logger';
import type { AgentCapability } from './agents/sovereign-protocol';

const getBaseUrl = (): string => {
  // Check for explicit API URL first (for VS Code port forwarding or custom tunnels)
  const explicitApiUrl = process.env.EXPO_PUBLIC_API_URL;
  if (explicitApiUrl) {
    console.log('[APIClient] Using explicit API URL:', explicitApiUrl);
    return explicitApiUrl;
  }
  
  const replitDomain = process.env.EXPO_PUBLIC_REPLIT_DOMAIN || process.env.REPLIT_DOMAINS;
  
  // For native platforms (iOS/Android)
  if (Platform.OS !== 'web') {
    // Check for Replit domain first
    if (replitDomain) {
      return `https://${replitDomain.split(',')[0]}`;
    }
    
    // Use Expo's debuggerHost to get the dev machine's IP
    // This works when connected via Expo Go or dev client
    const debuggerHost = Constants.expoConfig?.hostUri || Constants.manifest2?.extra?.expoGo?.debuggerHost;
    if (debuggerHost) {
      const hostIp = debuggerHost.split(':')[0];
      console.log('[APIClient] Using debugger host IP:', hostIp);
      return `http://${hostIp}:${API_CONFIG.FASTAPI_PORT}`;
    }
    
    // Fallback for Android emulator - 10.0.2.2 maps to host machine's localhost
    if (Platform.OS === 'android') {
      return `http://10.0.2.2:${API_CONFIG.FASTAPI_PORT}`;
    }
    
    // iOS simulator can use localhost
    console.warn('[APIClient] No host IP found, trying localhost (may fail on real devices)');
    return `http://localhost:${API_CONFIG.FASTAPI_PORT}`;
  }
  
  // For web platform
  if (typeof window !== 'undefined' && window.location) {
    const hostname = window.location.hostname;
    
    // Replit deployment
    if (hostname.includes('.replit.dev') || hostname.includes('.repl.co')) {
      return `${window.location.protocol}//${hostname}`;
    }
    
    // Expo tunnel web - extract IP from exp.direct URL or use localhost
    // exp.direct URLs can't reach local FastAPI, so fallback to localhost
    if (hostname.includes('.exp.direct')) {
      console.log('[APIClient] Running on exp.direct, using localhost for API');
      return `http://localhost:${API_CONFIG.FASTAPI_PORT}`;
    }
    
    // Regular localhost or LAN development
    return `${window.location.protocol}//${hostname}:${API_CONFIG.FASTAPI_PORT}`;
  }
  
  if (replitDomain) {
    return `https://${replitDomain.split(',')[0]}`;
  }
  
  return `http://localhost:${API_CONFIG.FASTAPI_PORT}`;
};

const BASE_URL = getBaseUrl();
const API_PREFIX = API_CONFIG.PYTHON_API_PREFIX;

logger.debug(`API Base URL: ${BASE_URL}`, { component: 'APIClient', action: 'init' });

interface HealthResponse {
  status: string;
  version: string;
  models: Record<string, string>;
  hrm_enabled: boolean;
}

interface AgentManifest {
  name: string;
  version: string;
  description: string;
  frameworks: string[];
  capabilities: string[];
  requires_hrm: boolean;
}

interface AgentListResponse {
  agents: AgentManifest[];
  total: number;
}

interface UniversalProtocolMessage {
  source_agent: string;
  target_layer: string;
  insight_type: 'Pattern' | 'Fact' | 'Suggestion';
  confidence_score: number;
  payload: Record<string, unknown>;
  hrm_validated: boolean;
}

// =========================================================================
// SOVEREIGN AGENT TYPES
// =========================================================================

/**
 * Component definition for generative UI
 */
interface ComponentDefinition {
  type: string;
  id?: string;
  props?: Record<string, unknown>;
  [key: string]: unknown;
}

/**
 * Sovereign Agent chat request
 */
interface SovereignChatRequest {
  message: string;
  session_id?: string;
  digital_twin?: Record<string, unknown>;
  enabled_capabilities?: AgentCapability[];
  module_data?: Record<string, Record<string, unknown>>;
  hrm_config?: HRMApiConfig;
  models_config?: ModelConfigRequest;
}

/**
 * Sovereign Agent chat response
 */
interface SovereignChatResponse {
  text: string;
  components: ComponentDefinition[];
  tool_calls: SovereignToolCall[];
  needs_confirmation: boolean;
  confirmation_prompt?: string;
  confirmation_options?: string[];
  suggestions: string[];
  session_id: string;
  turn_number: number;
  model_used?: string;
  processing_time_ms: number;
}

/**
 * Tool call record
 */
interface SovereignToolCall {
  tool_name: string;
  arguments: Record<string, unknown>;
  result?: unknown;
  success?: boolean;
  error?: string;
  timestamp?: string;
}

/**
 * Tool execution result
 */
interface SovereignToolResult {
  tool_name: string;
  result: unknown;
  success: boolean;
  error?: string;
}

/**
 * Sovereign context response
 */
interface SovereignContextResponse {
  session_id: string;
  digital_twin?: Record<string, unknown>;
  memory_summary?: string;
  active_hypotheses?: Array<{
    trait: string;
    confidence: number;
    framework: string;
  }>;
  enabled_capabilities: AgentCapability[];
}

/**
 * Sovereign tools list response
 */
interface SovereignToolsResponse {
  tools: Array<{
    name: string;
    description: string;
    parameters: Record<string, unknown>;
    required_capability?: AgentCapability;
  }>;
  total: number;
}

interface HRMApiConfig {
  enabled?: boolean;
  thinking_level?: 'low' | 'high';
  h_cycles?: number;
  l_cycles?: number;
  max_reasoning_depth?: number;
  halt_threshold?: number;
  candidate_count?: number;
  beam_size?: number;
  score_threshold?: number;
  show_reasoning_trace?: boolean;
  verbose_logging?: boolean;
}

/**
 * Model configuration for different processing roles
 */
interface ModelConfigRequest {
  primary?: string;    // Main conversation model
  fast?: string;       // Real-time pattern detection
  synthesis?: string;  // Deep insight generation
  fallback?: string;   // Backup model
}

interface ChatRequest {
  message: string;
  session_id?: string;
  enable_hrm?: boolean;
  hrm_config?: HRMApiConfig;
  context?: AgentInput['context'];
  model?: string; // Override default model (deprecated, use models_config.primary)
  models_config?: ModelConfigRequest; // Multi-model configuration
  enabled_capabilities?: AgentCapability[]; // Enabled modules/capabilities
}

interface ChatResponse {
  response: string;
  agent_output?: AgentOutput;
  protocol_message?: UniversalProtocolMessage;
  session_id: string;
}

// =========================================================================
// MODULE SYNC TYPES
// =========================================================================

/**
 * State of a single module
 */
interface ModuleState {
  id: string;
  name: string;
  enabled: boolean;
  domain: string | null;
  category: 'wisdom' | 'health' | 'life' | 'system';
  config: Record<string, unknown>;
  last_synced: string | null;
}

/**
 * Module preferences for sync request
 */
interface ModuleSyncRequest {
  enabled_modules: string[];
  disabled_modules: string[];
  preset?: string;
  sync_timestamp: string;
}

/**
 * Response from module sync operation
 */
interface ModuleSyncResponse {
  success: boolean;
  modules_synced: number;
  domains_updated: string[];
  message: string;
}

/**
 * Module to domain mapping
 */
interface DomainMapping {
  module_id: string;
  module_name: string;
  domain_name: string;
  enabled: boolean;
}

class APIClient {
  private baseUrl: string;
  private prefix: string;

  constructor(baseUrl: string = BASE_URL, prefix: string = API_PREFIX) {
    this.baseUrl = baseUrl;
    this.prefix = prefix;
    logger.info(`APIClient initialized with URL: ${baseUrl}${prefix}`, { component: 'APIClient' });
  }

  private async fetch<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${this.prefix}${endpoint}`;
    const method = options.method || 'GET';
    const startTime = Date.now();
    
    logApiRequest(method, url, { component: 'APIClient', action: endpoint });
    
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000);
      
      const response = await fetch(url, {
        ...options,
        signal: controller.signal,
        headers: {
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });
      
      clearTimeout(timeoutId);

      const duration = Date.now() - startTime;
      logApiResponse(method, url, response.status, duration, { component: 'APIClient', action: endpoint });

      if (!response.ok) {
        const error = await response.text();
        logger.networkError(url, response.status, error, { component: 'APIClient', action: endpoint });
        throw new Error(`API Error (${response.status}): ${error}`);
      }

      return response.json();
    } catch (err) {
      const duration = Date.now() - startTime;
      const error = err as Error;
      
      if (error.name === 'AbortError') {
        logger.error(`Request timeout after 30s: ${method} ${url}`, err, { component: 'APIClient', action: endpoint });
        throw new Error(`Request timeout: ${url}`);
      }
      
      logger.error(`Request failed: ${method} ${url} (${duration}ms)`, err, { component: 'APIClient', action: endpoint });
      throw err;
    }
  }

  async healthCheck(): Promise<HealthResponse> {
    return this.fetch<HealthResponse>('/health');
  }

  async listAgents(): Promise<AgentListResponse> {
    return this.fetch<AgentListResponse>('/agents/');
  }

  async getAgent(agentName: string): Promise<AgentManifest> {
    return this.fetch<AgentManifest>(`/agents/${agentName}`);
  }

  async executeAgent(
    agentName: string,
    input: AgentInput
  ): Promise<AgentOutput> {
    return this.fetch<AgentOutput>(`/agents/${agentName}/execute`, {
      method: 'POST',
      body: JSON.stringify(input),
    });
  }

  async getAgentPrompt(agentName: string): Promise<{ agent: string; prompt_template: string | null; has_prompt: boolean }> {
    return this.fetch(`/agents/${agentName}/prompt`);
  }

  async chat(request: ChatRequest): Promise<ChatResponse> {
    return this.fetch<ChatResponse>('/chat/', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * Clear a session's state on the backend
   * Called when user resets their profiling session
   */
  async clearSession(sessionId: string): Promise<{ cleared: boolean; message: string }> {
    try {
      return await this.fetch<{ cleared: boolean; message: string }>(`/chat/sessions/${sessionId}`, {
        method: 'DELETE',
      });
    } catch (err) {
      logger.warn(`Failed to clear session ${sessionId}: ${err}`, { component: 'APIClient', action: 'clearSession' });
      // Don't throw - session clear is best-effort
      return { cleared: false, message: 'Failed to clear backend session' };
    }
  }

  /**
   * SSE streaming chat - uses react-native-sse for native platforms
   * since fetch streaming is not supported on React Native
   */
  async chatStream(
    request: ChatRequest,
    callbacks: {
      onStart?: () => void;
      onToken?: (token: string) => void;
      onAgentOutput?: (output: AgentOutput) => void;
      onComplete?: (response: ChatResponse) => void;
      onError?: (error: Error) => void;
    },
    signal?: AbortSignal
  ): Promise<void> {
    const url = `${this.baseUrl}${this.prefix}/chat/stream`;
    const context = { component: 'APIClient', action: 'chatStream', sessionId: request.session_id };
    const startTime = Date.now();
    
    logger.info(`Starting SSE stream connection to ${url}`, context);
    
    // Use react-native-sse for native platforms (fetch streaming not supported)
    if (Platform.OS !== 'web') {
      return this.chatStreamNative(url, request, callbacks, signal, context, startTime);
    }
    
    // Web platform can use fetch streaming
    return this.chatStreamWeb(url, request, callbacks, signal, context, startTime);
  }
  
  /**
   * Native SSE implementation using react-native-sse
   */
  private async chatStreamNative(
    url: string,
    request: ChatRequest,
    callbacks: {
      onStart?: () => void;
      onToken?: (token: string) => void;
      onAgentOutput?: (output: AgentOutput) => void;
      onComplete?: (response: ChatResponse) => void;
      onError?: (error: Error) => void;
    },
    signal: AbortSignal | undefined,
    context: Record<string, unknown>,
    startTime: number
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      callbacks.onStart?.();
      
      let finalResponse: ChatResponse | null = null;
      let eventCount = 0;
      let tokenCount = 0;
      
      // Create SSE connection with POST method
      const es = new EventSource(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify(request),
        pollingInterval: 0, // Disable polling, use true SSE
      });
      
      // Handle abort signal
      if (signal) {
        signal.addEventListener('abort', () => {
          logger.info('Stream aborted by user', context);
          es.close();
          resolve();
        });
      }
      
      es.addEventListener('open', () => {
        const connectTime = Date.now() - startTime;
        logger.info(`SSE connection opened (${connectTime}ms)`, context);
      });
      
      es.addEventListener('message', (event) => {
        let data = event.data;
        if (!data) return;
        
        // react-native-sse may pass the raw SSE line with "data: " prefix
        // Strip it if present
        if (data.startsWith('data: ')) {
          data = data.slice(6);
        }
        
        try {
          const parsed = JSON.parse(data);
          eventCount++;
          logStreamEvent(parsed.type, parsed.data, context);
          
          switch (parsed.type) {
            case 'session':
              logger.info(`Session started: ${parsed.session_id}, model: ${parsed.model}`, context);
              break;
            case 'token':
              tokenCount++;
              callbacks.onToken?.(parsed.data as string);
              break;
            case 'agent_output':
              logger.info('Received agent output', { ...context, metadata: { phase: parsed.data?.calculation?.phase } });
              callbacks.onAgentOutput?.(parsed.data as AgentOutput);
              break;
            case 'visualization':
              // Visualization is part of agent output, but sent separately
              // The genesis screen handles this via visualizationData in agent_output
              logger.info('Received visualization data', context);
              break;
            case 'complete':
              finalResponse = parsed.data as ChatResponse;
              logger.info('Stream complete event received', context);
              
              const totalDuration = Date.now() - startTime;
              logger.info(`Stream session completed (${totalDuration}ms) - Events: ${eventCount}, Tokens: ${tokenCount}`, context);
              
              es.close();
              
              if (finalResponse) {
                callbacks.onComplete?.(finalResponse);
              } else {
                callbacks.onComplete?.({
                  response: 'Stream completed',
                  session_id: request.session_id,
                } as ChatResponse);
              }
              resolve();
              break;
            case 'error':
              logger.streamError('error', parsed.message || parsed.data, context);
              es.close();
              callbacks.onError?.(new Error(parsed.message || String(parsed.data)));
              reject(new Error(parsed.message || String(parsed.data)));
              break;
          }
        } catch (parseErr) {
          logger.warn(`Failed to parse SSE data: ${data?.slice(0, 100)}...`, context);
        }
      });
      
      es.addEventListener('error', (event: { message?: string; type?: string }) => {
        const totalDuration = Date.now() - startTime;
        const errorMsg = event.message || 'SSE connection error';
        logger.error(`SSE error (${totalDuration}ms): ${errorMsg}`, null, context);
        es.close();
        callbacks.onError?.(new Error(errorMsg));
        reject(new Error(errorMsg));
      });
    });
  }
  
  /**
   * Web SSE implementation using fetch streaming
   */
  private async chatStreamWeb(
    url: string,
    request: ChatRequest,
    callbacks: {
      onStart?: () => void;
      onToken?: (token: string) => void;
      onAgentOutput?: (output: AgentOutput) => void;
      onComplete?: (response: ChatResponse) => void;
      onError?: (error: Error) => void;
    },
    signal: AbortSignal | undefined,
    context: Record<string, unknown>,
    startTime: number
  ): Promise<void> {
    try {
      callbacks.onStart?.();
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify(request),
        signal,
      });

      const connectTime = Date.now() - startTime;
      logger.info(`SSE connection established (${connectTime}ms) - Status: ${response.status}`, context);

      if (!response.ok) {
        const errorText = await response.text();
        logger.networkError(url, response.status, errorText, context);
        throw new Error(`Stream Error (${response.status}): ${errorText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        logger.error('No response body available for streaming', null, context);
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let buffer = '';
      let finalResponse: ChatResponse | null = null;
      let eventCount = 0;
      let tokenCount = 0;

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          logger.info(`Stream completed - Events: ${eventCount}, Tokens: ${tokenCount}`, context);
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.slice(6));
              eventCount++;
              logStreamEvent(event.type, event.data, context);
              
              switch (event.type) {
                case 'token':
                  tokenCount++;
                  callbacks.onToken?.(event.data as string);
                  break;
                case 'agent_output':
                  logger.info('Received agent output', { ...context, metadata: { phase: (event.data as AgentOutput).calculation?.phase } });
                  callbacks.onAgentOutput?.(event.data as AgentOutput);
                  break;
                case 'complete':
                  finalResponse = event.data as ChatResponse;
                  logger.info('Stream complete event received', context);
                  break;
                case 'error':
                  logger.streamError('error', event.data, context);
                  callbacks.onError?.(new Error(event.data as string));
                  return;
              }
            } catch (parseErr) {
              logger.warn(`Failed to parse SSE data: ${line.slice(0, 100)}...`, context);
            }
          }
        }
      }
      
      const totalDuration = Date.now() - startTime;
      logger.info(`Stream session completed (${totalDuration}ms)`, context);
      
      if (finalResponse) {
        callbacks.onComplete?.(finalResponse);
      } else {
        callbacks.onComplete?.({
          response: 'Stream completed',
          session_id: request.session_id,
        } as ChatResponse);
      }
    } catch (err) {
      const totalDuration = Date.now() - startTime;
      if ((err as Error).name === 'AbortError') {
        logger.info(`Stream aborted by user (${totalDuration}ms)`, context);
        return;
      }
      logger.error(`Stream error (${totalDuration}ms)`, err, context);
      callbacks.onError?.(err as Error);
    }
  }
  
  async *chatStreamGenerator(request: ChatRequest): AsyncGenerator<{
    type: string;
    data?: unknown;
  }> {
    const url = `${this.baseUrl}${this.prefix}/chat/stream`;
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Stream Error (${response.status})`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error('No response body');
    }

    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            yield data;
          } catch {
            console.warn('Failed to parse SSE data:', line);
          }
        }
      }
    }
  }

  async getSession(sessionId: string): Promise<{ session_id: string; status: string; message: string }> {
    return this.fetch(`/chat/sessions/${sessionId}`);
  }
  
  getApiUrl(): string {
    return `${this.baseUrl}${this.prefix}`;
  }

  // =========================================================================
  // PROFILE MANAGEMENT
  // =========================================================================

  /**
   * List all saved profiles
   */
  async listProfiles(): Promise<ProfileListResponse> {
    return this.fetch('/profiles/');
  }

  /**
   * Load a specific profile by slot ID
   */
  async loadProfile(slotId: string): Promise<LoadProfileResponse> {
    return this.fetch(`/profiles/${slotId}`);
  }

  /**
   * Save the current session as a profile
   * @param sessionId - The session ID to save
   * @param name - Name for the profile
   * @param slotId - Optional specific slot to save to
   * @param sessionState - Optional session state (fallback if backend session is lost)
   * @param digitalTwin - Optional Digital Twin data (fallback if backend session is lost)
   */
  async saveProfile(
    sessionId: string,
    name: string,
    slotId?: string,
    sessionState?: Record<string, unknown>,
    digitalTwin?: Record<string, unknown>
  ): Promise<SaveProfileResponse> {
    return this.fetch('/profiles/save', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        name,
        slot_id: slotId,
        session_state: sessionState,
        digital_twin: digitalTwin,
      }),
    });
  }

  /**
   * Resume a saved profile - creates a new session from saved state
   */
  async resumeProfile(slotId: string): Promise<ResumeProfileResponse> {
    return this.fetch(`/profiles/${slotId}/resume`, {
      method: 'POST',
    });
  }

  /**
   * Delete a saved profile
   */
  async deleteProfile(slotId: string): Promise<{ success: boolean; slot_id: string; message: string }> {
    return this.fetch(`/profiles/${slotId}`, {
      method: 'DELETE',
    });
  }

  /**
   * Export a profile to a downloadable JSON file
   */
  async exportProfile(slotId: string, exportName?: string): Promise<{ success: boolean; filepath: string; message: string }> {
    const params = exportName ? `?export_name=${encodeURIComponent(exportName)}` : '';
    return this.fetch(`/profiles/${slotId}/export${params}`, {
      method: 'POST',
    });
  }

  /**
   * Get download URL for a profile
   */
  getProfileDownloadUrl(slotId: string): string {
    return `${this.baseUrl}${this.prefix}/profiles/${slotId}/download`;
  }

  /**
   * List saved sessions (in-progress)
   */
  async listSessions(): Promise<SessionListResponse> {
    return this.fetch('/profiles/sessions/');
  }

  /**
   * Delete a saved session
   */
  async deleteSavedSession(sessionId: string): Promise<{ success: boolean; session_id: string; message: string }> {
    return this.fetch(`/profiles/sessions/${sessionId}`, {
      method: 'DELETE',
    });
  }

  // =========================================================================
  // SOVEREIGN AGENT - The Omniscient App Agent
  // =========================================================================

  /**
   * Chat with the Sovereign Agent (synchronous)
   * The Sovereign Agent knows everything about the app and user
   */
  async sovereignChat(request: SovereignChatRequest): Promise<SovereignChatResponse> {
    return this.fetch<SovereignChatResponse>('/sovereign/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  /**
   * SSE streaming chat with Sovereign Agent
   * Includes tool execution and generative UI components
   */
  async sovereignChatStream(
    request: SovereignChatRequest,
    callbacks: {
      onStart?: () => void;
      onToken?: (token: string) => void;
      onToolCall?: (tool: SovereignToolCall) => void;
      onToolResult?: (result: SovereignToolResult) => void;
      onComponent?: (component: ComponentDefinition) => void;
      onComplete?: (response: SovereignChatResponse) => void;
      onError?: (error: Error) => void;
    },
    signal?: AbortSignal
  ): Promise<void> {
    const url = `${this.baseUrl}${this.prefix}/sovereign/chat/stream`;
    const context = { component: 'APIClient', action: 'sovereignChatStream', sessionId: request.session_id };
    const startTime = Date.now();
    
    logger.info(`Starting Sovereign SSE stream to ${url}`, context);
    
    // Use react-native-sse for native platforms
    if (Platform.OS !== 'web') {
      return this.sovereignStreamNative(url, request, callbacks, signal, context, startTime);
    }
    
    // Web platform uses fetch streaming
    return this.sovereignStreamWeb(url, request, callbacks, signal, context, startTime);
  }

  /**
   * Native SSE implementation for Sovereign Agent
   */
  private async sovereignStreamNative(
    url: string,
    request: SovereignChatRequest,
    callbacks: {
      onStart?: () => void;
      onToken?: (token: string) => void;
      onToolCall?: (tool: SovereignToolCall) => void;
      onToolResult?: (result: SovereignToolResult) => void;
      onComponent?: (component: ComponentDefinition) => void;
      onComplete?: (response: SovereignChatResponse) => void;
      onError?: (error: Error) => void;
    },
    signal: AbortSignal | undefined,
    context: Record<string, unknown>,
    startTime: number
  ): Promise<void> {
    return new Promise((resolve, reject) => {
      callbacks.onStart?.();
      
      let finalResponse: SovereignChatResponse | null = null;
      let eventCount = 0;
      let tokenCount = 0;
      
      const es = new EventSource(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify(request),
        pollingInterval: 0,
      });
      
      if (signal) {
        signal.addEventListener('abort', () => {
          logger.info('Sovereign stream aborted by user', context);
          es.close();
          resolve();
        });
      }
      
      es.addEventListener('open', () => {
        const connectTime = Date.now() - startTime;
        logger.info(`Sovereign SSE connection opened (${connectTime}ms)`, context);
      });
      
      es.addEventListener('message', (event) => {
        let data = event.data;
        
        // Debug: Log raw event data
        logger.debug(`Raw SSE event.data: ${JSON.stringify(data)?.slice(0, 200)}`, context);
        
        if (!data) {
          logger.warn('Received empty SSE event data', context);
          return;
        }
        
        // react-native-sse may pass the raw SSE line with "data: " prefix
        if (typeof data === 'string' && data.startsWith('data: ')) {
          data = data.slice(6);
        }
        
        try {
          const parsed = JSON.parse(data);
          eventCount++;
          
          // Debug: Log parsed structure
          logger.debug(`Parsed SSE: type=${parsed.type}, hasData=${!!parsed.data}, keys=${Object.keys(parsed).join(',')}`, context);
          logStreamEvent(parsed.type, parsed.data, context);
          
          switch (parsed.type) {
            case 'session':
              logger.info(`Sovereign session: ${parsed.session_id}`, context);
              break;
              
            case 'token':
            case 'chunk':  // Backend sends 'chunk' for text streaming
              tokenCount++;
              callbacks.onToken?.(parsed.data as string);
              break;
              
            case 'tool_call':
              callbacks.onToolCall?.(parsed.data as SovereignToolCall);
              break;
              
            case 'tool_result':
              callbacks.onToolResult?.(parsed.data as SovereignToolResult);
              break;
              
            case 'component':
              callbacks.onComponent?.(parsed.data as ComponentDefinition);
              break;
              
            case 'response':
              finalResponse = parsed.data as SovereignChatResponse;
              break;
              
            case 'complete':
              logger.info('Sovereign stream complete', context);
              es.close();
              
              if (finalResponse) {
                callbacks.onComplete?.(finalResponse);
              } else if (parsed.data) {
                callbacks.onComplete?.(parsed.data as SovereignChatResponse);
              }
              resolve();
              break;
              
            case 'error':
              logger.streamError('error', parsed.message || parsed.data, context);
              es.close();
              callbacks.onError?.(new Error(parsed.message || String(parsed.data)));
              reject(new Error(parsed.message || String(parsed.data)));
              break;
          }
        } catch (parseErr) {
          logger.warn(`Failed to parse Sovereign SSE data: ${data?.slice(0, 100)}...`, context);
        }
      });
      
      es.addEventListener('error', (event: { message?: string; type?: string }) => {
        const totalDuration = Date.now() - startTime;
        const errorMsg = event.message || 'Sovereign SSE connection error';
        logger.error(`Sovereign SSE error (${totalDuration}ms): ${errorMsg}`, null, context);
        es.close();
        callbacks.onError?.(new Error(errorMsg));
        reject(new Error(errorMsg));
      });
    });
  }

  /**
   * Web SSE implementation for Sovereign Agent
   */
  private async sovereignStreamWeb(
    url: string,
    request: SovereignChatRequest,
    callbacks: {
      onStart?: () => void;
      onToken?: (token: string) => void;
      onToolCall?: (tool: SovereignToolCall) => void;
      onToolResult?: (result: SovereignToolResult) => void;
      onComponent?: (component: ComponentDefinition) => void;
      onComplete?: (response: SovereignChatResponse) => void;
      onError?: (error: Error) => void;
    },
    signal: AbortSignal | undefined,
    context: Record<string, unknown>,
    startTime: number
  ): Promise<void> {
    try {
      callbacks.onStart?.();
      
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'text/event-stream',
        },
        body: JSON.stringify(request),
        signal,
      });

      const connectTime = Date.now() - startTime;
      logger.info(`Sovereign SSE established (${connectTime}ms) - Status: ${response.status}`, context);

      if (!response.ok) {
        const errorText = await response.text();
        logger.networkError(url, response.status, errorText, context);
        throw new Error(`Sovereign Stream Error (${response.status}): ${errorText}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body for Sovereign stream');
      }

      const decoder = new TextDecoder();
      let buffer = '';
      let finalResponse: SovereignChatResponse | null = null;
      let eventCount = 0;
      let tokenCount = 0;

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          logger.info(`Sovereign stream done - Events: ${eventCount}, Tokens: ${tokenCount}`, context);
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const event = JSON.parse(line.slice(6));
              eventCount++;
              
              switch (event.type) {
                case 'token':
                case 'chunk':  // Backend sends 'chunk' for text streaming
                  tokenCount++;
                  callbacks.onToken?.(event.data as string);
                  break;
                case 'tool_call':
                  callbacks.onToolCall?.(event.data as SovereignToolCall);
                  break;
                case 'tool_result':
                  callbacks.onToolResult?.(event.data as SovereignToolResult);
                  break;
                case 'component':
                  callbacks.onComponent?.(event.data as ComponentDefinition);
                  break;
                case 'response':
                  finalResponse = event.data as SovereignChatResponse;
                  break;
                case 'complete':
                  finalResponse = finalResponse || event.data as SovereignChatResponse;
                  break;
                case 'error':
                  callbacks.onError?.(new Error(event.data as string));
                  return;
              }
            } catch (parseErr) {
              logger.warn(`Failed to parse Sovereign SSE: ${line.slice(0, 100)}...`, context);
            }
          }
        }
      }
      
      if (finalResponse) {
        callbacks.onComplete?.(finalResponse);
      }
    } catch (err) {
      const totalDuration = Date.now() - startTime;
      if ((err as Error).name === 'AbortError') {
        logger.info(`Sovereign stream aborted (${totalDuration}ms)`, context);
        return;
      }
      logger.error(`Sovereign stream error (${totalDuration}ms)`, err, context);
      callbacks.onError?.(err as Error);
    }
  }

  /**
   * Get current Sovereign context for a session
   * Includes Digital Twin, memory, and active hypotheses
   */
  async getSovereignContext(sessionId?: string): Promise<SovereignContextResponse> {
    const params = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : '';
    return this.fetch<SovereignContextResponse>(`/sovereign/context${params}`);
  }

  /**
   * Get list of available Sovereign tools
   */
  async getSovereignTools(): Promise<SovereignToolsResponse> {
    return this.fetch<SovereignToolsResponse>('/sovereign/tools');
  }

  // =========================================================================
  // MODULE SYNC METHODS
  // =========================================================================

  /**
   * List all modules with their current state
   */
  async listModules(): Promise<ModuleState[]> {
    return this.fetch<ModuleState[]>('/modules/');
  }

  /**
   * Get state of a specific module
   */
  async getModuleState(moduleId: string): Promise<ModuleState> {
    return this.fetch<ModuleState>(`/modules/${encodeURIComponent(moduleId)}`);
  }

  /**
   * Sync frontend module preferences to backend
   * Call this after any module toggle or preset change
   */
  async syncModules(preferences: ModuleSyncRequest): Promise<ModuleSyncResponse> {
    return this.fetch<ModuleSyncResponse>('/modules/sync', {
      method: 'POST',
      body: JSON.stringify({ preferences }),
    });
  }

  /**
   * Toggle a specific module on or off
   */
  async toggleModule(moduleId: string, enabled: boolean): Promise<ModuleState> {
    return this.fetch<ModuleState>(`/modules/${encodeURIComponent(moduleId)}/toggle?enabled=${enabled}`, {
      method: 'POST',
    });
  }

  /**
   * Get list of module-to-domain mappings
   */
  async getModuleDomainMappings(): Promise<DomainMapping[]> {
    return this.fetch<DomainMapping[]>('/modules/domains');
  }

  /**
   * Get list of currently enabled module IDs
   */
  async getEnabledModules(): Promise<string[]> {
    return this.fetch<string[]>('/modules/enabled');
  }
}

// =========================================================================
// PROFILE TYPES
// =========================================================================

interface ProfileSlot {
  slot_id: string;
  name: string;
  status: 'in_progress' | 'completed' | 'archived';
  created_at: string;
  updated_at: string;
  phase: string;
  completion_percentage: number;
  total_responses: number;
  summary?: string;
}

interface ProfileListResponse {
  profiles: ProfileSlot[];
  total: number;
  max_slots: number;
}

interface LoadProfileResponse {
  success: boolean;
  slot?: ProfileSlot;
  session_state?: Record<string, unknown>;
  digital_twin?: Record<string, unknown>;
  message: string;
}

interface SaveProfileResponse {
  success: boolean;
  slot_id: string;
  message: string;
}

interface ResumeProfileResponse {
  success: boolean;
  session_id: string;
  restored: boolean;
  phase?: string;
  completion_percentage?: number;
  session_state?: Record<string, unknown>;
  digital_twin?: Record<string, unknown>;
  message: string;
}

interface SessionListItem {
  session_id: string;
  saved_at: string;
  phase: string;
  responses: number;
}

interface SessionListResponse {
  sessions: SessionListItem[];
  total: number;
}

export const apiClient = new APIClient();

export type {
  HealthResponse,
  AgentManifest,
  AgentListResponse,
  UniversalProtocolMessage,
  ChatRequest,
  ChatResponse,
  ProfileSlot,
  ProfileListResponse,
  LoadProfileResponse,
  SaveProfileResponse,
  ResumeProfileResponse,
  SessionListItem,
  SessionListResponse,
  // Sovereign Agent types
  ComponentDefinition,
  SovereignChatRequest,
  SovereignChatResponse,
  SovereignToolCall,
  SovereignToolResult,
  SovereignContextResponse,
  SovereignToolsResponse,
  // Module Sync types
  ModuleState,
  ModuleSyncRequest,
  ModuleSyncResponse,
  DomainMapping,
};

export { APIClient };
