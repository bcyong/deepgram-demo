from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
from datetime import datetime
from loguru import logger

router = APIRouter(prefix="/api/v1/webhook")


class DeepgramWebhookResponse(BaseModel):
    """Formatted response for file output"""

    request_id: str
    url_index: int
    total_urls: int
    audio_url: str
    transcript: str
    confidence: float
    storage_location: str
    language: str
    model: str
    submitted_at: str
    completed_at: str
    user_callback_url: Optional[str] = None
    metadata: Dict[str, Any]


@router.post("/deepgram", tags=["webhook"])
async def deepgram_webhook(request: Request):
    """
    Webhook endpoint for receiving Deepgram transcription results.

    This endpoint receives the callback from Deepgram when transcription is complete,
    formats the response, and prepares it for file output.
    """
    try:
        # Parse the incoming webhook payload
        webhook_data = await request.json()

        logger.info(f"Webhook data: {webhook_data}")

        # Extract extra data from the webhook
        extra = webhook_data.get("extra", {})
        request_id = metadata.get("request_id")
        url_index = metadata.get("url_index", 0)
        total_urls = metadata.get("total_urls", 1)
        storage_location = metadata.get("storage_location")
        language = metadata.get("language", "en-US")
        model = metadata.get("model", "nova-3")
        submitted_at = metadata.get("submitted_at")
        user_callback_url = metadata.get("user_callback_url")

        logger.info(f"Extra data: {extra}")

        logger.info(f"Extracted metadata: request_id={request_id}, url_index={url_index}")

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

        logger.info(f"Extracted transcript: {transcript[:50]}... (confidence: {confidence})")

        # Get the original audio URL from the webhook
        audio_url = webhook_data.get("metadata", {}).get("url") or "unknown"

        # Create formatted response
        formatted_response = DeepgramWebhookResponse(
            request_id=request_id,
            url_index=url_index,
            total_urls=total_urls,
            audio_url=audio_url,
            transcript=transcript,
            confidence=confidence,
            storage_location=storage_location,
            language=language,
            model=model,
            submitted_at=submitted_at,
            completed_at=datetime.utcnow().isoformat(),
            user_callback_url=user_callback_url,
            metadata=metadata,
        )

        # Convert to JSON for file output
        output_json = formatted_response.model_dump()

        # Generate filename based on request_id and url_index
        filename = f"{request_id}_url_{url_index}.json"

        logger.info(f"Successfully processed webhook for request_id={request_id}, filename={filename}")

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
