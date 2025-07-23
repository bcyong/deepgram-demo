from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import List, Optional
from ..utils.deepgram_client import create_deepgram_client
from ..utils.google_cloud_storage_client import list_files, generate_signed_urls
import uuid
from datetime import datetime, timezone
from loguru import logger
from ..utils.keyterm_manager import get_all_keyterms
from ..utils.keyword_manager import get_all_keywords
from urllib.parse import quote_plus

NOVA_3_MODELS = ["nova-3", "nova-3-general", "nova-3-medical"]


class TranscribeAudioRequest(BaseModel):
    audio_urls: List[str]
    language: str = "en-US"
    model: str = "nova-3"
    summarize: str = "v2"
    sentiment: bool = True
    intents: bool = True
    topics: bool = True
    diarize: bool = True
    keyterm: List[str] = []
    keywords: List[str] = []
    search_terms: List[str] = []
    use_url_as_filename: bool = False
    filename_prefix: Optional[str] = ""
    storage_bucket_name: Optional[str] = ""
    storage_folder_name: Optional[str] = ""
    user_callback_url: Optional[str] = ""


class TranscribeAudioResponse(BaseModel):
    batch_id: str
    audio_urls: List[str]
    status: str
    submitted_at: str
    user_callback_url: str
    success_count: int
    error_count: int


class TranscribeGCSRequest(BaseModel):
    bucket_name: str
    folder_name: str = ""
    language: str = "en-US"
    model: str = "nova-3"
    summarize: str = "v2"
    sentiment: bool = True
    intents: bool = True
    topics: bool = True
    diarize: bool = True
    keyterm: List[str] = []
    keywords: List[str] = []
    search_terms: List[str] = []
    use_url_as_filename: bool = False
    filename_prefix: Optional[str] = ""
    storage_bucket_name: Optional[str] = ""
    storage_folder_name: Optional[str] = ""
    user_callback_url: Optional[str] = ""


class TranscribeGCSResponse(BaseModel):
    batch_id: str
    bucket_name: str
    folder_name: str
    audio_files: List[str]
    status: str
    submitted_at: str
    user_callback_url: str
    success_count: int
    error_count: int


router = APIRouter(prefix="/api/v1/transcribe")


async def submit_transcription_requests(
    http_request: Request,
    audio_urls: List[str],
    batch_id: str,
    request: TranscribeAudioRequest,
):
    """
    Submit transcription requests for a list of audio URLs.

    Args:
        http_request: FastAPI request object for building callback URL
        audio_urls: List of audio URLs to transcribe
        batch_id: Unique batch identifier
        request: The original request object containing all parameters

    Returns:
        dict: Dictionary with 'success_count' and 'error_count' keys
    """

    # Create Deepgram client
    deepgram_client = create_deepgram_client()

    # Build full URL for internal webhook endpoint
    base_url = str(http_request.base_url).rstrip("/")
    internal_callback_url = f"{base_url}/api/v1/webhook/deepgram/batch_url_completed"

    # Build full list of keyterms or keywords depending on model
    if request.model in NOVA_3_MODELS:
        global_keyterms = await get_all_keyterms()
        logger.info(f"Global keyterms: {global_keyterms}")
        logger.info(f"Request keyterms: {request.keyterm}")
        keyterms = global_keyterms + request.keyterm
        logger.info(f"Keyterms: {keyterms}")
        keywords = []
    else:
        # For other models: merge list of "keyword:int" strings with dict of "key:int"
        global_keywords = await get_all_keywords()
        logger.info(f"Global keywords: {global_keywords}")
        logger.info(f"Request keywords: {request.keywords}")
        keywords = global_keywords + request.keywords
        logger.info(f"Keywords: {keywords}")
        keyterms = []

    # URL-encode search terms if present
    if hasattr(request, "search_terms") and request.search_terms:
        encoded_search_terms = [quote_plus(term) for term in request.search_terms]
    else:
        encoded_search_terms = []

    # Track success and error counts
    success_count = 0
    error_count = 0

    # Submit each URL for transcription with extra data
    for i, audio_url in enumerate(audio_urls):
        try:
            # Build options for Deepgram API with comprehensive extra data
            extra_data = {
                "batch_id": batch_id,
                "url_index": i,
                "audio_url": audio_url,
                "summarize": request.summarize,
                "sentiment": request.sentiment,
                "intents": request.intents,
                "topics": request.topics,
                "diarize": request.diarize,
                "total_urls": len(audio_urls),
                "storage_bucket_name": request.storage_bucket_name,
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
                "topics": request.topics,
                "diarize": request.diarize,
                "keyterm": keyterms,
                "keywords": keywords,
                "search": encoded_search_terms,
                "callback": internal_callback_url,  # Full URL for internal webhook endpoint
            }

            # Add extra data as query parameters in the format expected by PrerecordedOptions
            extra_list = [f"{key}:{value}" for key, value in extra_data.items()]
            options["extra"] = extra_list

            # Submit transcription request to Deepgram
            # The extra data will be passed back in the webhook callback
            response = deepgram_client.transcribe_audio_url(audio_url, **options)

            logger.info(f"Deepgram client response: {response}")
            success_count += 1

        except Exception as e:
            # Log error but continue with other URLs
            # In a production system, you might want to handle this differently
            logger.error(
                f"Error submitting transcription for URL {audio_url}: {str(e)}"
            )
            logger.error(f"Full error details: {type(e).__name__}: {str(e)}")
            error_count += 1

    logger.info(
        f"Transcription submission complete. Success: {success_count}, Errors: {error_count}"
    )
    return {"success_count": success_count, "error_count": error_count}


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

        # Validate storage bucket name
        if request.storage_bucket_name:
            if not request.storage_bucket_name.startswith("gs://"):
                raise HTTPException(
                    status_code=400,
                    detail="Storage bucket name must start with 'gs://'",
                )

        # Validate storage folder name
        if request.storage_folder_name:
            if not request.storage_folder_name.endswith("/"):
                request.storage_folder_name = request.storage_folder_name + "/"

        submission_results = await submit_transcription_requests(
            http_request, request.audio_urls, batch_id, request
        )

        return TranscribeAudioResponse(
            batch_id=batch_id,
            audio_urls=request.audio_urls,
            storage_bucket_name=request.storage_bucket_name,
            storage_folder_name=request.storage_folder_name,
            status="submitted",
            submitted_at=datetime.now(timezone.utc).isoformat(),
            user_callback_url=request.user_callback_url or "",
            success_count=submission_results["success_count"],
            error_count=submission_results["error_count"],
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to submit transcription batch: {str(e)}"
        )


