#!/usr/bin/env python3
"""
Migration script to integrate Chatterbox TTS into the voice agent system
"""
import os
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

def update_imports():
    """Update imports in files that use voice_processor"""
    files_to_update = [
        'src/routes/twilio_routes.py',
        'src/services/agent_brain.py',
        'tests/test_voice_processor.py'
    ]
    
    for file_path in files_to_update:
        full_path = Path(file_path)
        if full_path.exists():
            logger.info(f"Updating imports in {file_path}")
            
            content = full_path.read_text()
            
            # Replace old import with new one
            content = content.replace(
                'from services.voice_processor import voice_processor',
                'from services.enhanced_voice_processor import enhanced_voice_processor as voice_processor'
            )
            content = content.replace(
                'from src.services.voice_processor import voice_processor',
                'from src.services.enhanced_voice_processor import enhanced_voice_processor as voice_processor'
            )
            
            full_path.write_text(content)
            logger.info(f"✓ Updated {file_path}")

def create_voice_samples_directory():
    """Create directory for agent voice samples"""
    voice_dir = Path('voice_samples')
    voice_dir.mkdir(exist_ok=True)
    
    # Create placeholder files
    agents = ['general', 'billing', 'support', 'sales', 'scheduling']
    
    for agent in agents:
        sample_file = voice_dir / f'{agent}_voice_sample.wav'
        if not sample_file.exists():
            sample_file.touch()
            logger.info(f"Created placeholder: {sample_file}")
    
    logger.info("✓ Voice samples directory created")

def update_env_template():
    """Update .env.template with new Chatterbox settings"""
    env_template_path = Path('.env.template')
    
    chatterbox_settings = """
# Chatterbox TTS Settings
USE_CHATTERBOX=true
OPTIMIZE_FOR_TWILIO=true

# Voice Sample Paths (optional - for voice cloning)
GENERAL_VOICE_SAMPLE=voice_samples/general_voice_sample.wav
BILLING_VOICE_SAMPLE=voice_samples/billing_voice_sample.wav
SUPPORT_VOICE_SAMPLE=voice_samples/support_voice_sample.wav
SALES_VOICE_SAMPLE=voice_samples/sales_voice_sample.wav
SCHEDULING_VOICE_SAMPLE=voice_samples/scheduling_voice_sample.wav
"""
    
    if env_template_path.exists():
        content = env_template_path.read_text()
        
        if 'USE_CHATTERBOX' not in content:
            content += chatterbox_settings
            env_template_path.write_text(content)
            logger.info("✓ Updated .env.template with Chatterbox settings")
    else:
        logger.warning("⚠ .env.template not found")

def create_installation_guide():
    """Create Chatterbox installation guide"""
    guide_content = """# Chatterbox TTS Installation Guide

## Prerequisites
- Python 3.11+
- CUDA-capable GPU (recommended) or CPU

## Installation Steps

1. **Install PyTorch** (if not already installed):
   ```bash
   # For CUDA 11.8
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
   
   # For CPU only
   pip install torch torchvision torchaudio
   ```

2. **Install Chatterbox dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Chatterbox** (when available):
   ```bash
   # From GitHub (current method)
   git clone https://github.com/resemble-ai/chatterbox.git
   cd chatterbox
   pip install -e .
   cd ..
   
   # Or via pip (when released)
   # pip install chatterbox-tts
   ```

4. **Configure environment**:
   - Copy `.env.template` to `.env`
   - Set `USE_CHATTERBOX=true` to enable Chatterbox
   - Optionally add voice sample paths for voice cloning

5. **Test the integration**:
   ```bash
   python test_chatterbox_integration.py
   ```

## Voice Samples (Optional)

To use voice cloning:
1. Record 10-30 seconds of clear speech for each agent
2. Save as WAV files in the `voice_samples/` directory
3. Update paths in `.env` file

## Troubleshooting

- If Chatterbox fails to load, the system will fall back to OpenAI TTS
- Check logs for detailed error messages
- Ensure CUDA is properly installed for GPU acceleration
- For production, consider using CPU-optimized settings
"""
    
    guide_path = Path('CHATTERBOX_SETUP.md')
    guide_path.write_text(guide_content)
    logger.info("✓ Created Chatterbox installation guide")

def create_test_script():
    """Create test script for Chatterbox integration"""
    test_content = '''#!/usr/bin/env python3
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
        print(f"\\nTest {i+1}: {test['agent_type']} agent")
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
    
    print("\\nTest complete!")

def test_fallback():
    """Test OpenAI fallback"""
    print("\\nTesting OpenAI fallback...")
    
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
'''
    
    test_path = Path('test_chatterbox_integration.py')
    test_path.write_text(test_content)
    test_path.chmod(0o755)
    logger.info("✓ Created test script")

def main():
    """Run migration steps"""
    logger.info("Starting Chatterbox TTS migration...")
    
    # Change to project directory
    project_dir = Path('/Users/copp1723/Desktop/working_projects/voice-agent-fresh-main')
    os.chdir(project_dir)
    
    # Run migration steps
    update_imports()
    create_voice_samples_directory()
    update_env_template()
    create_installation_guide()
    create_test_script()
    
    logger.info("\n✅ Migration complete!")
    logger.info("\nNext steps:")
    logger.info("1. Review CHATTERBOX_SETUP.md for installation instructions")
    logger.info("2. Install Chatterbox and dependencies")
    logger.info("3. Run test_chatterbox_integration.py to verify")
    logger.info("4. Optionally add voice samples for voice cloning")

if __name__ == "__main__":
    main()