from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import json
from datetime import datetime
from loguru import logger
import tempfile
import os
from ..utils.google_cloud_storage_client import upload_file

router = APIRouter(prefix="/api/v1/webhook")


class DeepgramBatchURLCompletedWebhookResponse(BaseModel):
    """Formatted response for file output"""

    batch_id: str
    request_id: str
    url_index: int
    total_urls: int
    audio_url: str
    transcript: str
    confidence: float
    submitted_at: str
    completed_at: str


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

        batch_id = extra_data.get("batch_id") or "unknown"
        url_index = extra_data.get("url_index", 0)
        total_urls = extra_data.get("total_urls", 1)
        storage_location = extra_data.get("storage_location") or "unknown"
        submitted_at = extra_data.get("submitted_at") or "unknown"
        user_callback_url = extra_data.get("user_callback_url")

        logger.info(f"Extra data: {extra_data}")

        # Extract transcription results
        results = webhook_data.get("results", {})
        channels = results.get("channels", [])

        if not channels:
            logger.error("No channels found in webhook data")
            raise HTTPException(
                status_code=400, detail="No transcription results found"
            )

        channel = channels[0]
        alternatives = channel.get("alternatives", [])

        if not alternatives:
            logger.error("No alternatives found in channel")
            raise HTTPException(
                status_code=400, detail="No transcription alternatives found"
            )

        alternative = alternatives[0]
        transcript = alternative.get("transcript", "")
        confidence = alternative.get("confidence", 0.0)

        logger.info(
            f"Extracted transcript: {transcript[:50]}... (confidence: {confidence})"
        )

        # Get the original audio URL from the webhook
        audio_url = webhook_data.get("metadata", {}).get("url") or "unknown"

        # Create formatted response
        formatted_response = DeepgramBatchURLCompletedWebhookResponse(
            batch_id=batch_id,
            request_id=request_id,
            url_index=url_index,
            total_urls=total_urls,
            audio_url=audio_url,
            transcript=transcript,
            confidence=confidence,
            submitted_at=submitted_at,
            completed_at=datetime.utcnow().isoformat(),
        )

        # Convert to JSON for file output
        output_json = formatted_response.model_dump()

        # Generate filename based on request_id and url_index
        filename = f"{request_id}_url_{url_index}.json"

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
