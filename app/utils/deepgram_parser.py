from typing import Dict, List, Any
from loguru import logger

INTENT_CONFIDENCE_THRESHOLD = 0.1
SENTIMENT_EXTREME_THRESHOLD = 0.7
TOPIC_CONFIDENCE_THRESHOLD = 0.1
SEARCH_CONFIDENCE_THRESHOLD = 0.8


def format_timestamp(seconds: float) -> str:
    """
    Convert seconds to [hh:mm:ss] format.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted timestamp string
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)

    return f"[{hours:02d}:{minutes:02d}:{secs:02d}]"


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
        current_start_time = None

        for word in words:
            speaker = word.get("speaker", 0)
            word_text = word.get("word", "")
            start_time = word.get("start", 0)

            # If speaker changes, save current segment and start new one
            if current_speaker is not None and speaker != current_speaker:
                if current_segment:
                    speaker_text = " ".join(current_segment)
                    timestamp = format_timestamp(current_start_time)
                    diarized_lines.append(
                        f"Speaker {current_speaker} {timestamp}: {speaker_text}"
                    )
                current_segment = []
                current_start_time = start_time

            # Set start time for new speaker or first word
            if current_speaker is None:
                current_start_time = start_time

            current_speaker = speaker
            current_segment.append(word_text)

        # Don't forget the last segment
        if current_segment:
            speaker_text = " ".join(current_segment)
            timestamp = format_timestamp(current_start_time)
            diarized_lines.append(
                f"Speaker {current_speaker} {timestamp}: {speaker_text}"
            )

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
    if summarize == "v2" or summarize.lower() == "true":
        summary_dict = results_data.get("summary", None)
        logger.info(f"Summary dict: {summary_dict}")
        if summary_dict:
            if summary_dict.get("result", "") == "success":
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
    intents = set()
    intents_data = results_data.get("intents", {})
    if intents_data and "segments" in intents_data:
        for segment in intents_data["segments"]:
            if "intents" in segment:
                for intent_obj in segment["intents"]:
                    intent_name = intent_obj.get("intent")
                    confidence = intent_obj.get("confidence_score", 0.0)
                    logger.info(f"Intent: {intent_name} (confidence: {confidence})")
                    if intent_name and confidence > INTENT_CONFIDENCE_THRESHOLD:
                        intents.add(intent_name)

    return list(intents)


def extract_sentiment(results_data: Dict[str, Any]) -> tuple[str, float, list[float]]:
    """
    Extract sentiment from Deepgram results.

    Args:
        results_data: The results object from Deepgram webhook data

    Returns:
        Tuple of (sentiment as a string, sentiment score as a float between -1 and 1, list of extreme sentiment scores for each segment)
    """
    sentiment = ""
    sentiment_score = 0.0
    extreme_sentiment_scores = []
    sentiments_data = results_data.get("sentiments", {})
    average_sentiment = sentiments_data.get("average", {})

    if average_sentiment:
        sentiment = average_sentiment.get("sentiment", "")
        sentiment_score = average_sentiment.get("sentiment_score", 0.0)

    if sentiments_data and "segments" in sentiments_data:
        for segment in sentiments_data["segments"]:
            if "sentiment_score" in segment:
                if abs(segment["sentiment_score"]) > SENTIMENT_EXTREME_THRESHOLD:
                    extreme_sentiment_scores.append(segment["sentiment_score"])

    return sentiment, sentiment_score, extreme_sentiment_scores


def extract_topics(results_data: Dict[str, Any]) -> List[str]:
    """
    Extract topics from Deepgram results.

    Args:
        results_data: The results object from Deepgram webhook data

    Returns:
        List of topics as strings
    """
    topics = set()
    topics_data = results_data.get("topics", {})
    if topics_data and "segments" in topics_data:
        for segment in topics_data["segments"]:
            if "topics" in segment:
                for topic_obj in segment["topics"]:
                    topic_name = topic_obj.get("topic")
                    confidence = topic_obj.get("confidence_score", 0.0)
                    logger.info(f"Topic: {topic_name} (confidence: {confidence})")
                    if topic_name and confidence > TOPIC_CONFIDENCE_THRESHOLD:
                        topics.add(topic_name)

    return list(topics)


def extract_search_hits(results_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract search term hits from Deepgram results.

    Args:
        results_data: The results object from Deepgram webhook data

    Returns:
        List of dicts with 'channel', 'term', 'snippet', and 'start' for each search hit above confidence threshold
    """
    search_hits = []
    channels = results_data.get("channels", [])
    for channel_idx, channel in enumerate(channels):
        search_results = channel.get("search", [])
        for search_obj in search_results:
            term = search_obj.get("query", "")
            hits = search_obj.get("hits", [])
            for hit in hits:
                confidence = hit.get("confidence", 0.0)
                if confidence >= SEARCH_CONFIDENCE_THRESHOLD:
                    snippet = hit.get("snippet", "")
                    start = hit.get("start", 0.0)
                    search_hits.append(
                        {
                            "channel": channel_idx,
                            "term": term,
                            "snippet": snippet,
                            "start": start,
                        }
                    )
                    # Only record the first hit above threshold for each term per channel
                    break
    return search_hits


def build_filename(
    use_url_as_filename: bool,
    filename_prefix: str,
    storage_bucket_name: str,
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

    if storage_bucket_name != "":
        logger.warning(
            "Storage bucket name is not empty. This is not supported yet. Defaulting to 'yonger-deepgram-demo'"
        )

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
