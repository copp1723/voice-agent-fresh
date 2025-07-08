#!/usr/bin/env python3
"""
Test script for Chatterbox TTS integration
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.services.enhanced_voice_processor import enhanced_voice_processor
from src.services.chatterbox_service import chatterbox_service

def test_chatterbox_tts():
    """Test Chatterbox TTS generation"""
    print("Testing Chatterbox TTS integration...")
    
    # Test texts with different emotions
    test_cases = [
        {
            'text': "Hello! Welcome to our automotive service center. How can I help you today?",
            'agent_type': 'general',
            'expected_emotion': 'neutral'
        },
        {
            'text': "I understand your concern about the billing. Let me help you with that right away.",
            'agent_type': 'billing',
            'expected_emotion': 'empathetic'
        },
        {
            'text': "Great news! Your appointment has been confirmed for tomorrow at 10 AM!",
            'agent_type': 'scheduling',
            'expected_emotion': 'excited'
        },
        {
            'text': "I apologize for the confusion. Let me correct that for you immediately.",
            'agent_type': 'support',
            'expected_emotion': 'apologetic'
        }
    ]
    
    for i, test in enumerate(test_cases):
        print(f"\nTest {i+1}: {test['agent_type']} agent")
        print(f"Text: {test['text'][:50]}...")
        
        # Test emotion detection
        detected_emotion = chatterbox_service.detect_emotion_context(test['text'])
        print(f"Detected emotion: {detected_emotion}")
        
        # Generate audio
        audio_bytes, metadata = enhanced_voice_processor.text_to_speech(
            text=test['text'],
            agent_type=test['agent_type']
        )
        
        if audio_bytes:
            print(f"✓ Generated {len(audio_bytes)} bytes of audio")
            print(f"  Engine: {metadata.get('tts_engine', 'unknown')}")
            print(f"  Emotion: {metadata.get('emotion', 'unknown')}")
            
            # Save sample
            output_path = f"test_output_{i+1}_{test['agent_type']}.wav"
            with open(output_path, 'wb') as f:
                f.write(audio_bytes)
            print(f"  Saved to: {output_path}")
        else:
            print(f"✗ Failed to generate audio")
            print(f"  Error: {metadata.get('error', 'Unknown error')}")
    
    print("\nTest complete!")

def test_fallback():
    """Test OpenAI fallback"""
    print("\nTesting OpenAI fallback...")
    
    # Temporarily disable Chatterbox
    enhanced_voice_processor.use_chatterbox = False
    
    audio_bytes, metadata = enhanced_voice_processor.text_to_speech(
        text="This is a test of the OpenAI fallback system.",
        voice="nova"
    )
    
    if audio_bytes:
        print(f"✓ OpenAI fallback working: {len(audio_bytes)} bytes")
        print(f"  Engine: {metadata.get('tts_engine', 'unknown')}")
    else:
        print("✗ OpenAI fallback failed")

if __name__ == "__main__":
    test_chatterbox_tts()
    test_fallback()
