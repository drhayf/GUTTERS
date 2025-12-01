/**
 * Comprehensive AI Integration Test
 * Tests both Vercel AI SDK and LangChain integrations with Gemini 2.5
 */

import 'dotenv/config';
import { generateText } from 'ai';
import { chatModel, synthesisModel, quickModel, stableModel } from './lib/ai/client';
import { langchainChatModel, langchainSynthesisModel } from './lib/ai/client';

console.log('=================================');
console.log('AI INTEGRATION TEST');
console.log('=================================\n');

const API_KEY = process.env.EXPO_PUBLIC_GOOGLE_API_KEY || process.env.GOOGLE_API_KEY;
if (!API_KEY) {
  console.error('❌ GOOGLE_API_KEY or EXPO_PUBLIC_GOOGLE_API_KEY not set in .env file!');
  process.exit(1);
}

console.log('✓ API Key found (length:', API_KEY.length, ')\n');

// Test 1: Vercel AI SDK - Basic Generation
async function testVercelBasic() {
  console.log('═══════════════════════════════════');
  console.log('TEST 1: Vercel AI SDK - Basic Text');
  console.log('═══════════════════════════════════');
  console.log('Model: gemini-2.5-flash (chatModel)');
  
  try {
    const result = await generateText({
      model: chatModel,
      prompt: 'Say "Test successful" and nothing else.',
    });
    
    console.log('✅ SUCCESS');
    console.log('Response:', result.text);
    console.log('Tokens:', result.usage);
    console.log('Finish reason:', result.finishReason);
    return true;
  } catch (error: any) {
    console.error('❌ FAILED');
    console.error('Error:', error.message);
    console.error('Cause:', error.cause);
    return false;
  }
}

// Test 2: Vercel AI SDK - Synthesis Model
async function testVercelSynthesis() {
  console.log('\n═══════════════════════════════════');
  console.log('TEST 2: Vercel AI SDK - Synthesis');
  console.log('═══════════════════════════════════');
  console.log('Model: gemini-2.5-pro (synthesisModel)');
  
  try {
    const result = await generateText({
      model: synthesisModel,
      prompt: 'Summarize the concept of "somatic alignment" in one sentence.',
    });
    
    console.log('✅ SUCCESS');
    console.log('Response:', result.text);
    console.log('Tokens:', result.usage);
    return true;
  } catch (error: any) {
    console.error('❌ FAILED');
    console.error('Error:', error.message);
    return false;
  }
}

// Test 3: Vercel AI SDK - Quick Model
async function testVercelQuick() {
  console.log('\n═══════════════════════════════════');
  console.log('TEST 3: Vercel AI SDK - Quick Model');
  console.log('═══════════════════════════════════');
  console.log('Model: gemini-2.5-flash-lite (quickModel)');
  
  try {
    const result = await generateText({
      model: quickModel,
      prompt: 'Count: 1, 2, 3',
    });
    
    console.log('✅ SUCCESS');
    console.log('Response:', result.text);
    console.log('Tokens:', result.usage);
    return true;
  } catch (error: any) {
    console.error('❌ FAILED');
    console.error('Error:', error.message);
    return false;
  }
}

// Test 4: LangChain - Basic Call
async function testLangChainBasic() {
  console.log('\n═══════════════════════════════════');
  console.log('TEST 4: LangChain - Basic Call');
  console.log('═══════════════════════════════════');
  console.log('Model: ChatGoogleGenerativeAI (gemini-2.5-flash)');
  
  try {
    // @ts-ignore - LangChain types may not be fully resolved
    const result = await langchainChatModel.invoke([
      { role: 'user', content: 'Say "LangChain working" and nothing else.' },
    ]);
    
    console.log('✅ SUCCESS');
    console.log('Response:', result.content);
    console.log('Response type:', typeof result.content);
    return true;
  } catch (error: any) {
    console.error('❌ FAILED');
    console.error('Error:', error.message);
    console.error('Stack:', error.stack?.substring(0, 200));
    return false;
  }
}

// Test 5: LangChain - System Message
async function testLangChainSystem() {
  console.log('\n═══════════════════════════════════');
  console.log('TEST 5: LangChain - System Message');
  console.log('═══════════════════════════════════');
  
  try {
    // @ts-ignore
    const result = await langchainChatModel.invoke([
      { role: 'system', content: 'You are a helpful assistant who speaks like a pirate.' },
      { role: 'user', content: 'Tell me about the weather.' },
    ]);
    
    console.log('✅ SUCCESS');
    console.log('Response:', result.content);
    console.log('Has pirate-like language:', /arr|ahoy|matey|ye/i.test(result.content.toString()));
    return true;
  } catch (error: any) {
    console.error('❌ FAILED');
    console.error('Error:', error.message);
    return false;
  }
}

