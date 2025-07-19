from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from ..utils.wer_calculator import calculate_wer
import tempfile
import os

router = APIRouter(prefix="/api/v1/audit")


class AuditTextRequest(BaseModel):
    reference: str
    hypothesis: str


class AuditAudioRequest(BaseModel):
    reference: str
    hypothesis_url: str


class AuditTextResponse(BaseModel):
    reference: str
    hypothesis: str
    reference_word_count: int
    hypothesis_word_count: int
    wer: float
    substitutions: int
    deletions: int
    insertions: int


class AuditAudioResponse(BaseModel):
    reference: str
    hypothesis_url: str
    hypothesis_transcript: str
    reference_word_count: int
    hypothesis_word_count: int
    wer: float
    substitutions: int
    deletions: int
    insertions: int


@router.post("/text", response_model=AuditTextResponse, tags=["audit"])
async def audit_text(request: AuditTextRequest):
    """
    Calculate Word Error Rate (WER) between reference and hypothesis text.

    WER = (Substitutions + Deletions + Insertions) / Number of words in reference
    """
    try:
        # Use the reusable WER calculation utility
        wer_result = calculate_wer(request.reference, request.hypothesis)

        return AuditTextResponse(
            reference=request.reference,
            hypothesis=request.hypothesis,
            reference_word_count=wer_result.reference_word_count,
            hypothesis_word_count=wer_result.hypothesis_word_count,
            wer=wer_result.wer_score,
            substitutions=wer_result.substitutions,
            deletions=wer_result.deletions,
            insertions=wer_result.insertions,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/audio-url", response_model=AuditAudioResponse, tags=["audit"])
async def audit_audio(request: AuditAudioRequest):
    """
    Calculate Word Error Rate (WER) between reference and hypothesis audio.

    WER = (Substitutions + Deletions + Insertions) / Number of words in reference
    """
    try:
        # Import Deepgram client
        from ..utils.deepgram_client import create_deepgram_client

        # Create Deepgram client and transcribe the hypothesis audio
        deepgram_client = create_deepgram_client()
        transcription_result = deepgram_client.transcribe_audio_url(
            request.hypothesis_url
        )

        # Get the transcript from Deepgram
        hypothesis_transcript = transcription_result["transcript"]

        # Calculate WER between reference and transcribed hypothesis
        wer_result = calculate_wer(request.reference, hypothesis_transcript)

        return AuditAudioResponse(
            reference=request.reference,
            hypothesis_url=request.hypothesis_url,
            hypothesis_transcript=hypothesis_transcript,
            reference_word_count=wer_result.reference_word_count,
            hypothesis_word_count=wer_result.hypothesis_word_count,
            wer=wer_result.wer_score,
            substitutions=wer_result.substitutions,
            deletions=wer_result.deletions,
            insertions=wer_result.insertions,
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@router.post("/audio-file", response_model=AuditAudioResponse, tags=["audit"])
async def audit_audio_file(reference: str, audio_file: UploadFile = File(...)):
    """
    Calculate Word Error Rate (WER) between reference text and uploaded audio file.

    WER = (Substitutions + Deletions + Insertions) / Number of words in reference
    """
    try:
        # Import Deepgram client
        from ..utils.deepgram_client import create_deepgram_client

        # Validate file type
        if not audio_file.content_type or not audio_file.content_type.startswith(
            "audio/"
        ):
            raise HTTPException(status_code=400, detail="File must be an audio file")

        # Create temporary file to store the uploaded audio
        filename = audio_file.filename or "audio"
        file_extension = filename.split(".")[-1] if "." in filename else "wav"
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=f".{file_extension}"
        ) as temp_file:
            # Write uploaded file content to temporary file
            content = await audio_file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name

        try:
            # Create Deepgram client and transcribe the uploaded audio file
            deepgram_client = create_deepgram_client()
            transcription_result = deepgram_client.transcribe_audio_file(temp_file_path)

            # Get the transcript from Deepgram
            hypothesis_transcript = transcription_result["transcript"]

            # Calculate WER between reference and transcribed hypothesis
            wer_result = calculate_wer(reference, hypothesis_transcript)

            return AuditAudioResponse(
                reference=reference,
                hypothesis_url="",
                hypothesis_transcript=hypothesis_transcript,
                reference_word_count=wer_result.reference_word_count,
                hypothesis_word_count=wer_result.hypothesis_word_count,
                wer=wer_result.wer_score,
                substitutions=wer_result.substitutions,
                deletions=wer_result.deletions,
                insertions=wer_result.insertions,
            )

        finally:
            # Clean up temporary file
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
