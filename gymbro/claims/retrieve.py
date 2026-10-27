"""Step 2: find research for a claim.

Order: Europe PMC (covers PubMed, no key) -> Tavily fallback.
Responses are cached on disk so re-runs and evals don't burn API quota.
TODO(artem): curated core of key meta-analyses in pgvector, searched first.
"""
from __future__ import annotations

import hashlib
import json

import requests

from .. import config
from ..schema import Evidence, EvidenceLevel

EUROPEPMC_URL = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
_CACHE = config.CACHE_DIR / "retrieval"


def _cached(key: str, fn):
    _CACHE.mkdir(parents=True, exist_ok=True)
    f = _CACHE / (hashlib.sha1(key.encode()).hexdigest() + ".json")
    if f.exists():
        return json.loads(f.read_text())
    data = fn()
    f.write_text(json.dumps(data))
    return data


def _level(pub_types: list[str]) -> EvidenceLevel:
    t = " ".join(pub_types).lower()
    if "meta-analysis" in t:
        return EvidenceLevel.meta_analysis
    if "systematic review" in t:
        return EvidenceLevel.systematic_review
    if "randomized controlled trial" in t:
        return EvidenceLevel.rct
    if "observational" in t or "cohort" in t:
        return EvidenceLevel.observational
    return EvidenceLevel.other


def search_europepmc(query: str, n: int = 8) -> list[dict]:
    """Returns raw records with abstracts. `query` uses Europe PMC syntax."""
    def call():
        r = requests.get(EUROPEPMC_URL, params={
            "query": query, "format": "json", "resultType": "core", "pageSize": n,
        }, timeout=30)
        r.raise_for_status()
        return r.json().get("resultList", {}).get("result", [])
    return _cached(f"epmc:{n}:{query}", call)


def to_evidence(rec: dict) -> Evidence:
    types = (rec.get("pubTypeList") or {}).get("pubType", [])
    pmid = rec.get("pmid")
    return Evidence(
        source="europepmc", id=pmid or rec.get("doi"), title=rec.get("title", ""),
        year=int(rec["pubYear"]) if rec.get("pubYear") else None, level=_level(types),
        url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None,
    )


def search_tavily(query: str, n: int = 5) -> list[dict]:
    if not config.TAVILY_API_KEY:
        return []
    from tavily import TavilyClient

    def call():
        res = TavilyClient(api_key=config.TAVILY_API_KEY).search(
            query, search_depth="basic", max_results=n)
        return res.get("results", [])
    return _cached(f"tavily:{n}:{query}", call)


def build_query(claim_text: str) -> str:
    """TODO(artem): let MODEL_FAST rewrite the claim into keywords + MeSH-ish terms."""
    return f'({claim_text}) AND (PUB_TYPE:"meta-analysis" OR PUB_TYPE:"systematic-review" OR PUB_TYPE:"randomized-controlled-trial")'


def retrieve(claim_text: str, n: int = 8) -> list[tuple[Evidence, str]]:
    """Returns (evidence, abstract_or_snippet) pairs for the verifier."""
    out = [(to_evidence(r), r.get("abstractText", "")) for r in search_europepmc(build_query(claim_text), n)]
    if not out:
        out = [(Evidence(source="tavily", id=r["url"], title=r["title"], url=r["url"]), r.get("content", ""))
               for r in search_tavily(claim_text)]
    return out