// Test 6: LangChain - Synthesis Model
async function testLangChainSynthesis() {
  console.log('\n═══════════════════════════════════');
  console.log('TEST 6: LangChain - Synthesis Model');
  console.log('═══════════════════════════════════');
  console.log('Model: ChatGoogleGenerativeAI (gemini-2.5-pro)');
  
  try {
    // @ts-ignore
    const result = await langchainSynthesisModel.invoke([
      { role: 'user', content: 'Explain quantum entanglement in simple terms.' },
    ]);
    
    console.log('✅ SUCCESS');
    console.log('Response length:', result.content.toString().length, 'characters');
    console.log('First 100 chars:', result.content.toString().substring(0, 100) + '...');
    return true;
  } catch (error: any) {
    console.error('❌ FAILED');
    console.error('Error:', error.message);
    return false;
  }
}

// Test 7: LangChain - Multi-turn Conversation
async function testLangChainConversation() {
  console.log('\n═══════════════════════════════════');
  console.log('TEST 7: LangChain - Conversation');
  console.log('═══════════════════════════════════');
  
  try {
    const messages: any[] = [
      { role: 'system', content: 'You are a helpful math tutor.' },
      { role: 'user', content: 'What is 5 + 3?' },
    ];
    
    // @ts-ignore
    const result1 = await langchainChatModel.invoke(messages);
    console.log('Turn 1:', result1.content);
    
    // Add AI response and follow-up
    messages.push({ role: 'assistant', content: result1.content.toString() });
    messages.push({ role: 'user', content: 'Now multiply that by 2.' });
    
    // @ts-ignore
    const result2 = await langchainChatModel.invoke(messages);
    console.log('Turn 2:', result2.content);
    
    console.log('✅ SUCCESS');
    console.log('Maintains context:', /16|sixteen/i.test(result2.content.toString()));
    return true;
  } catch (error: any) {
    console.error('❌ FAILED');
    console.error('Error:', error.message);
    return false;
  }
}

// Test 8: Cross-compatibility test
async function testCrossCompatibility() {
  console.log('\n═══════════════════════════════════');
  console.log('TEST 8: Cross-Compatibility');
  console.log('═══════════════════════════════════');
  console.log('Testing same prompt on both SDKs');
  
  const testPrompt = 'What is 2+2? Answer with just the number.';
  
  try {
    // Vercel AI SDK
    const vercelResult = await generateText({
      model: chatModel,
      prompt: testPrompt,
    });
    
    // LangChain
    // @ts-ignore
    const langchainResult = await langchainChatModel.invoke([
      { role: 'user', content: testPrompt },
    ]);
    
    console.log('✅ SUCCESS');
    console.log('Vercel response:', vercelResult.text);
    console.log('LangChain response:', langchainResult.content);
    console.log('Both contain "4":', 
      vercelResult.text.includes('4') && 
      langchainResult.content.toString().includes('4'));
    return true;
  } catch (error: any) {
    console.error('❌ FAILED');
    console.error('Error:', error.message);
    return false;
  }
}

// Run all tests
async function runAllTests() {
  const results = {
    vercelBasic: await testVercelBasic(),
    vercelSynthesis: await testVercelSynthesis(),
    vercelQuick: await testVercelQuick(),
    langchainBasic: await testLangChainBasic(),
    langchainSystem: await testLangChainSystem(),
    langchainSynthesis: await testLangChainSynthesis(),
    langchainConversation: await testLangChainConversation(),
    crossCompatibility: await testCrossCompatibility(),
  };
  
  console.log('\n═════════════════════════════════════');
  console.log('FINAL RESULTS');
  console.log('═════════════════════════════════════');
  
  const passed = Object.values(results).filter(r => r).length;
  const total = Object.values(results).length;
  
  Object.entries(results).forEach(([test, passed]) => {
    console.log(`${passed ? '✅' : '❌'} ${test}`);
  });
  
  console.log('\n─────────────────────────────────────');
  console.log(`PASSED: ${passed}/${total}`);
  console.log('─────────────────────────────────────');
  
  if (passed === total) {
    console.log('\n🎉 ALL TESTS PASSED!');
    console.log('\nYour AI integration is fully working:');
    console.log('  ✓ Vercel AI SDK with Gemini 2.5');
    console.log('  ✓ LangChain with Google GenAI');
    console.log('  ✓ All model variants (flash, pro, lite)');
    console.log('  ✓ System messages & conversations');
    console.log('  ✓ Cross-SDK compatibility');
  } else {
    console.log('\n⚠️  SOME TESTS FAILED');
    console.log('Check the error messages above for details.');
  }
}

// Execute
runAllTests().catch(error => {
  console.error('\n💥 CRITICAL ERROR:', error);
  process.exit(1);
});
