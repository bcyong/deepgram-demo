from typing import Dict, List, Any
from loguru import logger


def build_transcript(
    results: Dict[str, Any], diarize: bool = False
) -> tuple[str, float]:
    """
    Build transcript from Deepgram results.

    Args:
        results: The results object from Deepgram webhook data
        diarize: Whether to build a diarized transcript

    Returns:
        Tuple of (transcript string, confidence float)
    """
    channels = results.get("channels", [])

    if not channels:
        raise ValueError("No channels found in webhook data")

    channel = channels[0]
    alternatives = channel.get("alternatives", [])

    if not alternatives:
        raise ValueError("No transcription alternatives found")

    alternative = alternatives[0]

    # Extract confidence
    confidence = alternative.get("confidence", 0.0)

    if diarize:
        logger.info("Building diarized transcript")
        # Build diarized transcript from words array
        words = alternative.get("words", [])
        if not words:
            logger.warning(
                "No words found for diarization, falling back to regular transcript"
            )
            return alternative.get("transcript", ""), confidence

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
        return transcript, confidence
    else:
        logger.info("Building non-diarized transcript")
        return alternative.get("transcript", ""), confidence


def extract_summary(results_data: Dict[str, Any], summarize: str) -> str:
    """
    Extract summary from Deepgram results.

    Args:
        results_data: The results object from Deepgram webhook data
        summarize: The summarize parameter (e.g., "v2")

    Returns:
        Summary as a string, or empty string if not found
    """
    summary = ""
    if summarize == "v2":
        summary_dict = results_data.get("summary", None)
        if summary_dict:
            if summary_dict.get("success", False):
                summary = summary_dict.get("short", "")

    return summary


def extract_intents(results_data: Dict[str, Any]) -> List[str]:
    """
    Extract intent names from Deepgram results.

    Args:
        results_data: The results object from Deepgram webhook data

    Returns:
        List of intent names as strings
    """
    intents = []
    intents_data = results_data.get("intents", {})

    if intents_data and "segments" in intents_data:
        for segment in intents_data["segments"]:
            if "intents" in segment:
                for intent_obj in segment["intents"]:
                    intent_name = intent_obj.get("intent")
                    if intent_name:
                        intents.append(intent_name)

    return intents


def build_filename(
    use_url_as_filename: bool,
    filename_prefix: str,
    storage_folder_name: str,
    audio_url: str,
    batch_id: str,
    url_index: int,
) -> str:
    """
    Build filename for the transcription output.

    Args:
        use_url_as_filename: Whether to use the audio URL as filename
        filename_prefix: Prefix for the filename
        storage_folder_name: Folder name for storage
        audio_url: The audio URL
        batch_id: The batch ID
        url_index: The URL index within the batch

    Returns:
        Filename as a string
    """
    if use_url_as_filename:
        filename = f"{audio_url.split('/')[-1]}.json"
    elif filename_prefix:
        filename = f"{filename_prefix}_{url_index}.json"
    else:
        filename = f"{batch_id}_url_{url_index}.json"

    if storage_folder_name:
        filename = storage_folder_name + "/" + filename
    else:
        filename = batch_id + "/" + filename

    return filename
