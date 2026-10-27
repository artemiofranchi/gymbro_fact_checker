"""Evaluate claim verdicts against data/gold/claims_gold.csv.

Compares the full pipeline (retrieval + verifier) with a no-retrieval baseline
(the same LLM answering from its own knowledge). This table goes into the README.

python -m eval.eval_claims [--limit N]
"""
from __future__ import annotations

import argparse
import csv
from collections import Counter
from pathlib import Path

from gymbro import config, llm
from gymbro.claims.retrieve import retrieve
from gymbro.claims.verify import verify
from gymbro.schema import Claim

GOLD = Path(__file__).resolve().parent.parent / "data" / "gold" / "claims_gold.csv"

BASELINE_PROMPT = """Is this fitness claim scientifically accurate?
Claim: "{claim}"
Answer with one of: supported, overstated, not_supported, no_evidence.
Return JSON: {{"verdict": "..."}}"""


def baseline(text: str) -> str:
    return llm.chat_json(BASELINE_PROMPT.format(claim=text), model=config.MODEL_SMART).get("verdict", "no_evidence")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int)
    args = ap.parse_args()

    rows = [r for r in csv.DictReader(GOLD.open()) if r.get("claim_text") and r.get("claim_verdict")]
    rows = rows[: args.limit] if args.limit else rows
    hits = Counter()
    for r in rows:
        claim = Claim(text=r["claim_text"], quote=r["claim_text"], t_start=0, t_end=0)
        ours = verify(claim, retrieve(claim.text)).verdict.value
        base = baseline(claim.text)
        hits["ours"] += ours == r["claim_verdict"]
        hits["baseline"] += base == r["claim_verdict"]
        print(f"gold={r['claim_verdict']:14} ours={ours:14} base={base:14} | {claim.text}")
    n = len(rows) or 1
    print(f"\nAccuracy on {len(rows)} claims: ours={hits['ours']/n:.0%}  baseline={hits['baseline']/n:.0%}")


if __name__ == "__main__":
    main()
