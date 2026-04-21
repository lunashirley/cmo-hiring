import os
from pathlib import Path

PIPELINE_DIR = Path(__file__).parent.parent
AGENTS_DIR = PIPELINE_DIR / "agents"
TEMPLATES_DIR = PIPELINE_DIR / "templates"
BRAND_VOICES_DIR = PIPELINE_DIR / "brand_voices"
OUTPUT_DIR = PIPELINE_DIR.parent / "output"

# Ensure output dir exists
OUTPUT_DIR.mkdir(exist_ok=True)

DEFAULT_SETTINGS = {
    "provider": "ollama",
    "ollama_endpoint": "http://localhost:11434",
    "model": "deepseek-r1:8b",
    "anthropic_api_key": "",
    "max_concurrency": "2",
    "per_call_timeout_s": "180",
    "run_timeout_s": "600",
    "atom_target_min": "8",
    "atom_target_max": "15",
    "qa_max_attempts": "3",
    "exemplar_pool_size": "5",
    "exemplars_injected": "3",
}


def get_pipeline_password() -> str:
    return os.getenv("PIPELINE_PASSWORD", "admin")
