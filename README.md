# Gymbro Science Detector

Paste a fitness video — we check **what they say** against peer-reviewed research and **how they move** against proper form.

Built for the Nebius x NVIDIA Global AI Hackathon on **Nebius Token Factory** with **NVIDIA Nemotron** models.

## How it works

```
YouTube URL ──► ingest (transcript + video)
                 │
   ┌─────────────┴──────────────┐
   ▼                            ▼
claims/  (Artem)             form/  (Tema)
 extract claims  [Nemotron]   MediaPipe keypoints
 retrieve: Europe PMC→Tavily  joint angles + rules
 verify + evidence level      reps, form issues
   └─────────────┬──────────────┘
                 ▼
     merge.py: cards by time + exercise_id,
     said-vs-shown mismatch (exercise catalog)
                 ▼
          api.py → VideoReport (JSON) → UI
```

Claim verdicts: `supported` · `overstated` · `not_supported` · `no_evidence` · `not_checkable`.

## Shared contract

- `gymbro/schema.py` — the single source of truth for data passed between parts. Change it only together.
- `exercise_id` = id from [free-exercise-db](https://github.com/yuhonas/free-exercise-db) (e.g. `Barbell_Squat`). Both parts use it.
- Gold labels for evaluation: `data/gold/claims_gold.csv` (Artem), `data/gold/form_gold.csv` (Tema).

## Who owns what

| Area | Owner | Files |
|---|---|---|
| Claim extraction, retrieval, verdicts, claim eval | Artem | `gymbro/claims/`, `eval/eval_claims.py` |
| Pose, angles, form rules, form eval | Tema | `gymbro/form/`, `eval/eval_form.py` |
| Schema, merge, API, ingest | together | `gymbro/schema.py`, `merge.py`, `api.py`, `ingest/` |

Search for `TODO(artem)` / `TODO(tema)` to find your next task.

## Quickstart

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env            # add NEBIUS_API_KEY (and TAVILY_API_KEY)
python scripts/fetch_exercises.py
python scripts/list_models.py   # pick Nemotron ids -> MODEL_FAST / MODEL_SMART in .env
pytest -q                       # offline tests

# claims only
python -m gymbro.claims.pipeline "https://www.youtube.com/shorts/<id>"
# form only
python -m gymbro.form.pipeline path/to/video.mp4 Barbell_Squat 0 20
# full API
uvicorn gymbro.api:app --reload   # POST /analyze {"url": "..."}
# evaluation
python -m eval.eval_claims
```

Run ingestion locally: YouTube often blocks cloud IPs.

## Evaluation

| | Accuracy |
|---|---|
| Claims: ours (retrieval + Nemotron verifier) | TODO |
| Claims: baseline (same LLM, no retrieval) | TODO |
| Form checks | TODO |

## How we use NVIDIA & Nebius

- **Nebius Token Factory** — all LLM calls (OpenAI-compatible API).
- **NVIDIA Nemotron** — fast model for claim extraction, larger model for evidence-based verdicts.
- TODO: anything else (Nebius AI Cloud GPU for video processing, etc.)

## License

Apache-2.0 — see [LICENSE](LICENSE).
