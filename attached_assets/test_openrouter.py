"""
Test OpenRouter connection with Grok 4.1 Fast.

Direct test without using the full module structure.
"""
import asyncio
import os
import sys

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# Direct imports to avoid circular dependencies
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI


# Get API keys from environment
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") or os.getenv("EXPO_PUBLIC_GOOGLE_API_KEY") or ""
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY") or os.getenv("EXPO_PUBLIC_OPENROUTER_API_KEY") or ""
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"


async def test_openrouter_grok():
    """Test OpenRouter with Grok 4.1 Fast."""
    print(f"\n{'='*60}")
    print("Testing: xAI Grok 4.1 Fast (Free) via OpenRouter")
    print(f"Model ID: x-ai/grok-4.1-fast:free")
    print(f"{'='*60}")
    
    if not OPENROUTER_API_KEY:
        print("❌ FAILED: No OpenRouter API key")
        return False
    
    try:
        llm = ChatOpenAI(
            model="x-ai/grok-4.1-fast:free",
            temperature=0.7,
            openai_api_key=OPENROUTER_API_KEY,
            openai_api_base=OPENROUTER_BASE_URL,
            default_headers={
                "HTTP-Referer": "https://project-sovereign.app",
                "X-Title": "Project Sovereign",
            }
        )
        
        print("✓ LLM instance created")
        
        response = await llm.ainvoke("What is your name? Answer in one short sentence.")
        
        print(f"✅ SUCCESS!")
        print(f"   Response: {response.content}")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


async def test_google_gemini():
    """Test Google Gemini."""
    print(f"\n{'='*60}")
    print("Testing: Google Gemini 2.5 Flash")
    print(f"Model ID: gemini-2.5-flash")
    print(f"{'='*60}")
    
    if not GOOGLE_API_KEY:
        print("❌ FAILED: No Google API key")
        return False
    
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0.7,
            google_api_key=GOOGLE_API_KEY,
        )
        
        print("✓ LLM instance created")
        
        response = await llm.ainvoke("What is your name? Answer in one short sentence.")
        
        print(f"✅ SUCCESS!")
        print(f"   Response: {response.content}")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False


async def main():
    print("\n" + "="*60)
    print("LLM Provider Test")
    print("="*60)
    
    # Check API keys
    print("\n📋 Configuration Status:")
    print(f"   Google API Key: {'✓ Set' if GOOGLE_API_KEY else '❌ Not set'}")
    print(f"   OpenRouter API Key: {'✓ Set' if OPENROUTER_API_KEY else '❌ Not set'}")
    
    results = []
    
    # Test OpenRouter
    success = await test_openrouter_grok()
    results.append(("OpenRouter Grok 4.1 Fast", success))
    
    # Test Google
    success = await test_google_gemini()
    results.append(("Google Gemini", success))
    
    # Summary
    print("\n" + "="*60)
    print("📊 Test Summary")
    print("="*60)
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"   {name}: {status}")
    
    all_passed = all(s for _, s in results)
    print("\n" + ("🎉 All tests passed!" if all_passed else "⚠️  Some tests failed"))
    print("="*60 + "\n")
    
    return all_passed


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
