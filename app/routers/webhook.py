from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Dict, Any, Optional
import json
from datetime import datetime
from loguru import logger

router = APIRouter(prefix="/api/v1/webhook")


class DeepgramWebhookResponse(BaseModel):
    """Formatted response for file output"""

    batch_id: str
    request_id: str
    url_index: int
    total_urls: int
    audio_url: str
    transcript: str
    confidence: float
    storage_location: str
    submitted_at: str
    completed_at: str
    user_callback_url: Optional[str] = None
    extra: Dict[str, Any]


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
        metadata = webhook_data.get("metadata", {})
        request_id = metadata.get("request_id")
        extra_data = metadata.get("extra", {})
        
        # Handle extra data which could be a list of strings, dict, or malformed
        extra = {}
        if isinstance(extra_data, list):
            # Reconstruct dictionary from list of "key=value" strings
            for item in extra_data:
                if isinstance(item, str) and "=" in item:
                    key, value = item.split("=", 1)
                    extra[key] = value
        elif isinstance(extra_data, dict):
            extra = extra_data
        elif isinstance(extra_data, str):
            try:
                extra = json.loads(extra_data)
            except json.JSONDecodeError:
                logger.error(f"Failed to parse extra data JSON string: {extra_data}")
                extra = {}
        else:
            logger.warning(f"Unexpected extra data type: {type(extra_data)}, value: {extra_data}")
            extra = {}
            
        batch_id = extra.get("batch_id") or "unknown"
        url_index = extra.get("url_index", 0)
        total_urls = extra.get("total_urls", 1)
        storage_location = extra.get("storage_location") or "unknown"
        submitted_at = extra.get("submitted_at") or "unknown"
        user_callback_url = extra.get("user_callback_url")

        logger.info(f"Extra data: {extra}")

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
            batch_id=batch_id,
            request_id=request_id,
            url_index=url_index,
            total_urls=total_urls,
            audio_url=audio_url,
            transcript=transcript,
            confidence=confidence,
            storage_location=storage_location,
            submitted_at=submitted_at,
            completed_at=datetime.utcnow().isoformat(),
            user_callback_url=user_callback_url,
            extra=extra,
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
