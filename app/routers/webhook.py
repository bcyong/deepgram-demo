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

        # Extract metadata from the webhook
        metadata = webhook_data.get("metadata", {})
        request_id = metadata.get("request_id")
        url_index = metadata.get("url_index", 0)
        total_urls = metadata.get("total_urls", 1)
        storage_location = metadata.get("storage_location")
        language = metadata.get("language", "en-US")
        model = metadata.get("model", "nova-3")
        submitted_at = metadata.get("submitted_at")
        user_callback_url = metadata.get("user_callback_url")

        # Extract transcription results
        results = webhook_data.get("results", {})
        channels = results.get("channels", [])

        if not channels:
            raise HTTPException(
                status_code=400, detail="No transcription results found"
            )

        channel = channels[0]
        alternatives = channel.get("alternatives", [])

        if not alternatives:
            raise HTTPException(
                status_code=400, detail="No transcription alternatives found"
            )

        alternative = alternatives[0]
        transcript = alternative.get("transcript", "")
        confidence = alternative.get("confidence", 0.0)

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

        # # Create output directory if it doesn't exist
        # output_dir = "transcription_outputs"
        # os.makedirs(output_dir, exist_ok=True)

        # # Write to file
        # output_path = os.path.join(output_dir, filename)
        # with open(output_path, 'w', encoding='utf-8') as f:
        #     json.dump(output_json, f, indent=2, ensure_ascii=False)

        # # TODO: In production, save to the specified storage_location
        # # For now, we're saving locally

        # # Call user callback if provided
        # if user_callback_url:
        #     try:
        #         # TODO: Implement async HTTP call to user callback
        #         # This would typically use httpx or aiohttp
        #         print(f"Would call user callback: {user_callback_url}")
        #         print(f"With data: {json.dumps(output_json, indent=2)}")
        #     except Exception as e:
        #         print(f"Error calling user callback: {str(e)}")

        return {
            "status": "success",
            "message": f"Transcription result saved to {filename}",
            "request_id": request_id,
            "url_index": url_index,
            "filename": filename,
        }

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Webhook processing failed: {str(e)}"
        )
