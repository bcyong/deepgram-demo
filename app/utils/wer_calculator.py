from typing import NamedTuple
import jiwer


class WERResult(NamedTuple):
    """Result of Word Error Rate calculation"""

    wer_score: float
    substitutions: int
    deletions: int
    insertions: int
    reference_word_count: int
    hypothesis_word_count: int


def calculate_wer(reference: str, hypothesis: str) -> WERResult:
    """
    Calculate Word Error Rate (WER) between reference and hypothesis text.

    Args:
        reference: The reference/ground truth text
        hypothesis: The hypothesis/predicted text

    Returns:
        WERResult: Named tuple containing WER score and detailed metrics

    Raises:
        ValueError: If inputs are invalid
    """
    if not reference or not hypothesis:
        raise ValueError("Both reference and hypothesis must be non-empty strings")

    try:
        transforms = jiwer.Compose(
            [
                jiwer.ToLowerCase(),
                jiwer.RemoveEmptyStrings(),
                jiwer.RemoveMultipleSpaces(),
                jiwer.Strip(),
                jiwer.RemovePunctuation(),
                jiwer.ReduceToListOfListOfWords(),
            ]
        )

        # Calculate WER using jiwer library
        output = jiwer.process_words(
            reference,
            hypothesis,
            reference_transform=transforms,
            hypothesis_transform=transforms,
        )

        # Get word counts
        reference_words = len(reference.split())
        hypothesis_words = len(hypothesis.split())

        return WERResult(
            wer_score=output.wer,
            substitutions=output.substitutions,
            deletions=output.deletions,
            insertions=output.insertions,
            reference_word_count=reference_words,
            hypothesis_word_count=hypothesis_words,
        )

    except Exception as e:
        raise ValueError(f"Error calculating WER: {str(e)}")


def calculate_simple_wer(reference: str, hypothesis: str) -> float:
    """
    Calculate simple WER score without detailed metrics.

    Args:
        reference: The reference/ground truth text
        hypothesis: The hypothesis/predicted text

    Returns:
        float: WER score between 0 and 1
    """
    return calculate_wer(reference, hypothesis).wer_score
