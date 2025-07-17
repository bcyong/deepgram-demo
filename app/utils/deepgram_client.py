import os
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from deepgram import DeepgramClient, PrerecordedOptions, FileSource

load_dotenv()

class DeepgramWrapper:
    """
    Wrapper for Deepgram SDK providing simplified access to Deepgram's AI services.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the Deepgram wrapper.
        
        Args:
            api_key: Deepgram API key. If not provided, will try to get from
                    DEEPGRAM_API_KEY environment variable.
        """
        self.api_key = api_key or os.getenv('DEEPGRAM_API_KEY')
        if not self.api_key:
            raise ValueError("Deepgram API key is required. Set DEEPGRAM_API_KEY environment variable or pass api_key parameter.")
        
        self.client = DeepgramClient(self.api_key)
    
    def transcribe_audio(self, 
                        audio_url: str, 
                        language: str = "en-US",
                        model: str = "nova-3",
                        smart_format: bool = True,
                        punctuate: bool = True,
                        **kwargs) -> Dict[str, Any]:
        """
        Transcribe audio from a URL using Deepgram's speech-to-text.
        
        Args:
            audio_url: URL to the audio file
            language: Language code (e.g., "en-US", "es-ES")
            model: Deepgram model to use (e.g., "nova-2", "enhanced")
            smart_format: Enable smart formatting
            punctuate: Enable punctuation
            **kwargs: Additional options to pass to Deepgram
            
        Returns:
            Dict containing transcription results
        """
        try:
            # Build options dict for Deepgram API
            options = {
                "model": model,
                "language": language,
                "smart_format": smart_format,
                "punctuate": punctuate,
                **kwargs
            }
            
            # Use the REST API for transcription
            response = self.client.listen.rest.v("1").transcribe_url(
                {"url": audio_url}, options
            )
            
            # Extract results from response
            transcript = ""
            confidence = 0.0
            
            if hasattr(response, 'results') and response.results:
                if hasattr(response.results, 'channels') and response.results.channels:
                    channel = response.results.channels[0]
                    if hasattr(channel, 'alternatives') and channel.alternatives:
                        alternative = channel.alternatives[0]
                        transcript = getattr(alternative, 'transcript', '')
                        confidence = getattr(alternative, 'confidence', 0.0)
            
            return {
                "transcript": transcript,
                "confidence": confidence,
                "metadata": {
                    "model": model,
                    "language": language,
                    "url": audio_url
                }
            }
            
        except Exception as e:
            raise Exception(f"Transcription failed: {str(e)}")
    
    def transcribe_file(self, 
                       file_path: str,
                       language: str = "en-US",
                       model: str = "nova-3",
                       smart_format: bool = True,
                       punctuate: bool = True,
                       **kwargs) -> Dict[str, Any]:
        """
        Transcribe audio from a local file using Deepgram's speech-to-text.
        
        Args:
            file_path: Path to the local audio file
            language: Language code (e.g., "en-US", "es-ES")
            model: Deepgram model to use (e.g., "nova-3", "enhanced")
            smart_format: Enable smart formatting
            punctuate: Enable punctuation
            **kwargs: Additional options to pass to Deepgram
            
        Returns:
            Dict containing transcription results
        """
        try:
            # Build options dict for Deepgram API
            options = {
                "model": model,
                "language": language,
                "smart_format": smart_format,
                "punctuate": punctuate,
                **kwargs
            }
            
            # Open and transcribe the local file
            with open(file_path, "rb") as audio_file:

              buffer_data = audio_file.read()
              payload: FileSource = {
                  "buffer": buffer_data,
              }

              response = self.client.listen.rest.v("1").transcribe_file(payload, options)

            # Extract results from response (same logic as transcribe_audio)
            transcript = ""
            confidence = 0.0
            
            if hasattr(response, 'results') and response.results:
                if hasattr(response.results, 'channels') and response.results.channels:
                    channel = response.results.channels[0]
                    if hasattr(channel, 'alternatives') and channel.alternatives:
                        alternative = channel.alternatives[0]
                        transcript = getattr(alternative, 'transcript', '')
                        confidence = getattr(alternative, 'confidence', 0.0)
            
            return {
                "transcript": transcript,
                "confidence": confidence,
                "metadata": {
                    "model": model,
                    "language": language,
                    "file_path": file_path
                }
            }
            
        except FileNotFoundError:
            raise Exception(f"Audio file not found: {file_path}")
        except Exception as e:
            raise Exception(f"File transcription failed: {str(e)}")


# Convenience function to create a Deepgram wrapper instance
def create_deepgram_client(api_key: Optional[str] = None) -> DeepgramWrapper:
    """
    Create a Deepgram wrapper instance.
    """
    return DeepgramWrapper(api_key) 