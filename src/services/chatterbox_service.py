"""
Chatterbox TTS Integration Service
Provides emotion-aware text-to-speech using Resemble AI's Chatterbox model
"""
import os
import logging
import io
import tempfile
from typing import Optional, Dict, Any, Tuple
import numpy as np
import torch
import torchaudio

logger = logging.getLogger(__name__)

class ChatterboxService:
    """
    Service for integrating Resemble AI's Chatterbox TTS
    """
    
    def __init__(self):
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_loaded = False
        
        # Voice sample paths for different agents
        self.voice_samples = {
            'general': os.getenv('GENERAL_VOICE_SAMPLE', None),
            'billing': os.getenv('BILLING_VOICE_SAMPLE', None),
            'support': os.getenv('SUPPORT_VOICE_SAMPLE', None),
            'sales': os.getenv('SALES_VOICE_SAMPLE', None),
            'scheduling': os.getenv('SCHEDULING_VOICE_SAMPLE', None)
        }
        
        # Emotion settings for different contexts
        self.emotion_presets = {
            'neutral': {'exaggeration': 0.0, 'cfg_weight': 5.0},
            'empathetic': {'exaggeration': 0.3, 'cfg_weight': 6.0},
            'excited': {'exaggeration': 0.7, 'cfg_weight': 7.0},
            'calm': {'exaggeration': -0.3, 'cfg_weight': 4.0},
            'apologetic': {'exaggeration': -0.5, 'cfg_weight': 5.0}
        }
        
    def load_model(self):
        """
        Load the Chatterbox model
        """
        try:
            if self.model_loaded:
                return True
                
            from chatterbox.tts import ChatterboxTTS
            
            logger.info(f"Loading Chatterbox model on {self.device}")
            self.model = ChatterboxTTS.from_pretrained(device=self.device)
            self.model_loaded = True
            logger.info("Chatterbox model loaded successfully")
            return True
            
        except ImportError:
            logger.error("Chatterbox TTS not installed. Please install from: https://github.com/resemble-ai/chatterbox")
            return False
        except Exception as e:
            logger.error(f"Failed to load Chatterbox model: {e}")
            return False
    
    def detect_emotion_context(self, text: str, conversation_context: Optional[Dict] = None) -> str:
        """
        Detect appropriate emotion based on text and context
        
        Args:
            text: Text to analyze
            conversation_context: Optional conversation history
            
        Returns:
            Emotion key (neutral, empathetic, excited, calm, apologetic)
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
        conversation_context: Optional[Dict] = None
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Convert text to speech using Chatterbox with emotion control
        
        Args:
            text: Text to convert
            agent_type: Type of agent (for voice selection)
            emotion: Explicit emotion override
            conversation_context: Conversation history for emotion detection
            
        Returns:
            Tuple of (audio_bytes, metadata)
        """
        try:
            # Ensure model is loaded
            if not self.model_loaded and not self.load_model():
                logger.error("Failed to load Chatterbox model")
                return b"", {"error": "Model not loaded"}
            
            # Determine emotion
            if emotion is None:
                emotion = self.detect_emotion_context(text, conversation_context)
            
            emotion_settings = self.emotion_presets.get(emotion, self.emotion_presets['neutral'])
            
            # Get voice sample for agent type
            voice_sample_path = self.voice_samples.get(agent_type)
            
            # Generate speech
            logger.info(f"Generating speech for agent '{agent_type}' with emotion '{emotion}'")
            
            if voice_sample_path and os.path.exists(voice_sample_path):
                # Generate with voice cloning
                wav = self.model.generate(
                    text=text,
                    audio_prompt_path=voice_sample_path,
                    **emotion_settings
                )
            else:
                # Generate without voice cloning
                wav = self.model.generate(
                    text=text,
                    **emotion_settings
                )
            
            # Convert to audio bytes
            audio_bytes = self._wav_to_bytes(wav)
            
            metadata = {
                'agent_type': agent_type,
                'emotion': emotion,
                'emotion_settings': emotion_settings,
                'voice_cloned': bool(voice_sample_path),
                'text_length': len(text),
                'device': self.device
            }
            
            logger.info(f"Generated {len(audio_bytes)} bytes of audio")
            return audio_bytes, metadata
            
        except Exception as e:
            logger.error(f"Chatterbox TTS error: {e}")
            return b"", {"error": str(e)}
    
    def _wav_to_bytes(self, wav_tensor: torch.Tensor, sample_rate: int = 24000) -> bytes:
        """
        Convert PyTorch audio tensor to bytes
        
        Args:
            wav_tensor: Audio tensor from Chatterbox
            sample_rate: Sample rate (Chatterbox uses 24kHz)
            
        Returns:
            Audio bytes in WAV format
        """
        try:
            # Create temporary file
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                # Save tensor as WAV
                torchaudio.save(tmp_file.name, wav_tensor.unsqueeze(0), sample_rate)
                
                # Read bytes
                with open(tmp_file.name, 'rb') as f:
                    audio_bytes = f.read()
                
                # Clean up
                os.unlink(tmp_file.name)
                
            return audio_bytes
            
        except Exception as e:
            logger.error(f"Error converting audio to bytes: {e}")
            return b""
    
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
            # Load audio
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_in:
                tmp_in.write(audio_bytes)
                tmp_in.flush()
                
                # Load with torchaudio
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
    
    def create_voice_sample(self, text: str, output_path: str, emotion: str = 'neutral') -> bool:
        """
        Create a voice sample for agent voice cloning
        
        Args:
            text: Sample text to record
            output_path: Path to save voice sample
            emotion: Emotion to use for sample
            
        Returns:
            Success boolean
        """
        try:
            audio_bytes, _ = self.text_to_speech(text, emotion=emotion)
            
            if audio_bytes:
                with open(output_path, 'wb') as f:
                    f.write(audio_bytes)
                logger.info(f"Created voice sample at {output_path}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error creating voice sample: {e}")
            return False

# Global instance
chatterbox_service = ChatterboxService()