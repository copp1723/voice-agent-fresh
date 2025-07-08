"""
Coqui TTS Integration Service
High-quality, low-latency text-to-speech with voice cloning capabilities
"""
import os
import logging
import io
import time
import tempfile
import threading
from typing import Optional, Dict, Any, Tuple
import numpy as np
from pathlib import Path
import wave
import json
import hashlib
from collections import OrderedDict

# TTS imports
try:
    from TTS.api import TTS
    import torch
    import torchaudio
    import librosa
    COQUI_AVAILABLE = True
except ImportError:
    COQUI_AVAILABLE = False
    logging.warning("Coqui TTS not installed. Install with: pip install TTS")

logger = logging.getLogger(__name__)

class CoquiTTSService:
    """
    Service for integrating Coqui TTS with voice cloning and emotion support
    """
    
    def __init__(self):
        self.model = None
        self.model_name = "tts_models/multilingual/multi-dataset/xtts_v2"
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_loaded = False
        
        # Voice sample paths for different agents
        self.voice_samples = {
            'general': 'voice_samples/general_voice_sample.wav',
            'billing': 'voice_samples/billing_voice_sample.wav',
            'support': 'voice_samples/support_voice_sample.wav',
            'sales': 'voice_samples/sales_voice_sample.wav',
            'scheduling': 'voice_samples/scheduling_voice_sample.wav'
        }
        
        # Voice embeddings cache
        self.voice_embeddings = {}
        self.embeddings_lock = threading.Lock()
        
        # Audio cache for frequently used phrases
        self.audio_cache = OrderedDict()
        self.cache_size = 100
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Emotion settings for speech parameters
        self.emotion_presets = {
            'neutral': {
                'speed': 1.0,
                'temperature': 0.65,
                'top_p': 0.85,
                'top_k': 50
            },
            'empathetic': {
                'speed': 0.95,
                'temperature': 0.7,
                'top_p': 0.9,
                'top_k': 50
            },
            'excited': {
                'speed': 1.1,
                'temperature': 0.75,
                'top_p': 0.85,
                'top_k': 40
            },
            'calm': {
                'speed': 0.9,
                'temperature': 0.6,
                'top_p': 0.8,
                'top_k': 60
            },
            'apologetic': {
                'speed': 0.92,
                'temperature': 0.65,
                'top_p': 0.85,
                'top_k': 55
            }
        }
        
        # Initialize model in background
        self._init_thread = threading.Thread(target=self._background_init)
        self._init_thread.start()
    
    def _background_init(self):
        """Background initialization of TTS model"""
        try:
            if COQUI_AVAILABLE:
                logger.info("Starting background initialization of Coqui TTS model...")
                self.load_model()
                self._preload_voice_embeddings()
        except Exception as e:
            logger.error(f"Background initialization failed: {e}")
    
    def load_model(self):
        """Load the Coqui TTS model"""
        try:
            if self.model_loaded or not COQUI_AVAILABLE:
                return self.model_loaded
                
            logger.info(f"Loading Coqui TTS model: {self.model_name} on {self.device}")
            
            # Initialize TTS with XTTS v2 for voice cloning
            self.model = TTS(self.model_name, progress_bar=False).to(self.device)
            
            self.model_loaded = True
            logger.info("Coqui TTS model loaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load Coqui TTS model: {e}")
            return False
    
    def _preload_voice_embeddings(self):
        """Preload voice embeddings for all agent types"""
        for agent_type, sample_path in self.voice_samples.items():
            if os.path.exists(sample_path):
                try:
                    self._get_voice_embedding(agent_type, sample_path)
                    logger.info(f"Preloaded voice embedding for {agent_type}")
                except Exception as e:
                    logger.error(f"Failed to preload embedding for {agent_type}: {e}")
    
    def _get_voice_embedding(self, agent_type: str, voice_sample_path: str) -> Any:
        """Get or compute voice embedding for an agent type"""
        with self.embeddings_lock:
            if agent_type in self.voice_embeddings:
                return self.voice_embeddings[agent_type]
            
            try:
                # Compute speaker embedding using the model
                if hasattr(self.model, 'synthesizer') and hasattr(self.model.synthesizer, 'tts_model'):
                    # For XTTS models
                    embedding = self.model.synthesizer.tts_model.get_conditioning_latents(
                        audio_path=voice_sample_path
                    )
                else:
                    # Fallback for other models
                    embedding = None
                
                self.voice_embeddings[agent_type] = embedding
                return embedding
                
            except Exception as e:
                logger.error(f"Failed to compute voice embedding: {e}")
                return None
    
    def detect_emotion_context(self, text: str, conversation_context: Optional[Dict] = None) -> str:
        """
        Detect appropriate emotion based on text and context
        
        Args:
            text: Text to analyze
            conversation_context: Optional conversation history
            
        Returns:
            Emotion key
        """
        text_lower = text.lower()
        
        # Apologetic contexts
        if any(phrase in text_lower for phrase in ['sorry', 'apologize', 'mistake', 'error', 'unfortunately']):
            return 'apologetic'
        
        # Excited contexts
        if any(phrase in text_lower for phrase in ['great news', 'congratulations', 'approved', 'excellent', 'wonderful']):
            return 'excited'
        
        # Empathetic contexts
        if any(phrase in text_lower for phrase in ['understand', 'help you', 'assist', 'concern', 'worry']):
            return 'empathetic'
        
        # Calm contexts
        if any(phrase in text_lower for phrase in ['relax', 'take your time', 'no rush', 'whenever you\'re ready']):
            return 'calm'
        
        # Check conversation context if provided
        if conversation_context:
            sentiment = conversation_context.get('sentiment', 'neutral')
            if sentiment == 'negative':
                return 'empathetic'
            elif sentiment == 'positive':
                return 'excited'
        
        return 'neutral'
    
    def text_to_speech(
        self, 
        text: str, 
        agent_type: Optional[str] = 'general',
        emotion: Optional[str] = None,
        conversation_context: Optional[Dict] = None,
        use_cache: bool = True
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Convert text to speech using Coqui TTS with voice cloning
        
        Args:
            text: Text to convert
            agent_type: Type of agent (for voice selection)
            emotion: Explicit emotion override
            conversation_context: Conversation history for emotion detection
            use_cache: Whether to use audio cache
            
        Returns:
            Tuple of (audio_bytes, metadata)
        """
        try:
            # Ensure model is loaded
            if not self.model_loaded and not self.load_model():
                logger.error("Failed to load Coqui TTS model")
                return self._fallback_tts(text)
            
            # Determine emotion
            if emotion is None:
                emotion = self.detect_emotion_context(text, conversation_context)
            
            # Check cache
            cache_key = self._get_cache_key(text, agent_type, emotion)
            if use_cache and cache_key in self.audio_cache:
                self.cache_hits += 1
                logger.info(f"Cache hit for: {text[:30]}... (hits: {self.cache_hits})")
                return self.audio_cache[cache_key]
            
            self.cache_misses += 1
            
            # Get emotion settings
            emotion_settings = self.emotion_presets.get(emotion, self.emotion_presets['neutral'])
            
            # Get voice sample path
            voice_sample_path = self.voice_samples.get(agent_type)
            
            # Generate speech
            start_time = time.time()
            logger.info(f"Generating speech for agent '{agent_type}' with emotion '{emotion}'")
            
            if voice_sample_path and os.path.exists(voice_sample_path):
                # Generate with voice cloning
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                    self.model.tts_to_file(
                        text=text,
                        speaker_wav=voice_sample_path,
                        language="en",
                        file_path=tmp_file.name,
                        speed=emotion_settings['speed']
                    )
                    
                    # Read the generated audio
                    with open(tmp_file.name, 'rb') as f:
                        audio_bytes = f.read()
                    
                    # Clean up
                    os.unlink(tmp_file.name)
            else:
                # Generate without voice cloning
                with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                    self.model.tts_to_file(
                        text=text,
                        language="en",
                        file_path=tmp_file.name,
                        speed=emotion_settings['speed']
                    )
                    
                    # Read the generated audio
                    with open(tmp_file.name, 'rb') as f:
                        audio_bytes = f.read()
                    
                    # Clean up
                    os.unlink(tmp_file.name)
            
            generation_time = time.time() - start_time
            
            metadata = {
                'agent_type': agent_type,
                'emotion': emotion,
                'emotion_settings': emotion_settings,
                'voice_cloned': bool(voice_sample_path),
                'text_length': len(text),
                'generation_time': generation_time,
                'device': self.device,
                'cache_stats': {
                    'hits': self.cache_hits,
                    'misses': self.cache_misses,
                    'hit_rate': self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
                }
            }
            
            # Cache the result
            if use_cache:
                self._add_to_cache(cache_key, (audio_bytes, metadata))
            
            logger.info(f"Generated {len(audio_bytes)} bytes of audio in {generation_time:.2f}s")
            return audio_bytes, metadata
            
        except Exception as e:
            logger.error(f"Coqui TTS error: {e}")
            return self._fallback_tts(text)
    
    def _get_cache_key(self, text: str, agent_type: str, emotion: str) -> str:
        """Generate cache key for audio"""
        content = f"{text}:{agent_type}:{emotion}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _add_to_cache(self, key: str, value: Tuple[bytes, Dict]):
        """Add audio to cache with size limit"""
        if len(self.audio_cache) >= self.cache_size:
            # Remove oldest item
            self.audio_cache.popitem(last=False)
        
        self.audio_cache[key] = value
    
    def _fallback_tts(self, text: str) -> Tuple[bytes, Dict[str, Any]]:
        """Fallback TTS when Coqui is not available"""
        logger.warning("Using fallback TTS - no audio generated")
        return b"", {"error": "TTS not available", "fallback": True}
    
    def optimize_for_twilio(self, audio_bytes: bytes) -> bytes:
        """
        Optimize audio for Twilio playback
        Twilio prefers 8kHz mono μ-law encoded audio
        
        Args:
            audio_bytes: Original audio bytes
            
        Returns:
            Optimized audio bytes
        """
        try:
            # Create temporary files for processing
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_in:
                tmp_in.write(audio_bytes)
                tmp_in.flush()
                
                # Load audio
                waveform, sample_rate = torchaudio.load(tmp_in.name)
                os.unlink(tmp_in.name)
            
            # Convert to mono if stereo
            if waveform.shape[0] > 1:
                waveform = torch.mean(waveform, dim=0, keepdim=True)
            
            # Resample to 8kHz
            if sample_rate != 8000:
                resampler = torchaudio.transforms.Resample(sample_rate, 8000)
                waveform = resampler(waveform)
            
            # Save as μ-law encoded
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_out:
                torchaudio.save(
                    tmp_out.name, 
                    waveform, 
                    8000,
                    encoding='ULAW',
                    bits_per_sample=8
                )
                
                with open(tmp_out.name, 'rb') as f:
                    optimized_bytes = f.read()
                
                os.unlink(tmp_out.name)
            
            logger.info(f"Optimized audio for Twilio: {len(audio_bytes)} -> {len(optimized_bytes)} bytes")
            return optimized_bytes
            
        except Exception as e:
            logger.error(f"Error optimizing audio for Twilio: {e}")
            return audio_bytes  # Return original if optimization fails
    
    def get_emotion_from_agent_state(self, agent_type: str, call_state: Dict) -> str:
        """
        Determine emotion based on agent type and call state
        
        Args:
            agent_type: Type of agent
            call_state: Current call state/metrics
            
        Returns:
            Emotion key
        """
        # Billing agents should be more empathetic
        if agent_type == 'billing' and call_state.get('customer_frustrated', False):
            return 'empathetic'
        
        # Sales agents should be more excited
        if agent_type == 'sales' and call_state.get('interest_level', 0) > 0.7:
            return 'excited'
        
        # Support agents should be calm and reassuring
        if agent_type == 'support':
            return 'calm'
        
        # Scheduling agents should be neutral and professional
        if agent_type == 'scheduling':
            return 'neutral'
        
        return 'neutral'
    
    def create_voice_profile(self, audio_path: str, profile_name: str) -> bool:
        """
        Create a voice profile from an audio sample
        
        Args:
            audio_path: Path to audio sample
            profile_name: Name for the voice profile
            
        Returns:
            Success boolean
        """
        try:
            if not self.model_loaded:
                logger.error("Model not loaded")
                return False
            
            # Validate audio file
            if not os.path.exists(audio_path):
                logger.error(f"Audio file not found: {audio_path}")
                return False
            
            # Store voice sample path
            self.voice_samples[profile_name] = audio_path
            
            # Precompute embedding
            self._get_voice_embedding(profile_name, audio_path)
            
            logger.info(f"Created voice profile '{profile_name}' from {audio_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating voice profile: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get TTS service statistics"""
        return {
            'model_loaded': self.model_loaded,
            'device': self.device,
            'model_name': self.model_name,
            'voice_profiles': list(self.voice_samples.keys()),
            'cache_stats': {
                'size': len(self.audio_cache),
                'hits': self.cache_hits,
                'misses': self.cache_misses,
                'hit_rate': self.cache_hits / (self.cache_hits + self.cache_misses) if (self.cache_hits + self.cache_misses) > 0 else 0
            },
            'emotion_presets': list(self.emotion_presets.keys())
        }

# Global instance
coqui_tts_service = CoquiTTSService()