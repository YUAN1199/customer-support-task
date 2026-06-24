"""Central configuration for the Agentic Reasoning Lab."""

import os
from dataclasses import dataclass, field

# --- API / Model config ---
SOLVER_MODEL = os.getenv("SOLVER_MODEL", "openai/gpt-4o-mini")
JUDGE_MODEL = os.getenv("JUDGE_MODEL", "openai/gpt-4o")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")

# --- Strategy defaults ---
REACT_MAX_STEPS = int(os.getenv("REACT_MAX_STEPS", "8"))
SELF_CONSISTENCY_N = int(os.getenv("SELF_CONSISTENCY_N", "5"))
TOT_BEAM_WIDTH = int(os.getenv("TOT_BEAM_WIDTH", "2"))
TOT_MAX_DEPTH = int(os.getenv("TOT_MAX_DEPTH", "3"))

# --- Eval ---
GOLDEN_SET_PATH = os.getenv("GOLDEN_SET_PATH", "data/golden_set.jsonl")
TRACES_DIR = os.getenv("TRACES_DIR", "data/traces")
BASELINE_PATH = os.getenv("BASELINE_PATH", "data/baselines/baseline.json")

# --- Tracing ---
TRACING_ENABLED = os.getenv("TRACING_ENABLED", "1") == "1"

# --- Cost (per 1M tokens, input / output) ---
# GPT-4o-mini pricing (OpenRouter approximate)
COST_PER_1M_INPUT = float(os.getenv("COST_PER_1M_INPUT", "0.15"))
COST_PER_1M_OUTPUT = float(os.getenv("COST_PER_1M_OUTPUT", "0.60"))


@dataclass
class SystemConfig:
    solver_model: str = SOLVER_MODEL
    judge_model: str = JUDGE_MODEL
    openrouter_api_key: str = OPENROUTER_API_KEY
    openrouter_base_url: str = OPENROUTER_BASE_URL
    openai_api_key: str = OPENAI_API_KEY
    openai_base_url: str = OPENAI_BASE_URL

    react_max_steps: int = REACT_MAX_STEPS
    self_consistency_n: int = SELF_CONSISTENCY_N
    tot_beam_width: int = TOT_BEAM_WIDTH
    tot_max_depth: int = TOT_MAX_DEPTH

    golden_set_path: str = GOLDEN_SET_PATH
    traces_dir: str = TRACES_DIR
    baseline_path: str = BASELINE_PATH
    tracing_enabled: bool = TRACING_ENABLED

    cost_per_1m_input: float = COST_PER_1M_INPUT
    cost_per_1m_output: float = COST_PER_1M_OUTPUT


CONFIG = SystemConfig()