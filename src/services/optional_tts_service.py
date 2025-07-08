"""
Optional TTS Service - Graceful handling of Chatterbox TTS and fallback to OpenAI
"""
import os
import logging
from typing import Optional, Dict, Any, Tuple, Union
import tempfile

logger = logging.getLogger(__name__)

class OptionalTTSService:
    """
    TTS service that gracefully handles Chatterbox dependencies and provides fallbacks
    """
    
    def __init__(self):
        self.coqui_available = False
        self.chatterbox_available = False
        self.openai_available = False
        self.fallback_mode = 'openai'  # 'coqui', 'openai' or 'system'
        
        # Configuration
        self.use_coqui = os.getenv('USE_COQUI', 'true').lower() == 'true'
        self.use_chatterbox = os.getenv('USE_CHATTERBOX', 'false').lower() == 'true'
        self.optimize_for_twilio = os.getenv('OPTIMIZE_FOR_TWILIO', 'true').lower() == 'true'
        
        # Initialize available services
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize available TTS services"""
        
        # Try to initialize Coqui if requested
        if self.use_coqui:
            try:
                self._initialize_coqui()
                self.coqui_available = True
                logger.info("✅ Coqui TTS initialized successfully")
            except Exception as e:
                logger.warning(f"⚠️ Coqui TTS not available: {e}")
                logger.info("🔄 Will try other TTS services")
        
        # Try to initialize Chatterbox if requested and Coqui not available
        if self.use_chatterbox and not self.coqui_available:
            try:
                self._initialize_chatterbox()
                self.chatterbox_available = True
                logger.info("✅ Chatterbox TTS initialized successfully")
            except Exception as e:
                logger.warning(f"⚠️ Chatterbox TTS not available: {e}")
        
        # Try to initialize OpenAI TTS
        try:
            self._initialize_openai()
            self.openai_available = True
            logger.info("✅ OpenAI TTS initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ OpenAI TTS not available: {e}")
        
        # Set fallback mode
        if self.coqui_available:
            self.fallback_mode = 'coqui'
        elif self.chatterbox_available:
            self.fallback_mode = 'chatterbox'
        elif self.openai_available:
            self.fallback_mode = 'openai'
        else:
            self.fallback_mode = 'system'
            logger.warning("⚠️ No TTS services available - using system fallback")
    
    def _initialize_coqui(self):
        """Initialize Coqui TTS with proper error handling"""
        try:
            # Try to import Coqui TTS
            from TTS.api import TTS
            import torch
            
            # Test torch installation
            if not torch.cuda.is_available():
                logger.info("CUDA not available, using CPU for Coqui TTS")
            
            # Initialize service
            from src.services.coqui_tts_service import coqui_tts_service
            self.coqui_service = coqui_tts_service
            
            # Wait a bit for background initialization
            import time
            time.sleep(0.5)
            
            return True
            
        except ImportError as e:
            missing_deps = []
            try:
                import torch
            except ImportError:
                missing_deps.append("torch")
            
            try:
                from TTS.api import TTS
            except ImportError:
                missing_deps.append("TTS")
            
            if missing_deps:
                raise Exception(f"Missing Coqui TTS dependencies: {', '.join(missing_deps)}. Install with: pip install -r requirements-ml.txt")
            else:
                raise Exception(f"Coqui TTS initialization failed: {e}")
    
    def _initialize_chatterbox(self):
        """Initialize Chatterbox TTS with proper error handling"""
        try:
            # Check for required packages
            import torch
            import torchaudio
            import numpy as np
            
            # Test torch installation
            if not torch.cuda.is_available():
                logger.info("CUDA not available, using CPU for Chatterbox")
            
            # Try to import chatterbox
            try:
                from chatterbox.tts import ChatterboxTTS
                
                # Initialize service
                from src.services.chatterbox_service import chatterbox_service
                if chatterbox_service.load_model():
                    self.chatterbox_service = chatterbox_service
                    return True
                else:
                    raise Exception("Failed to load Chatterbox model")
                    
            except ImportError:
                raise Exception("Chatterbox TTS not installed. Install with: pip install chatterbox-tts")
                
        except ImportError as e:
            missing_deps = []
            try:
                import torch
            except ImportError:
                missing_deps.append("torch")
            
            try:
                import torchaudio
            except ImportError:
                missing_deps.append("torchaudio")
            
            try:
                import numpy
            except ImportError:
                missing_deps.append("numpy")
            
            if missing_deps:
                raise Exception(f"Missing ML dependencies: {', '.join(missing_deps)}")
            else:
                raise Exception(f"Chatterbox initialization failed: {e}")
    
    def _initialize_openai(self):
        """Initialize OpenAI TTS"""
        try:
            import openai
            
            # Check for API key
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise Exception("OPENAI_API_KEY not configured")
            
            # Initialize client
            self.openai_client = openai.OpenAI(api_key=api_key)
            
            # Test connection
            try:
                response = self.openai_client.audio.speech.create(
                    model="tts-1",
                    voice="alloy",
                    input="test"
                )
                return True
            except Exception as e:
                raise Exception(f"OpenAI TTS test failed: {e}")
                
        except ImportError:
            raise Exception("OpenAI library not installed")
    
    def text_to_speech(
        self, 
        text: str, 
        agent_type: Optional[str] = 'general',
        emotion: Optional[str] = None,
        voice: Optional[str] = None,
        conversation_context: Optional[Dict] = None
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Convert text to speech using the best available service
        
        Args:
            text: Text to convert
            agent_type: Type of agent (for voice selection)
            emotion: Emotion for Chatterbox (ignored for OpenAI)
            voice: Voice override
            conversation_context: Conversation history
            
        Returns:
            Tuple of (audio_bytes, metadata)
        """
        
        # Try Coqui first if available and requested
        if self.coqui_available and self.use_coqui:
            try:
                audio_bytes, metadata = self.coqui_service.text_to_speech(
                    text=text,
                    agent_type=agent_type,
                    emotion=emotion,
                    conversation_context=conversation_context
                )
                
                if audio_bytes:
                    metadata['tts_service'] = 'coqui'
                    if self.optimize_for_twilio:
                        audio_bytes = self.coqui_service.optimize_for_twilio(audio_bytes)
                        metadata['optimized_for_twilio'] = True
                    
                    return audio_bytes, metadata
                    
            except Exception as e:
                logger.error(f"Coqui TTS failed: {e}")
                logger.info("🔄 Falling back to next available TTS")
        
        # Try Chatterbox if available and requested
        if self.chatterbox_available and self.use_chatterbox:
            try:
                audio_bytes, metadata = self.chatterbox_service.text_to_speech(
                    text=text,
                    agent_type=agent_type,
                    emotion=emotion,
                    conversation_context=conversation_context
                )
                
                if audio_bytes:
                    metadata['tts_service'] = 'chatterbox'
                    if self.optimize_for_twilio:
                        audio_bytes = self.chatterbox_service.optimize_for_twilio(audio_bytes)
                        metadata['optimized_for_twilio'] = True
                    
                    return audio_bytes, metadata
                    
            except Exception as e:
                logger.error(f"Chatterbox TTS failed: {e}")
                logger.info("🔄 Falling back to OpenAI TTS")
        
        # Try OpenAI TTS
        if self.openai_available:
            try:
                audio_bytes, metadata = self._openai_tts(text, agent_type, voice)
                if audio_bytes:
                    return audio_bytes, metadata
                    
            except Exception as e:
                logger.error(f"OpenAI TTS failed: {e}")
                logger.info("🔄 Falling back to system TTS")
        
        # System fallback
        return self._system_fallback(text)
    
    def _openai_tts(self, text: str, agent_type: str, voice: Optional[str] = None) -> Tuple[bytes, Dict[str, Any]]:
        """OpenAI TTS implementation"""
        
        # Voice mapping for different agents
        voice_mapping = {
            'general': 'alloy',
            'billing': 'nova',
            'support': 'echo',
            'sales': 'fable',
            'scheduling': 'shimmer'
        }
        
        selected_voice = voice or voice_mapping.get(agent_type, 'alloy')
        
        try:
            response = self.openai_client.audio.speech.create(
                model="tts-1",
                voice=selected_voice,
                input=text
            )
            
            audio_bytes = response.content
            
            # Optimize for Twilio if requested
            if self.optimize_for_twilio:
                audio_bytes = self._optimize_for_twilio_simple(audio_bytes)
            
            metadata = {
                'tts_service': 'openai',
                'voice': selected_voice,
                'agent_type': agent_type,
                'text_length': len(text),
                'optimized_for_twilio': self.optimize_for_twilio
            }
            
            return audio_bytes, metadata
            
        except Exception as e:
            logger.error(f"OpenAI TTS error: {e}")
            return b"", {"error": str(e)}
    
    def _optimize_for_twilio_simple(self, audio_bytes: bytes) -> bytes:
        """Simple optimization for Twilio without heavy dependencies"""
        try:
            # For production, you'd want to use FFmpeg or similar
            # This is a basic implementation
            return audio_bytes
        except Exception as e:
            logger.error(f"Audio optimization failed: {e}")
            return audio_bytes
    
    def _system_fallback(self, text: str) -> Tuple[bytes, Dict[str, Any]]:
        """System fallback - returns empty audio with error message"""
        logger.warning("No TTS services available - using system fallback")
        
        metadata = {
            'tts_service': 'system_fallback',
            'error': 'No TTS services available',
            'text': text[:100] + ('...' if len(text) > 100 else ''),
            'recommendation': 'Configure OPENAI_API_KEY or install Chatterbox dependencies'
        }
        
        return b"", metadata
    
    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all TTS services"""
        status = {
            'coqui': {
                'available': self.coqui_available,
                'enabled': self.use_coqui,
                'dependencies': self._check_coqui_dependencies()
            },
            'chatterbox': {
                'available': self.chatterbox_available,
                'enabled': self.use_chatterbox,
                'dependencies': self._check_chatterbox_dependencies()
            },
            'openai': {
                'available': self.openai_available,
                'configured': bool(os.getenv('OPENAI_API_KEY'))
            },
            'active_service': self.fallback_mode,
            'optimization': {
                'twilio_optimization': self.optimize_for_twilio
            }
        }
        
        # Add Coqui-specific stats if available
        if self.coqui_available:
            try:
                status['coqui']['stats'] = self.coqui_service.get_stats()
            except:
                pass
                
        return status
    
    def _check_coqui_dependencies(self) -> Dict[str, bool]:
        """Check Coqui TTS dependencies"""
        deps = {}
        
        for package in ['torch', 'torchaudio', 'numpy', 'librosa']:
            try:
                __import__(package)
                deps[package] = True
            except ImportError:
                deps[package] = False
        
        try:
            from TTS.api import TTS
            deps['TTS'] = True
        except ImportError:
            deps['TTS'] = False
        
        return deps
    
    def _check_chatterbox_dependencies(self) -> Dict[str, bool]:
        """Check Chatterbox dependencies"""
        deps = {}
        
        for package in ['torch', 'torchaudio', 'numpy']:
            try:
                __import__(package)
                deps[package] = True
            except ImportError:
                deps[package] = False
        
        try:
            from chatterbox.tts import ChatterboxTTS
            deps['chatterbox'] = True
        except ImportError:
            deps['chatterbox'] = False
        
        return deps
    
    def install_chatterbox_dependencies(self) -> bool:
        """Attempt to install Chatterbox dependencies"""
        try:
            import subprocess
            import sys
            
            # Install ML dependencies
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", 
                "torch>=2.0.0", "torchaudio>=2.0.0", "numpy>=1.24.0"
            ])
            
            # Install Chatterbox
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "chatterbox-tts"
            ])
            
            logger.info("✅ Chatterbox dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to install Chatterbox dependencies: {e}")
            return False
    
    def create_installation_guide(self) -> str:
        """Create installation guide for missing dependencies"""
        guide = """
# TTS Service Installation Guide

## Current Status
"""
        status = self.get_service_status()
        
        guide += f"- Chatterbox Available: {status['chatterbox']['available']}\n"
        guide += f"- OpenAI Available: {status['openai']['available']}\n"
        guide += f"- Active Service: {status['active_service']}\n\n"
        
        if not status['chatterbox']['available'] and self.use_chatterbox:
            guide += """## Install Chatterbox TTS (Optional)

### Option 1: Full Installation
```bash
# Install PyTorch and dependencies
pip install torch>=2.0.0 torchaudio>=2.0.0 numpy>=1.24.0

# Install Chatterbox TTS
pip install chatterbox-tts
```

### Option 2: Use Conda (Recommended for ML)
```bash
# Install with conda
conda install pytorch torchaudio -c pytorch
pip install chatterbox-tts
```

### Option 3: Disable Chatterbox
```bash
# In .env file
USE_CHATTERBOX=false
```
"""
        
        if not status['openai']['available']:
            guide += """## Install OpenAI TTS (Recommended)

```bash
# Install OpenAI library
pip install openai

# Set API key in .env
OPENAI_API_KEY=your-api-key-here
```
"""
        
        return guide

# Global instance
tts_service = OptionalTTSService()
