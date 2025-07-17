from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from ..utils.wer_calculator import calculate_wer

router = APIRouter(prefix='/api/v1/audit')

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

@router.post("/text", response_model=AuditTextResponse, tags=["audit-text"])
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

@router.post("/audio", response_model=AuditAudioResponse, tags=["audit-audio"])
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
        transcription_result = deepgram_client.transcribe_audio(request.hypothesis_url)
        
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