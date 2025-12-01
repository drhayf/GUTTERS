/**
 * Chat Interface Component
 * Uses Vercel AI SDK Core with Google Gemini for React Native/Expo
 * Following: https://sdk.vercel.ai/docs/getting-started/expo
 */

import { View, TextInput, TouchableOpacity, FlatList, StyleSheet, KeyboardAvoidingView, Platform } from 'react-native';
import { Text } from 'tamagui';
import { useState } from 'react';
import { useAtom } from 'jotai';
import { messagesAtom, birthDataAtom, Message } from '../lib/state/atoms';
import { HumanDesignAgent } from '../lib/agents/human-design-agent';
import { generateText } from 'ai';
import { chatModel } from '../lib/ai/client';

export function ChatInterface() {
  const [messages, setMessages] = useAtom(messagesAtom);
  const [birthData] = useAtom(birthDataAtom);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async () => {
    if (!input.trim()) return;

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    const query = input;
    setInput('');
    setIsLoading(true);

    try {
      console.log('[ChatInterface] Starting message processing...');
      console.log('[ChatInterface] Using model:', chatModel);
      
      // Check if query is about Human Design
      if (
        query.toLowerCase().includes('design') ||
        query.toLowerCase().includes('chart') ||
        query.toLowerCase().includes('type') ||
        query.toLowerCase().includes('gate')
      ) {
        console.log('[ChatInterface] Detected Human Design query');
        // Run HD agent first to get data
        const hdAgent = new HumanDesignAgent();

        const mockBirthData = birthData || {
          date: '1990-01-15',
          time: '14:30',
          location: { latitude: 40.7128, longitude: -74.006 },
        };

        console.log('[ChatInterface] Executing HD agent with birth data:', mockBirthData);
        const agentResult = await hdAgent.execute({
          framework: 'human-design',
          context: {
            birthData: mockBirthData,
            userQuery: query,
          },
        });
        console.log('[ChatInterface] HD agent completed:', agentResult.method);

        // Use AI SDK to generate interpretation with streaming
        let fullResponse = '';
        const assistantMessageId = (Date.now() + 1).toString();

        // Add empty assistant message that we'll update
        const assistantMessage: Message = {
          id: assistantMessageId,
          role: 'assistant',
          content: '',
          timestamp: new Date(),
          agentData: agentResult,
        };
        setMessages((prev) => [...prev, assistantMessage]);

        console.log('[ChatInterface] Generating response with prompt:', agentResult.interpretationSeed.substring(0, 100) + '...');
        // Generate AI response (non-streaming for React Native compatibility)
        const result = await generateText({
          model: chatModel,
          prompt: agentResult.interpretationSeed,
        });
        console.log('[ChatInterface] generateText completed successfully');
        console.log('[ChatInterface] Response length:', result.text.length);
        console.log('[ChatInterface] Usage:', result.usage);

        fullResponse = result.text;
        
        // Update message with full response
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId ? { ...msg, content: fullResponse } : msg
          )
        );
        console.log('[ChatInterface] Message updated with full response');
      } else {
        console.log('[ChatInterface] Generic query, using direct AI response');
        // Generic AI response for non-HD queries (non-streaming for React Native)
        const assistantMessageId = (Date.now() + 1).toString();

        const assistantMessage: Message = {
          id: assistantMessageId,
          role: 'assistant',
          content: '',
          timestamp: new Date(),
        };
        setMessages((prev) => [...prev, assistantMessage]);

        console.log('[ChatInterface] Generating response for generic query');
        const result = await generateText({
          model: chatModel,
          prompt: `You are a compassionate guide for somatic alignment and self-mastery. User asks: "${query}". Respond with empathy and embodied wisdom.`,
        });
        console.log('[ChatInterface] generateText completed for generic query');
        console.log('[ChatInterface] Response length:', result.text.length);
        console.log('[ChatInterface] Usage:', result.usage);
        
        const fullResponse = result.text;
        
        // Update message with full response
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId ? { ...msg, content: fullResponse } : msg
          )
        );
        console.log('[ChatInterface] Generic response updated');
      }
    } catch (error) {
      console.error('[ChatInterface] ERROR:', error);
      console.error('[ChatInterface] Error details:', {
        name: error instanceof Error ? error.name : 'Unknown',
        message: error instanceof Error ? error.message : 'Unknown error',
        stack: error instanceof Error ? error.stack : 'No stack trace',
      });
      
      // Log API-specific error details if available
      if (error && typeof error === 'object' && 'cause' in error) {
        console.error('[ChatInterface] Error cause:', error.cause);
      }
      if (error && typeof error === 'object' && 'responseBody' in error) {
        console.error('[ChatInterface] Response body:', error.responseBody);
      }
      
      const errorMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}. Please check your API key and model configuration.`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      keyboardVerticalOffset={100}
    >
      <FlatList
        data={messages}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <View
            style={[
              styles.messageBubble,
              item.role === 'user' ? styles.userBubble : styles.assistantBubble,
            ]}
          >
            <Text style={item.role === 'user' ? styles.userText : styles.assistantText}>
              {item.content || '...'}
            </Text>
            {item.agentData && (
              <Text style={styles.metaText}>
                {item.agentData.method} • {item.agentData.confidence ? `${(item.agentData.confidence * 100).toFixed(0)}% confidence` : ''}
              </Text>
            )}
          </View>
        )}
        style={styles.messageList}
        contentContainerStyle={styles.messageListContent}
      />

      {isLoading && (
        <View style={styles.loadingContainer}>
          <Text>Generating response...</Text>
        </View>
      )}

      <View style={styles.inputContainer}>
        <TextInput
          style={styles.input}
          value={input}
          onChangeText={setInput}
          placeholder="Ask about your Human Design..."
          placeholderTextColor="#999"
          onSubmitEditing={sendMessage}
          editable={!isLoading}
          multiline
        />
        <TouchableOpacity
          style={[styles.sendButton, (!input.trim() || isLoading) && styles.sendButtonDisabled]}
          onPress={sendMessage}
          disabled={!input.trim() || isLoading}
        >
          <Text style={styles.sendButtonText}>Send</Text>
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fff',
  },
  messageList: {
    flex: 1,
  },
  messageListContent: {
    padding: 16,
  },
  messageBubble: {
    maxWidth: '80%',
    padding: 12,
    borderRadius: 16,
    marginBottom: 12,
  },
  userBubble: {
    alignSelf: 'flex-end',
    backgroundColor: '#007AFF',
  },
  assistantBubble: {
    alignSelf: 'flex-start',
    backgroundColor: '#E5E5EA',
  },
  userText: {
    color: '#fff',
    fontSize: 16,
    lineHeight: 22,
  },
  assistantText: {
    color: '#000',
    fontSize: 16,
    lineHeight: 22,
  },
  metaText: {
    fontSize: 11,
    color: '#666',
    marginTop: 6,
  },
  loadingContainer: {
    padding: 12,
    alignItems: 'center',
  },
  inputContainer: {
    flexDirection: 'row',
    padding: 16,
    borderTopWidth: 1,
    borderTopColor: '#E5E5EA',
    backgroundColor: '#fff',
  },
  input: {
    flex: 1,
    minHeight: 40,
    maxHeight: 100,
    borderWidth: 1,
    borderColor: '#E5E5EA',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 10,
    marginRight: 8,
    fontSize: 16,
  },
  sendButton: {
    backgroundColor: '#007AFF',
    borderRadius: 20,
    paddingHorizontal: 20,
    justifyContent: 'center',
    alignItems: 'center',
    minHeight: 40,
  },
  sendButtonDisabled: {
    backgroundColor: '#C7C7CC',
  },
  sendButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: '600',
  },
});
