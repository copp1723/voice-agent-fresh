"""
Voice Processing Service - Text-to-Speech and Speech-to-Text with OpenAI
"""
import os
import logging
import io
import base64
from typing import Optional, Dict, Any
import openai

logger = logging.getLogger(__name__)

class VoiceProcessor:
    """
    Voice processing service using OpenAI TTS and Whisper
    """
    
    def __init__(self):
        # Get API keys with fallbacks
        openrouter_key = os.getenv('OPENROUTER_API_KEY')
        openai_key = os.getenv('OPENAI_API_KEY', openrouter_key)
        
        # Initialize OpenRouter client for general AI
        if openrouter_key:
            self.openai_client = openai.OpenAI(
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1"
            )
        else:
            self.openai_client = None
        
        # For TTS, we need direct OpenAI API (optional)
        if openai_key:
            self.tts_client = openai.OpenAI(api_key=openai_key)
        else:
            self.tts_client = None
        
        self.default_voice = os.getenv('DEFAULT_VOICE', 'alloy')
        self.speech_model = 'whisper-1'
        self.tts_model = 'tts-1'  # or tts-1-hd for higher quality
        
    def text_to_speech(self, text: str, voice: Optional[str] = None) -> bytes:
        """
        Convert text to speech using OpenAI TTS
        
        Args:
            text: Text to convert to speech
            voice: Voice to use (alloy, echo, fable, onyx, nova, shimmer)
            
        Returns:
            Audio bytes (MP3 format)
        """
        try:
            if not self.tts_client:
                logger.warning("TTS client not available - returning empty audio")
                return b""
            
            voice_name = voice or self.default_voice
            
            # Ensure text is not too long (OpenAI TTS limit is 4096 characters)
            if len(text) > 4000:
                text = text[:4000] + "..."
            
            response = self.tts_client.audio.speech.create(
                model=self.tts_model,
                voice=voice_name,
                input=text,
                response_format="mp3"
            )
            
            logger.info(f"Generated TTS for: {text[:50]}... using voice: {voice_name}")
            return response.content
            
        except Exception as e:
            logger.error(f"TTS error: {e}")
            return b""
    
    def speech_to_text(self, audio_data: bytes, audio_format: str = "wav") -> str:
        """
        Convert speech to text using OpenAI Whisper
        
        Args:
            audio_data: Audio bytes
            audio_format: Audio format (wav, mp3, etc.)
            
        Returns:
            Transcribed text
        """
        try:
            if not self.openai_client:
                logger.warning("STT client not available - returning empty transcription")
                return ""
            
            # Create audio file object
            audio_file = io.BytesIO(audio_data)
            audio_file.name = f"audio.{audio_format}"
            
            # Use Whisper for transcription
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
    
    def create_twiml_audio_response(self, text: str, voice: Optional[str] = None) -> str:
        """
        Create TwiML response with audio for Twilio
        
        Args:
            text: Text to speak
            voice: Voice to use
            
        Returns:
            TwiML XML string
        """
        try:
            # For Twilio, we'll use the built-in TTS for now
            # This is more reliable than streaming custom audio
            from twilio.twiml.voice_response import VoiceResponse
            
            response = VoiceResponse()
            
            # Use Twilio's built-in voices for reliability
            # We can enhance this later with custom audio streaming
            response.say(text, voice='alice')  # Twilio voice
            
            return str(response)
            
        except Exception as e:
            logger.error(f"Error creating TwiML audio response: {e}")
            from twilio.twiml.voice_response import VoiceResponse
            response = VoiceResponse()
            response.say("I'm sorry, there was an audio processing error.")
            return str(response)
    
    def get_available_voices(self) -> Dict[str, Any]:
        """
        Get list of available voices
        
        Returns:
            Dictionary of available voices
        """
        return {
            "openai_voices": {
                "alloy": {
                    "name": "Alloy",
                    "description": "Balanced, clear voice",
                    "gender": "neutral"
                },
                "echo": {
                    "name": "Echo", 
                    "description": "Deep, resonant voice",
                    "gender": "male"
                },
                "fable": {
                    "name": "Fable",
                    "description": "Warm, storytelling voice", 
                    "gender": "male"
                },
                "onyx": {
                    "name": "Onyx",
                    "description": "Strong, confident voice",
                    "gender": "male"
                },
                "nova": {
                    "name": "Nova",
                    "description": "Bright, energetic voice",
                    "gender": "female"
                },
                "shimmer": {
                    "name": "Shimmer",
                    "description": "Soft, gentle voice",
                    "gender": "female"
                }
            },
            "twilio_voices": {
                "alice": "Clear female voice (Twilio)",
                "man": "Male voice (Twilio)",
                "woman": "Female voice (Twilio)"
            }
        }
    
    def process_twilio_recording(self, recording_url: str) -> str:
        """
        Process Twilio recording URL and transcribe
        
        Args:
            recording_url: Twilio recording URL
            
        Returns:
            Transcribed text
        """
        try:
            import requests
            
            # Download recording from Twilio
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
        
        Args:
            text: Original text
            
        Returns:
            Optimized text for TTS
        """
        # Remove or replace problematic characters
        optimized = text.replace("&", "and")
        optimized = optimized.replace("@", "at")
        optimized = optimized.replace("#", "number")
        optimized = optimized.replace("$", "dollars")
        optimized = optimized.replace("%", "percent")
        
        # Add pauses for better speech flow
        optimized = optimized.replace(". ", ". <break time='0.5s'/> ")
        optimized = optimized.replace("! ", "! <break time='0.5s'/> ")
        optimized = optimized.replace("? ", "? <break time='0.5s'/> ")
        
        # Ensure reasonable length
        if len(optimized) > 500:
            # Split into sentences and take first few
            sentences = optimized.split('. ')
            optimized = '. '.join(sentences[:3]) + '.'
        
        return optimized
    
    def get_voice_settings(self, agent_type: str) -> Dict[str, str]:
        """
        Get voice settings for specific agent type
        
        Args:
            agent_type: Type of agent
            
        Returns:
            Voice settings
        """
        voice_mapping = {
            'general': 'alloy',      # Neutral, professional
            'billing': 'nova',       # Friendly, approachable
            'support': 'echo',       # Calm, reassuring
            'sales': 'fable',        # Warm, engaging
            'scheduling': 'shimmer'  # Gentle, organized
        }
        
        return {
            'voice': voice_mapping.get(agent_type, 'alloy'),
            'model': self.tts_model,
            'format': 'mp3'
        }

# Global voice processor instance
voice_processor = VoiceProcessor()

