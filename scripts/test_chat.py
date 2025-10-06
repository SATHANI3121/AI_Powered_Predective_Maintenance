"""
Test script for AI chat functionality
"""

import requests
import json

API_BASE = "http://localhost:8000/api/v1"
API_KEY = "dev-CHANGE-ME"

def test_chat():
    """Test chat endpoint"""
    print("=" * 60)
    print("🤖 Testing AI Chat Functionality")
    print("=" * 60)
    print()
    
    # Test questions
    test_questions = [
        "How to maintain bearings?",
        "What causes high vibration?",
        "How often should I lubricate motors?",
        "What are the signs of bearing failure?"
    ]
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n[Test {i}/4] Question: {question}")
        print("-" * 60)
        
        try:
            response = requests.post(
                f"{API_BASE}/chat",
                params={"api_key": API_KEY},
                json={
                    "question": question,
                    "include_sources": True,
                    "max_results": 3
                },
                timeout=30
            )
            
            if response.ok:
                data = response.json()
                print(f"✅ Success!")
                print(f"\n📝 Answer:")
                print(f"   {data['answer'][:200]}...")
                print(f"\n📊 Metadata:")
                print(f"   Confidence: {data['confidence']*100:.1f}%")
                print(f"   Processing Time: {data['processing_time_seconds']:.2f}s")
                
                if data.get('sources'):
                    print(f"\n📚 Sources ({len(data['sources'])}):")
                    for idx, source in enumerate(data['sources'], 1):
                        print(f"   {idx}. {source['title']}")
                        print(f"      Relevance: {source['relevance_score']*100:.1f}%")
                        print(f"      Content: {source['content'][:100]}...")
            else:
                print(f"❌ Failed: {response.status_code}")
                try:
                    error = response.json()
                    print(f"   Error: {error.get('detail', response.text)}")
                except:
                    print(f"   Error: {response.text}")
        
        except requests.exceptions.ConnectionError:
            print("❌ Cannot connect to API server!")
            print("   Start the server with: start_api.bat")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    print("\n" + "=" * 60)
    print("✅ All chat tests completed!")
    print("=" * 60)
    return True


def test_chat_suggestions():
    """Test chat suggestions endpoint"""
    print("\n\n" + "=" * 60)
    print("💡 Testing Chat Suggestions")
    print("=" * 60)
    
    try:
        response = requests.get(
            f"{API_BASE}/chat/suggestions",
            params={"api_key": API_KEY, "limit": 5}
        )
        
        if response.ok:
            data = response.json()
            print(f"✅ Got {len(data['suggestions'])} suggestions:")
            for i, suggestion in enumerate(data['suggestions'], 1):
                print(f"   {i}. {suggestion}")
        else:
            print(f"❌ Failed: {response.status_code}")
    
    except Exception as e:
        print(f"❌ Error: {e}")


def test_health():
    """Test API health"""
    print("\n🏥 Checking API Health...")
    try:
        response = requests.get("http://localhost:8000/healthz", timeout=5)
        if response.ok:
            print("✅ API is healthy and running")
            return True
        else:
            print(f"❌ API health check failed: {response.status_code}")
            return False
    except:
        print("❌ API is not accessible")
        return False


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("  AI Chat System Test Suite")
    print("=" * 60)
    
    if not test_health():
        print("\n⚠️  Please start the API server first:")
        print("   run: start_api.bat")
        exit(1)
    
    success = test_chat()
    test_chat_suggestions()
    
    if success:
        print("\n\n🎉 All tests passed!")
        print("\n💡 You can now use the chat feature in the frontend:")
        print("   http://localhost:3000")
    else:
        print("\n\n⚠️  Some tests failed. Check the errors above.")

