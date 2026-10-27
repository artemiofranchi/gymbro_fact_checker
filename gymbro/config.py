"""Settings from environment / .env. See .env.example."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:  # python-dotenv is optional
    pass

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CACHE_DIR = ROOT / ".cache"

# Nebius Token Factory (OpenAI-compatible)
TF_BASE_URL = os.getenv("TF_BASE_URL", "https://api.tokenfactory.nebius.com/v1/")
TF_API_KEY = os.getenv("NEBIUS_API_KEY", "")
# Exact model ids: run `python scripts/list_models.py` and put them into .env
MODEL_FAST = os.getenv("MODEL_FAST", "nvidia/NVIDIA-Nemotron-Nano-9B-v2")     # extraction, routing
MODEL_SMART = os.getenv("MODEL_SMART", "nvidia/Llama-3_3-Nemotron-Super-49B-v1_5")  # verdicts

TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")
NCBI_API_KEY = os.getenv("NCBI_API_KEY", "")

EXERCISES_PATH = DATA_DIR / "exercises" / "exercises.json"
