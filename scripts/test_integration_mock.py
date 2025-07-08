#!/usr/bin/env python3
"""Mock test showing Chatterbox integration behavior"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.chatterbox_service import chatterbox_service

def test_emotion_detection():
    """Test emotion detection logic"""
    print("Testing emotion detection...")
    
    test_cases = [
        ("Hello! Welcome to our service center.", "neutral"),
        ("I'm so sorry for the inconvenience.", "apologetic"),
        ("Great news! Your car is ready!", "excited"),
        ("I understand your frustration.", "empathetic"),
        ("Please take your time, no rush.", "calm"),
    ]
    
    for text, expected in test_cases:
        detected = chatterbox_service.detect_emotion_context(text)
        status = "✓" if detected == expected else "✗"
        print(f"{status} '{text[:30]}...' → {detected} (expected: {expected})")

def test_agent_emotion_mapping():
    """Test agent-specific emotion tendencies"""
    print("\nTesting agent emotion mapping...")
    
    agents = ['general', 'billing', 'support', 'sales', 'scheduling']
    call_states = [
        {'customer_frustrated': False},
        {'customer_frustrated': True},
        {'interest_level': 0.8}
    ]
    
    for agent in agents:
        print(f"\n{agent.upper()} agent:")
        for state in call_states:
            emotion = chatterbox_service.get_emotion_from_agent_state(agent, state)
            print(f"  State: {state} → Emotion: {emotion}")

def test_voice_settings():
    """Test voice settings configuration"""
    print("\nTesting voice settings...")
    
    # Import the enhanced processor
    from src.services.enhanced_voice_processor import enhanced_voice_processor
    
    agents = ['general', 'billing', 'support', 'sales', 'scheduling']
    
    for agent in agents:
        settings = enhanced_voice_processor.get_voice_settings(agent)
        print(f"\n{agent.upper()} agent settings:")
        print(f"  OpenAI Voice: {settings['voice']}")
        print(f"  Default Emotion: {settings['default_emotion']}")
        print(f"  Chatterbox Enabled: {settings['use_chatterbox']}")

def test_conversation_sentiment():
    """Test conversation sentiment analysis"""
    print("\nTesting conversation sentiment analysis...")
    
    from src.services.enhanced_voice_processor import enhanced_voice_processor
    
    conversations = [
        {
            'name': 'Positive conversation',
            'messages': [
                {'content': 'Thank you so much for your help!'},
                {'content': 'This is excellent service!'},
                {'content': 'I really appreciate your assistance.'}
            ]
        },
        {
            'name': 'Negative conversation',
            'messages': [
                {'content': 'This is terrible service!'},
                {'content': 'I am very frustrated with this issue.'},
                {'content': 'This problem has been going on for weeks!'}
            ]
        },
        {
            'name': 'Neutral conversation',
            'messages': [
                {'content': 'I need to schedule an appointment.'},
                {'content': 'My car needs an oil change.'},
                {'content': 'What time works best?'}
            ]
        }
    ]
    
    for conv in conversations:
        result = enhanced_voice_processor.analyze_conversation_sentiment(conv['messages'])
        print(f"\n{conv['name']}:")
        print(f"  Sentiment: {result['sentiment']}")
        print(f"  Confidence: {result['confidence']:.1%}")

if __name__ == "__main__":
    print("=== Chatterbox Integration Mock Test ===\n")
    
    test_emotion_detection()
    test_agent_emotion_mapping()
    test_voice_settings()
    test_conversation_sentiment()
    
    print("\n✅ Mock tests complete!")
    print("\nNOTE: This demonstrates the integration logic.")
    print("Actual audio generation requires:")
    print("1. Valid API keys in .env")
    print("2. Chatterbox model download (first run takes time)")
    print("3. GPU for optimal performance (CPU works but slower)")