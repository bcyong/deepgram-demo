from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import json
from datetime import datetime, timezone
import tempfile
import os
from loguru import logger
from ..utils.google_cloud_storage_client import upload_file

router = APIRouter(prefix="/api/v1/webhook")


class DeepgramBatchURLCompletedWebhookResponse(BaseModel):
    """Formatted response for file output"""

    batch_id: str
    request_id: str
    url_index: int
    audio_url: str
    total_urls: int
    transcript: str
    confidence: float
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    intents: Optional[List[str]] = None
    submitted_at: str
    completed_at: str


def build_transcript(results: Dict[str, Any], diarize: bool = False) -> str:
    """
    Build transcript from Deepgram results.

    Args:
        results: The results object from Deepgram webhook data
        diarize: Whether to build a diarized transcript

    Returns:
        Formatted transcript string
    """
    channels = results.get("channels", [])

    if not channels:
        raise ValueError("No channels found in webhook data")

    channel = channels[0]
    alternatives = channel.get("alternatives", [])

    if not alternatives:
        raise ValueError("No transcription alternatives found")

    alternative = alternatives[0]

    if diarize:
        logger.info("Building diarized transcript")
        # Build diarized transcript from words array
        words = alternative.get("words", [])
        if not words:
            logger.warning(
                "No words found for diarization, falling back to regular transcript"
            )
            return alternative.get("transcript", "")

        # Build diarized transcript preserving conversation flow
        diarized_lines = []
        current_speaker = None
        current_segment = []

        for word in words:
            speaker = word.get("speaker", 0)
            word_text = word.get("word", "")

            # If speaker changes, save current segment and start new one
            if current_speaker is not None and speaker != current_speaker:
                if current_segment:
                    speaker_text = " ".join(current_segment)
                    diarized_lines.append(f"Speaker {current_speaker}: {speaker_text}")
                current_segment = []

            current_speaker = speaker
            current_segment.append(word_text)

        # Don't forget the last segment
        if current_segment:
            speaker_text = " ".join(current_segment)
            diarized_lines.append(f"Speaker {current_speaker}: {speaker_text}")

        transcript = "\n".join(diarized_lines)
        logger.info(
            f"Built diarized transcript with {len(set(word.get('speaker', 0) for word in words))} speakers"
        )
        return transcript
    else:
        logger.info("Building non-diarized transcript")
        return alternative.get("transcript", "")


@router.post("/deepgram/batch_url_completed", tags=["webhook"])
async def deepgram_webhook(request: Request):
    """
    Webhook endpoint for receiving Deepgram transcription results.

    This endpoint receives callbacks from Deepgram when individual URL transcription
    is complete within a batch, tracks completion status for each URL,
    formats the response, and prepares it for file output.
    """

    logger.info(f"Deepgram webhook request: {request}")
    try:
        # Parse the incoming webhook payload
        webhook_data = await request.json()

        logger.info(f"Webhook data: {webhook_data}")

        # Extract extra data from the webhook
        metadata = webhook_data.get("metadata", {})
        request_id = metadata.get("request_id")
        extra_data = metadata.get("extra", {})

        batch_id = extra_data.get("batch_id", "unknown")
        url_index = extra_data.get("url_index", 0)
        audio_url = extra_data.get("audio_url", "unknown")
        summarize = extra_data.get("summarize", "v2")
        sentiment = (
            True if extra_data.get("sentiment", "False").lower() == "true" else False
        )
        intents = (
            True if extra_data.get("intents", "False").lower() == "true" else False
        )
        diarize = (
            True if extra_data.get("diarize", "False").lower() == "true" else False
        )
        total_urls = extra_data.get("total_urls", 1)
        submitted_at = extra_data.get("submitted_at", "unknown")
        use_url_as_filename = (
            True
            if extra_data.get("use_url_as_filename", "False").lower() == "true"
            else False
        )
        filename_prefix = extra_data.get("filename_prefix", "")
        user_callback_url = extra_data.get("user_callback_url", "")

        logger.info(f"Extra data: {extra_data}")

        # Extract transcription results and build transcript
        results = webhook_data.get("results", {})
        try:
            transcript = build_transcript(results, diarize)
        except ValueError as e:
            logger.error(f"Error building transcript: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

        # Get confidence from the first alternative
        channels = results.get("channels", [])
        confidence = 0.0
        if channels and channels[0].get("alternatives"):
            confidence = channels[0]["alternatives"][0].get("confidence", 0.0)

        logger.info(f"Transcript: {transcript[:100]}... (confidence: {confidence})")

        summary = None
        sentiment = None
        intents = None

        if summarize == "v2":
            summary = results.get("summary", None)
        if sentiment:
            sentiment = results.get("sentiment", None)
        if intents:
            intents = results.get("intents", None)

        # Create formatted response
        formatted_response = DeepgramBatchURLCompletedWebhookResponse(
            batch_id=batch_id,
            request_id=request_id,
            url_index=url_index,
            audio_url=audio_url,
            total_urls=total_urls,
            transcript=transcript,
            confidence=confidence,
            summary=summary,
            sentiment=sentiment,
            intents=intents,
            submitted_at=submitted_at,
            completed_at=datetime.now(timezone.utc).isoformat(),
        )

        # Convert to JSON for file output
        output_json = formatted_response.model_dump()

        if use_url_as_filename:
            filename = f"{audio_url.split('/')[-1]}.json"
        elif filename_prefix != "":
            filename = f"{filename_prefix}_{url_index}.json"
        else:
            filename = f"{batch_id}_url_{url_index}.json"

        # Create temporary file and upload to GCS
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as temp_file:
                json.dump(output_json, temp_file, indent=2)
                temp_file_path = temp_file.name

            # Upload to Google Cloud Storage
            bucket_name = "yonger-deepgram-demo"
            gcs_filename = f"transcriptions/{filename}"

            upload_success = upload_file(
                bucket_name=bucket_name,
                source_file_name=temp_file_path,
                destination_file_name=gcs_filename,
                overwrite=False,
            )

            if upload_success:
                logger.info(
                    f"Successfully uploaded transcription to GCS: gs://{bucket_name}/{gcs_filename}"
                )
            else:
                logger.warning(
                    f"File upload to GCS failed or file already exists: {gcs_filename}"
                )

        except Exception as e:
            logger.error(f"Failed to create or upload file: {str(e)}")
        finally:
            # Clean up temporary file
            if "temp_file_path" in locals() and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

        logger.info(
            f"Successfully processed webhook for request_id={request_id}, filename={filename}"
        )

        # TODO: Call user callback URL

        return {
            "status": "success",
            "message": f"Transcription result processed: {filename}",
            "request_id": request_id,
            "url_index": url_index,
            "filename": filename,
        }

    except json.JSONDecodeError as e:
        logger.error(f"JSON decode error: {str(e)}")
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        logger.error(f"Webhook processing failed: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Webhook processing failed: {str(e)}"
        )
