from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import json
from datetime import datetime, timezone
import tempfile
import os
import httpx
from loguru import logger
from ..utils.google_cloud_storage_client import upload_file
from ..utils.deepgram_parser import (
    build_transcript,
    extract_summary,
    extract_intents,
    extract_sentiment,
    extract_topics,
    build_filename,
)

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
    sentiment_score: Optional[float] = None
    extreme_sentiment_scores: Optional[List[float]] = None
    intents: Optional[List[str]] = None
    topics: Optional[List[str]] = None
    submitted_at: str
    completed_at: str


def call_user_callback(user_callback_url: str, data: Dict) -> bool:
    """
    Helper function to call a user-provided callback URL with transcription data.
    """
    try:
        response = httpx.post(user_callback_url, json=data)
        response.raise_for_status()
        logger.info(f"Successfully called user callback URL: {user_callback_url}")
        return True
    except httpx.RequestError as e:
        logger.error(f"Failed to call user callback URL {user_callback_url}: {e}")
        return False


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

        # Extract data from the webhook
        metadata = webhook_data.get("metadata", {})
        request_id = metadata.get("request_id")
        results_data = webhook_data.get("results", {})

        # Extract extra data from the metadata
        extra_data = metadata.get("extra", {})
        batch_id = extra_data.get("batch_id", "unknown")
        url_index = extra_data.get("url_index", 0)
        audio_url = extra_data.get("audio_url", "unknown")
        summarize = extra_data.get("summarize", "false")
        sentiment_enabled = (
            True if extra_data.get("sentiment", "False").lower() == "true" else False
        )
        intents_enabled = (
            True if extra_data.get("intents", "False").lower() == "true" else False
        )
        topics_enabled = (
            True if extra_data.get("topics", "False").lower() == "true" else False
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
        storage_bucket_name = extra_data.get("storage_bucket_name", "")
        storage_folder_name = extra_data.get("storage_folder_name", "")
        user_callback_url = extra_data.get("user_callback_url", "")

        logger.info(f"Extra data: {extra_data}")

        # Extract transcription results and build transcript
        try:
            transcript, confidence = build_transcript(results_data, diarize)
        except ValueError as e:
            logger.error(f"Error building transcript: {str(e)}")
            raise HTTPException(status_code=400, detail=str(e))

        logger.info(f"Transcript: {transcript[:100]}... (confidence: {confidence})")

        # Extract summary from the results
        if summarize:
            summary = extract_summary(results_data, summarize)
        else:
            summary = ""
        logger.info(f"Summary: {summary}")

        # Extract sentiment from the results
        if sentiment_enabled:
            sentiment, sentiment_score, extreme_sentiment_scores = extract_sentiment(
                results_data
            )
        else:
            sentiment = ""
            sentiment_score = 0.0
            extreme_sentiment_scores = []
        logger.info(
            f"Sentiment: {sentiment} (score: {sentiment_score}, extreme scores: {extreme_sentiment_scores})"
        )

        # Extract intents from the results
        if intents_enabled:
            intents = extract_intents(results_data)
        else:
            intents = []
        logger.info(f"Intents: {intents}")

        # Extract topics from the results
        if topics_enabled:
            topics = extract_topics(results_data)
        else:
            topics = []
        logger.info(f"Topics: {topics}")

        completed_at = datetime.now(timezone.utc).isoformat()

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
            sentiment_score=sentiment_score,
            extreme_sentiment_scores=extreme_sentiment_scores,
            intents=intents,
            topics=topics,
            submitted_at=submitted_at,
            completed_at=completed_at,
        )

        # Convert to JSON for file output
        output_json = formatted_response.model_dump()

        filename = build_filename(
            use_url_as_filename=use_url_as_filename,
            filename_prefix=filename_prefix,
            storage_bucket_name=storage_bucket_name,
            storage_folder_name=storage_folder_name,
            audio_url=audio_url,
            batch_id=batch_id,
            url_index=url_index,
        )

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

        # Call user callback if provided
        if user_callback_url != "":
            callback_data = {
                "audio_url": audio_url,
                "batch_id": batch_id,
                "batch_index": url_index,
                "deepgram_request_id": request_id,
                "output_file_location": f"gs://yonger-deepgram-demo/transcriptions/{filename}",
                "summary": summary,
                "sentiment": sentiment,
                "sentiment_score": sentiment_score,
                "extreme_sentiment_scores": extreme_sentiment_scores,
                "intents": intents,
                "topics": topics,
                "submitted_at": submitted_at,
                "completed_at": completed_at,
            }
            call_user_callback(user_callback_url, callback_data)

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