@router.post("/batch-gcs", response_model=TranscribeGCSResponse, tags=["transcribe"])
async def transcribe_gcs_batch(request: TranscribeGCSRequest, http_request: Request):
    """
    Submit a batch of audio files from Google Cloud Storage for transcription.

    This endpoint lists all files in the specified GCS bucket and folder,
    converts them to GCS URLs, and submits them for transcription.
    Each transcription will be processed asynchronously and results will be
    sent to the internal webhook endpoint when complete.

    The user callback URL will be called when each transcription is complete.
    All request tracking is handled via extra data passed to Deepgram.
    """

    logger.info(f"Transcribe GCS batch request: {request}")
    try:
        # Generate a unique request ID for this batch
        batch_id = str(uuid.uuid4())

        # Validate input
        if not request.bucket_name:
            raise HTTPException(status_code=400, detail="Bucket name is required")

        # List files in the GCS bucket and folder
        try:
            audio_files = list_files(request.bucket_name, request.folder_name)
            logger.info(
                f"Found {len(audio_files)} files in GCS bucket {request.bucket_name}, folder: {request.folder_name or 'root'}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to list files in GCS bucket {request.bucket_name}: {str(e)}",
            )

        if not audio_files:
            raise HTTPException(
                status_code=400,
                detail=f"No files found in GCS bucket {request.bucket_name}, folder: {request.folder_name or 'root'}",
            )

        # Generate signed URLs for GCS blobs so Deepgram can access them
        try:
            audio_urls = generate_signed_urls(request.bucket_name, audio_files)
            logger.info(f"Generated {len(audio_urls)} signed URLs for Deepgram access")

            if not audio_urls:
                raise HTTPException(
                    status_code=400,
                    detail=f"No valid files found in GCS bucket {request.bucket_name}, folder: {request.folder_name or 'root'}",
                )

        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to generate signed URLs for GCS bucket {request.bucket_name}: {str(e)}",
            )

        # Create a TranscribeAudioRequest object for the helper function
        class GCSRequestAdapter:
            def __init__(self, gcs_request: TranscribeGCSRequest):
                self.audio_urls = audio_urls  # Will be set after URL conversion
                self.language = gcs_request.language
                self.model = gcs_request.model
                self.summarize = gcs_request.summarize
                self.sentiment = gcs_request.sentiment
                self.intents = gcs_request.intents
                self.topics = gcs_request.topics
                self.diarize = gcs_request.diarize
                self.keyterm = gcs_request.keyterm
                self.keywords = gcs_request.keywords
                self.search_terms = gcs_request.search_terms
                self.use_url_as_filename = gcs_request.use_url_as_filename
                self.filename_prefix = gcs_request.filename_prefix
                self.storage_bucket_name = gcs_request.storage_bucket_name
                self.storage_folder_name = gcs_request.storage_folder_name
                self.user_callback_url = gcs_request.user_callback_url

        # Create adapter and set the audio URLs
        adapter_request = GCSRequestAdapter(request)
        adapter_request.audio_urls = audio_urls

        # Submit transcription requests using the existing helper
        submission_results = await submit_transcription_requests(
            http_request, audio_urls, batch_id, adapter_request
        )

        return TranscribeGCSResponse(
            batch_id=batch_id,
            bucket_name=request.bucket_name,
            folder_name=request.folder_name,
            audio_files=audio_files,
            status="submitted",
            submitted_at=datetime.now(timezone.utc).isoformat(),
            user_callback_url=request.user_callback_url or "",
            success_count=submission_results["success_count"],
            error_count=submission_results["error_count"],
        )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to submit GCS transcription batch: {str(e)}",
        )
