#!/usr/bin/env python3
"""
Gemini Client Feature Test Script
Tests: Basic chat, web search, image recognition
"""
import asyncio
import sys
from pathlib import Path

# Add project root directory to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from llm_score.config import get_settings
from llm_score.logging_config import setup_logging, get_logger
from llm_score.llm.client.factory import LLMClientFactory
from llm_score.llm.schemas.types import LLMRequest, LLMMessage


# ============================================================
# Configuration Section
# ============================================================

# Model to use
MODEL_NAME = "Gemini-2.5-Pro"

# Test image path (optional, skip image recognition test if not provided)
TEST_IMAGE_PATH = "test.png"  # e.g., "test.png"

# ============================================================


async def test_basic_chat():
    """Test basic chat functionality"""
    print("\n" + "=" * 60)
    print("Test 1: Basic Chat")
    print("=" * 60)
    
    try:
        request = LLMRequest(
            model_name=MODEL_NAME,
            messages=[
                LLMMessage(role="user", content="Hello! Please introduce yourself in one sentence.")
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        response = await LLMClientFactory.call_with_attachments(request)
        
        print(f"✓ Response successful!")
        print(f"Model: {response.model}")
        print(f"Content: {response.content[:500]}...")
        if response.usage:
            print(f"Token usage: {response.usage}")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


async def test_grounding_search():
    """Test web search functionality (Google Search Grounding)"""
    print("\n" + "=" * 60)
    print("Test 2: Web Search (Google Search Grounding)")
    print("=" * 60)
    
    try:
        request = LLMRequest(
            model_name=MODEL_NAME,
            messages=[
                LLMMessage(role="user", content="What are the latest tech news today? Please list 3 items.")
            ],
            temperature=0.7,
            max_tokens=1000,
            use_grounding=True  # Enable web search
        )
        
        response = await LLMClientFactory.call_with_attachments(request)
        
        print(f"✓ Response successful!")
        print(f"Model: {response.model}")
        print(f"Content: {response.content[:800]}...")
        
        if response.grounding_metadata:
            print(f"\nWeb search metadata:")
            if 'sources' in response.grounding_metadata:
                print(f"  Source count: {len(response.grounding_metadata['sources'])}")
                for i, source in enumerate(response.grounding_metadata['sources'][:3], 1):
                    print(f"  {i}. {source.get('title', 'N/A')}: {source.get('uri', 'N/A')}")
            if 'web_search_queries' in response.grounding_metadata:
                print(f"  Search queries: {response.grounding_metadata['web_search_queries']}")
        else:
            print("  (No grounding metadata returned)")
        
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


async def test_image_recognition():
    """Test image recognition functionality"""
    print("\n" + "=" * 60)
    print("Test 3: Image Recognition")
    print("=" * 60)
    
    if not TEST_IMAGE_PATH:
        print("⚠ Test image path not configured, skipping this test")
        print("  Tip: Set TEST_IMAGE_PATH variable at the top of the script")
        return None
    
    if not Path(TEST_IMAGE_PATH).exists():
        print(f"⚠ Image file does not exist: {TEST_IMAGE_PATH}, skipping this test")
        return None
    
    try:
        request = LLMRequest(
            model_name=MODEL_NAME,
            messages=[
                LLMMessage(role="user", content="Please describe the content of this image.")
            ],
            attachments=[TEST_IMAGE_PATH],
            temperature=0.7,
            max_tokens=1000
        )
        
        response = await LLMClientFactory.call_with_attachments(request)
        
        print(f"✓ Response successful!")
        print(f"Model: {response.model}")
        print(f"Content: {response.content[:800]}...")
        return True
        
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return False


async def main():
    """Main function"""
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)
    
    print("=" * 60)
    print("Gemini Client Feature Test")
    print("=" * 60)
    print(f"Model: {MODEL_NAME}")
    
    # Check configuration
    settings = get_settings()
    if not settings.gemini_api_key:
        print("\nError: GEMINI_API_KEY not configured, please configure in backend/.env")
        return 1
    
    print(f"API Base URL: {settings.gemini_base_url}")
    print()
    
    results = {}
    
    # Test 1: Basic chat
    results['basic_chat'] = await test_basic_chat()
    
    # Test 2: Web search
    results['grounding'] = await test_grounding_search()
    
    # Test 3: Image recognition
    results['image'] = await test_image_recognition()
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Results Summary")
    print("=" * 60)
    
    for test_name, result in results.items():
        if result is True:
            status = "✓ Passed"
        elif result is False:
            status = "✗ Failed"
        else:
            status = "⚠ Skipped"
        print(f"  {test_name}: {status}")
    
    # Check if all passed
    failed = sum(1 for r in results.values() if r is False)
    if failed > 0:
        print(f"\n{failed} test(s) failed")
        return 1
    
    print("\nAll tests completed!")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
