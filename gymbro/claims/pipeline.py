"""Claims part (owner: Artem): transcript -> list[ClaimResult]."""
from __future__ import annotations

from ..schema import ClaimResult, ClaimVerdict, TranscriptSegment
from .extract import extract_claims
from .retrieve import retrieve
from .verify import verify


def run_claims(transcript: list[TranscriptSegment]) -> list[ClaimResult]:
    results = []
    for claim in extract_claims(transcript):
        try:
            results.append(verify(claim, retrieve(claim.text)))
        except Exception as e:  # never let one claim kill the whole report
            results.append(ClaimResult(claim=claim, verdict=ClaimVerdict.no_evidence,
                                       confidence=0.0, explanation=f"Check failed: {e}"))
    return results


if __name__ == "__main__":
    import sys

    from ..ingest.youtube import load

    video = load(sys.argv[1], with_video=False)
    for r in run_claims(video.transcript):
        print(f"[{r.claim.t_start:6.1f}s] {r.verdict.value:14} {r.claim.text}")
        print(f"          {r.explanation}")
