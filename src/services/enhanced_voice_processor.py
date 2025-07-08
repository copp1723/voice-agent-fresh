"""
Enhanced Voice Processing Service with Chatterbox Integration
Provides emotion-aware TTS with fallback to OpenAI
"""
import os
import logging
import io
import base64
from typing import Optional, Dict, Any, Tuple
import openai
from .chatterbox_service import chatterbox_service

logger = logging.getLogger(__name__)

class EnhancedVoiceProcessor:
    """
    Enhanced voice processing with Chatterbox TTS and OpenAI fallback
    """
    
    def __init__(self):
        # Initialize OpenAI clients (for STT and fallback TTS)
        openrouter_key = os.getenv('OPENROUTER_API_KEY')
        openai_key = os.getenv('OPENAI_API_KEY', openrouter_key)
        
        if openrouter_key:
            self.openai_client = openai.OpenAI(
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1"
            )
        else:
            self.openai_client = None
        
        if openai_key:
            self.tts_client = openai.OpenAI(api_key=openai_key)
        else:
            self.tts_client = None
        
        # Configuration
        self.use_chatterbox = os.getenv('USE_CHATTERBOX', 'true').lower() == 'true'
        self.default_voice = os.getenv('DEFAULT_VOICE', 'alloy')
        self.speech_model = 'whisper-1'
        self.tts_model = 'tts-1'
        
        # Initialize Chatterbox if enabled
        if self.use_chatterbox:
            try:
                chatterbox_service.load_model()
                logger.info("Chatterbox TTS enabled")
            except Exception as e:
                logger.warning(f"Failed to initialize Chatterbox: {e}. Falling back to OpenAI TTS")
                self.use_chatterbox = False
    
    def text_to_speech(
        self, 
        text: str, 
        voice: Optional[str] = None,
        agent_type: Optional[str] = 'general',
        conversation_context: Optional[Dict] = None
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Convert text to speech with emotion awareness
        
        Args:
            text: Text to convert
            voice: Voice to use (for OpenAI fallback)
            agent_type: Type of agent for voice selection
            conversation_context: Conversation history for emotion detection
            
        Returns:
            Tuple of (audio_bytes, metadata)
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
                    # Optimize for Twilio if needed
                    if os.getenv('OPTIMIZE_FOR_TWILIO', 'true').lower() == 'true':
                        audio_bytes = chatterbox_service.optimize_for_twilio(audio_bytes)
                    
                    metadata['tts_engine'] = 'chatterbox'
                    return audio_bytes, metadata
                    
            except Exception as e:
                logger.error(f"Chatterbox TTS failed: {e}. Falling back to OpenAI")
        
        # Fallback to OpenAI TTS
        return self._openai_text_to_speech(text, voice)
    
    def _openai_text_to_speech(self, text: str, voice: Optional[str] = None) -> Tuple[bytes, Dict[str, Any]]:
        """
        OpenAI TTS fallback
        """
        try:
            if not self.tts_client:
                logger.warning("TTS client not available - returning empty audio")
                return b"", {"error": "No TTS client available"}
            
            voice_name = voice or self.default_voice
            
            # Ensure text is not too long
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
        """
        Convert speech to text using OpenAI Whisper
        """
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
        """
        Create TwiML response with Chatterbox audio for Twilio
        """
        try:
            from twilio.twiml.voice_response import VoiceResponse
            response = VoiceResponse()
            
            # Generate audio with emotion awareness
            audio_bytes, metadata = self.text_to_speech(
                text=text,
                voice=voice,
                agent_type=agent_type,
                conversation_context=conversation_context
            )
            
            if audio_bytes and metadata.get('tts_engine') == 'chatterbox':
                # For Chatterbox audio, we need to serve it via URL
                # In production, this would upload to S3/CDN and return URL
                # For now, we'll use Twilio's built-in TTS as fallback
                logger.info(f"Generated Chatterbox audio with emotion: {metadata.get('emotion', 'neutral')}")
                
                # TODO: Implement audio serving endpoint
                # audio_url = self._upload_audio_to_cdn(audio_bytes)
                # response.play(audio_url)
                
                # Temporary fallback
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
    
    def analyze_conversation_sentiment(self, messages: list) -> Dict[str, Any]:
        """
        Analyze conversation sentiment for emotion detection
        
        Args:
            messages: List of conversation messages
            
        Returns:
            Sentiment analysis results
        """
        if not messages:
            return {'sentiment': 'neutral', 'confidence': 0.0}
        
        # Simple sentiment analysis based on keywords
        positive_words = ['thank', 'great', 'excellent', 'happy', 'good', 'love', 'appreciate']
        negative_words = ['angry', 'frustrated', 'upset', 'problem', 'issue', 'hate', 'terrible']
        
        positive_count = 0
        negative_count = 0
        
        for msg in messages[-5:]:  # Look at last 5 messages
            text_lower = msg.get('content', '').lower()
            positive_count += sum(1 for word in positive_words if word in text_lower)
            negative_count += sum(1 for word in negative_words if word in text_lower)
        
        if negative_count > positive_count:
            return {'sentiment': 'negative', 'confidence': 0.7}
        elif positive_count > negative_count:
            return {'sentiment': 'positive', 'confidence': 0.7}
        else:
            return {'sentiment': 'neutral', 'confidence': 0.5}
    
    def get_voice_settings(self, agent_type: str) -> Dict[str, Any]:
        """
        Get voice settings for specific agent type
        """
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
        """
        Process Twilio recording URL and transcribe
        """
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
        """
        Optimize text for better speech synthesis
        """
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

# Create enhanced processor instance
enhanced_voice_processor = EnhancedVoiceProcessor()