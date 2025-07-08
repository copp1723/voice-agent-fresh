#!/usr/bin/env python3
"""
Test script for Coqui TTS integration
"""
import os
import sys

# Add parent directory to Python path to allow imports from 'src'
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.optional_tts_service import tts_service
import time

def test_coqui_tts():
    """Test Coqui TTS functionality"""
    
    print("🔍 Checking TTS Service Status...")
    status = tts_service.get_service_status()
    
    print("\n📊 Service Status:")
    print(f"  - Coqui Available: {status['coqui']['available']}")
    print(f"  - Coqui Enabled: {status['coqui']['enabled']}")
    print(f"  - OpenAI Available: {status['openai']['available']}")
    print(f"  - Active Service: {status['active_service']}")
    
    print("\n📦 Coqui Dependencies:")
    if 'dependencies' in status['coqui']:
        for dep, available in status['coqui']['dependencies'].items():
            print(f"  - {dep}: {'✅' if available else '❌'}")
    
    if not status['coqui']['available']:
        print("\n❌ Coqui TTS is not available. Please install dependencies:")
        print("   pip install -r requirements-ml.txt")
        return
    
    print("\n🎤 Testing TTS with different agents and emotions...")
    
    test_cases = [
        {
            'text': "Hello! Welcome to A Killion Voice. How can I help you today?",
            'agent_type': 'general',
            'emotion': 'friendly'
        },
        {
            'text': "I understand your concern. Let me look into that for you right away.",
            'agent_type': 'support',
            'emotion': 'empathetic'
        },
        {
            'text': "Great news! Your application has been approved!",
            'agent_type': 'sales',
            'emotion': 'excited'
        },
        {
            'text': "I apologize for the inconvenience. Let me make this right for you.",
            'agent_type': 'billing',
            'emotion': 'apologetic'
        }
    ]
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n🧪 Test {i}:")
        print(f"   Agent: {test['agent_type']}")
        print(f"   Emotion: {test['emotion']}")
        print(f"   Text: {test['text'][:50]}...")
        
        start_time = time.time()
        audio_bytes, metadata = tts_service.text_to_speech(
            text=test['text'],
            agent_type=test['agent_type'],
            emotion=test['emotion']
        )
        generation_time = time.time() - start_time
        
        if audio_bytes:
            print(f"   ✅ Generated {len(audio_bytes)} bytes in {generation_time:.2f}s")
            print(f"   Service: {metadata.get('tts_service', 'unknown')}")
            
            # Save sample for listening
            filename = f"test_output_{test['agent_type']}_{test['emotion']}.wav"
            with open(filename, 'wb') as f:
                f.write(audio_bytes)
            print(f"   💾 Saved to: {filename}")
        else:
            print(f"   ❌ Failed to generate audio")
            if 'error' in metadata:
                print(f"   Error: {metadata['error']}")
    
    # Check cache stats if available
    if status['coqui']['available'] and 'stats' in status['coqui']:
        stats = status['coqui']['stats']
        if 'cache_stats' in stats:
            print(f"\n📈 Cache Statistics:")
            print(f"   - Hits: {stats['cache_stats']['hits']}")
            print(f"   - Misses: {stats['cache_stats']['misses']}")
            print(f"   - Hit Rate: {stats['cache_stats']['hit_rate']:.2%}")

if __name__ == "__main__":
    test_coqui_tts()