"""
Unified Voice Processing Service - Combines enhanced features with legacy compatibility
"""
import os
import logging
import io
import base64
from typing import Optional, Dict, Any, Tuple
import openai
from .chatterbox_service import chatterbox_service

logger = logging.getLogger(__name__)

class UnifiedVoiceProcessor:
    """
    Unified voice processing with enhanced features and legacy compatibility
    """
    
    def __init__(
        self,
        tts_client: Optional[Any] = None,
        stt_client: Optional[Any] = None,
        chatterbox_service: Optional[Any] = None,
        use_chatterbox: bool = True,
        default_voice: str = 'alloy',
        speech_model: str = 'whisper-1',
        tts_model: str = 'tts-1',
        optimize_for_twilio: bool = True,
    ):
        """
        Dependency injection constructor with fallback to legacy initialization
        """
        # Use injected dependencies or initialize from environment (legacy compatibility)
        self.tts_client = tts_client or self._init_legacy_tts_client()
        self.openai_client = stt_client or self._init_legacy_stt_client()
        self.chatterbox_service = chatterbox_service or self._init_legacy_chatterbox()
        
        self.use_chatterbox = use_chatterbox
        self.default_voice = default_voice
        self.speech_model = speech_model
        self.tts_model = tts_model
        self.optimize_for_twilio = optimize_for_twilio
        
        # Initialize Chatterbox if enabled and available
        if self.use_chatterbox and self.chatterbox_service:
            try:
                self.chatterbox_service.load_model()
                logger.info("Chatterbox TTS enabled in unified processor")
            except Exception as e:
                logger.warning(f"Failed to initialize Chatterbox: {e}. Using OpenAI TTS only")
                self.use_chatterbox = False
    
    def _init_legacy_tts_client(self):
        """Legacy initialization for TTS client"""
        openai_key = os.getenv('OPENAI_API_KEY') or os.getenv('OPENROUTER_API_KEY')
        if openai_key:
            return openai.OpenAI(api_key=openai_key)
        return None
    
    def _init_legacy_stt_client(self):
        """Legacy initialization for STT client"""
        openrouter_key = os.getenv('OPENROUTER_API_KEY')
        if openrouter_key:
            return openai.OpenAI(
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1"
            )
        return None
    
    def _init_legacy_chatterbox(self):
        """Legacy initialization for Chatterbox"""
        try:
            from .chatterbox_service import chatterbox_service
            return chatterbox_service
        except ImportError:
            return None
    
    def text_to_speech(
        self, 
        text: str, 
        voice: Optional[str] = None,
        agent_type: Optional[str] = 'general',
        conversation_context: Optional[Dict] = None
    ) -> bytes:
        """
        Convert text to speech - legacy compatible interface that returns enhanced features
        """
        # Try enhanced TTS first
        if self.use_chatterbox:
            try:
                audio_bytes, metadata = chatterbox_service.text_to_speech(
                    text=text,
                    agent_type=agent_type,
                    conversation_context=conversation_context
                )
                
                if audio_bytes:
                    if os.getenv('OPTIMIZE_FOR_TWILIO', 'true').lower() == 'true':
                        audio_bytes = chatterbox_service.optimize_for_twilio(audio_bytes)
                    return audio_bytes
                    
            except Exception as e:
                logger.error(f"Chatterbox TTS failed: {e}. Falling back to OpenAI")
        
        # Fallback to OpenAI TTS
        return self._openai_text_to_speech_legacy(text, voice)
    
    def text_to_speech_enhanced(
        self, 
        text: str, 
        voice: Optional[str] = None,
        agent_type: Optional[str] = 'general',
        conversation_context: Optional[Dict] = None
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Enhanced interface that returns metadata
        """
        # Try Chatterbox first if enabled
        if self.use_chatterbox:
            try:
                audio_bytes, metadata = chatterbox_service.text_to_speech(
                    text=text,
                    agent_type=agent_type,
                    conversation_context=conversation_context
                )
                
                if audio_bytes:
                    if os.getenv('OPTIMIZE_FOR_TWILIO', 'true').lower() == 'true':
                        audio_bytes = chatterbox_service.optimize_for_twilio(audio_bytes)
                    
                    metadata['tts_engine'] = 'chatterbox'
                    return audio_bytes, metadata
                    
            except Exception as e:
                logger.error(f"Chatterbox TTS failed: {e}. Falling back to OpenAI")
        
        # Fallback to OpenAI TTS
        return self._openai_text_to_speech(text, voice)
    
    def _openai_text_to_speech_legacy(self, text: str, voice: Optional[str] = None) -> bytes:
        """Legacy OpenAI TTS interface"""
        try:
            if not self.tts_client:
                logger.warning("TTS client not available - returning empty audio")
                return b""
            
            voice_name = voice or self.default_voice
            
            if len(text) > 4000:
                text = text[:4000] + "..."
            
            response = self.tts_client.audio.speech.create(
                model=self.tts_model,
                voice=voice_name,
                input=text,
                response_format="mp3"
            )
            
            logger.info(f"Generated OpenAI TTS using voice: {voice_name}")
            return response.content
            
        except Exception as e:
            logger.error(f"OpenAI TTS error: {e}")
            return b""
    
    def _openai_text_to_speech(self, text: str, voice: Optional[str] = None) -> Tuple[bytes, Dict[str, Any]]:
        """Enhanced OpenAI TTS with metadata"""
        try:
            if not self.tts_client:
                logger.warning("TTS client not available - returning empty audio")
                return b"", {"error": "No TTS client available"}
            
            voice_name = voice or self.default_voice
            
            if len(text) > 4000:
                text = text[:4000] + "..."
            
            response = self.tts_client.audio.speech.create(
                model=self.tts_model,
                voice=voice_name,
                input=text,
                response_format="mp3"
            )
            
            logger.info(f"Generated OpenAI TTS using voice: {voice_name}")
            
            metadata = {
                'tts_engine': 'openai',
                'voice': voice_name,
                'model': self.tts_model,
                'text_length': len(text)
            }
            
            return response.content, metadata
            
        except Exception as e:
            logger.error(f"OpenAI TTS error: {e}")
            return b"", {"error": str(e)}
    
    def speech_to_text(self, audio_data: bytes, audio_format: str = "wav") -> str:
        """Convert speech to text using OpenAI Whisper"""
        try:
            if not self.openai_client:
                logger.warning("STT client not available")
                return ""
            
            audio_file = io.BytesIO(audio_data)
            audio_file.name = f"audio.{audio_format}"
            
            transcript = self.openai_client.audio.transcriptions.create(
                model=self.speech_model,
                file=audio_file,
                response_format="text"
            )
            
            transcribed_text = transcript.strip()
            logger.info(f"Transcribed: {transcribed_text}")
            return transcribed_text
            
        except Exception as e:
            logger.error(f"STT error: {e}")
            return ""
    
    def create_twiml_audio_response(
        self, 
        text: str, 
        voice: Optional[str] = None,
        agent_type: Optional[str] = 'general',
        conversation_context: Optional[Dict] = None
    ) -> str:
        """Create TwiML response with enhanced audio capabilities"""
        try:
            from twilio.twiml.voice_response import VoiceResponse
            response = VoiceResponse()
            
            # Generate audio with enhanced capabilities
            audio_bytes, metadata = self.text_to_speech_enhanced(
                text=text,
                voice=voice,
                agent_type=agent_type,
                conversation_context=conversation_context
            )
            
            if audio_bytes and metadata.get('tts_engine') == 'chatterbox':
                logger.info(f"Generated Chatterbox audio with emotion: {metadata.get('emotion', 'neutral')}")
                # TODO: Implement audio serving endpoint for custom audio
                # For now, fallback to Twilio TTS
                response.say(text, voice='alice')
            else:
                # Use Twilio's built-in TTS
                response.say(text, voice='alice')
            
            return str(response)
            
        except Exception as e:
            logger.error(f"Error creating TwiML audio response: {e}")
            from twilio.twiml.voice_response import VoiceResponse
            response = VoiceResponse()
            response.say("I'm sorry, there was an audio processing error.")
            return str(response)
    
    def get_voice_settings(self, agent_type: str) -> Dict[str, Any]:
        """Get voice settings for specific agent type"""
        # Voice mapping for OpenAI fallback
        openai_voice_mapping = {
            'general': 'alloy',
            'billing': 'nova',
            'support': 'echo',
            'sales': 'fable',
            'scheduling': 'shimmer'
        }
        
        # Emotion tendencies for different agents
        emotion_mapping = {
            'general': 'neutral',
            'billing': 'empathetic',
            'support': 'calm',
            'sales': 'excited',
            'scheduling': 'neutral'
        }
        
        return {
            'voice': openai_voice_mapping.get(agent_type, 'alloy'),
            'default_emotion': emotion_mapping.get(agent_type, 'neutral'),
            'agent_type': agent_type,
            'use_chatterbox': self.use_chatterbox
        }
    
    def process_twilio_recording(self, recording_url: str) -> str:
        """Process Twilio recording URL and transcribe"""
        try:
            import requests
            
            response = requests.get(recording_url)
            if response.status_code == 200:
                audio_data = response.content
                return self.speech_to_text(audio_data, "wav")
            else:
                logger.error(f"Failed to download recording: {response.status_code}")
                return ""
                
        except Exception as e:
            logger.error(f"Error processing Twilio recording: {e}")
            return ""
    
    def optimize_text_for_speech(self, text: str) -> str:
        """Optimize text for better speech synthesis"""
        optimized = text.replace("&", "and")
        optimized = optimized.replace("@", "at")
        optimized = optimized.replace("#", "number")
        optimized = optimized.replace("$", "dollars")
        optimized = optimized.replace("%", "percent")
        
        # Add pauses for better flow
        optimized = optimized.replace(". ", ". <break time='0.5s'/> ")
        optimized = optimized.replace("! ", "! <break time='0.5s'/> ")
        optimized = optimized.replace("? ", "? <break time='0.5s'/> ")
        
        # Limit length
        if len(optimized) > 500:
            sentences = optimized.split('. ')
            optimized = '. '.join(sentences[:3]) + '.'
        
        return optimized
    
    def get_available_voices(self) -> Dict[str, Any]:
        """Get list of available voices"""
        return {
            "openai_voices": {
                "alloy": {"name": "Alloy", "description": "Balanced, clear voice", "gender": "neutral"},
                "echo": {"name": "Echo", "description": "Deep, resonant voice", "gender": "male"},
                "fable": {"name": "Fable", "description": "Warm, storytelling voice", "gender": "male"},
                "onyx": {"name": "Onyx", "description": "Strong, confident voice", "gender": "male"},
                "nova": {"name": "Nova", "description": "Bright, energetic voice", "gender": "female"},
                "shimmer": {"name": "Shimmer", "description": "Soft, gentle voice", "gender": "female"}
            },
            "twilio_voices": {
                "alice": "Clear female voice (Twilio)",
                "man": "Male voice (Twilio)",
                "woman": "Female voice (Twilio)"
            },
            "chatterbox_enabled": self.use_chatterbox
        }

# Factory function for creating instances with proper dependency injection
def create_unified_voice_processor(
    tts_client=None,
    stt_client=None,
    chatterbox_service=None,
    use_chatterbox=True,
    default_voice='alloy',
    speech_model='whisper-1',
    tts_model='tts-1',
    optimize_for_twilio=True,
):
    """Factory function for dependency injection"""
    return UnifiedVoiceProcessor(
        tts_client=tts_client,
        stt_client=stt_client,
        chatterbox_service=chatterbox_service,
        use_chatterbox=use_chatterbox,
        default_voice=default_voice,
        speech_model=speech_model,
        tts_model=tts_model,
        optimize_for_twilio=optimize_for_twilio,
    )

# Global unified voice processor instance with legacy compatibility
voice_processor = UnifiedVoiceProcessor()