from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from ..utils.deepgram_client import create_deepgram_client
import uuid
from datetime import datetime, timezone
from loguru import logger


class TranscribeAudioRequest(BaseModel):
    audio_urls: List[str]
    language: str = "en-US"
    model: str = "nova-3"
    summarize: str = "v2"
    sentiment: bool = True
    intents: bool = True
    diarize: bool = True
    keyterm: List[str] = []
    keywords: List[str] = []
    use_url_as_filename: bool = False
    filename_prefix: Optional[str] = None
    storage_location: Optional[str] = None
    storage_folder_name: Optional[str] = None
    user_callback_url: Optional[str] = None


class TranscribeAudioResponse(BaseModel):
    batch_id: str
    audio_urls: List[str]
    status: str
    submitted_at: str
    user_callback_url: str


router = APIRouter(prefix="/api/v1/transcribe")


@router.post("/batch-url", response_model=TranscribeAudioResponse, tags=["transcribe"])
async def transcribe_audio_batch(
    request: TranscribeAudioRequest, http_request: Request
):
    """
    Submit a batch of audio URLs for transcription.

    This endpoint initiates transcription requests for multiple audio files.
    Each transcription will be processed asynchronously and results will be
    sent to the internal webhook endpoint when complete.

    The user callback URL will be called when each transcription is complete.
    All request tracking is handled via extra data passed to Deepgram.
    """

    logger.info(f"Transcribe audio batch request: {request}")
    try:
        # Generate a unique request ID for this batch
        batch_id = str(uuid.uuid4())

        # Validate input
        if not request.audio_urls:
            raise HTTPException(
                status_code=400, detail="At least one audio URL is required"
            )

        # if not request.storage_location:
        #     raise HTTPException(status_code=400, detail="Storage location is required")

        # Create Deepgram client
        deepgram_client = create_deepgram_client()

        # Build full URL for internal webhook endpoint
        base_url = str(http_request.base_url).rstrip("/")
        internal_callback_url = (
            f"{base_url}/api/v1/webhook/deepgram/batch_url_completed"
        )

        # Submit each URL for transcription with extra data
        for i, audio_url in enumerate(request.audio_urls):
            try:
                # Build options for Deepgram API with comprehensive extra data
                extra_data = {
                    "batch_id": batch_id,
                    "url_index": i,
                    "audio_url": audio_url,
                    "summarize": request.summarize,
                    "sentiment": request.sentiment,
                    "intents": request.intents,
                    "diarize": request.diarize,
                    "total_urls": len(request.audio_urls),
                    "storage_location": request.storage_location,
                    "storage_folder_name": request.storage_folder_name,
                    "use_url_as_filename": request.use_url_as_filename,
                    "filename_prefix": request.filename_prefix,
                    "submitted_at": datetime.now(timezone.utc).isoformat(),
                    "user_callback_url": request.user_callback_url,  # User callback in extra data
                }

                options = {
                    "model": request.model,
                    "language": request.language,
                    "smart_format": True,
                    "punctuate": True,
                    "summarize": request.summarize,
                    "sentiment": request.sentiment,
                    "intents": request.intents,
                    "diarize": request.diarize,
                    "keyterm": request.keyterm,
                    "keywords": request.keywords,
                    "callback": internal_callback_url,  # Full URL for internal webhook endpoint
                }

                # Add extra data as query parameters in the format expected by PrerecordedOptions
                extra_list = [f"{key}:{value}" for key, value in extra_data.items()]
                options["extra"] = extra_list

                # Submit transcription request to Deepgram
                # The extra data will be passed back in the webhook callback
                response = deepgram_client.transcribe_audio_url(audio_url, **options)

                logger.info(f"Deepgram client response: {response}")

            except Exception as e:
                # Log error but continue with other URLs
                # In a production system, you might want to handle this differently
                logger.error(
                    f"Error submitting transcription for URL {audio_url}: {str(e)}"
                )

        return TranscribeAudioResponse(
            batch_id=batch_id,
            audio_urls=request.audio_urls,
            storage_location=request.storage_location,
            status="submitted",
            submitted_at=datetime.now(timezone.utc).isoformat(),
            user_callback_url=request.user_callback_url or "",
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to submit transcription batch: {str(e)}"
        )
