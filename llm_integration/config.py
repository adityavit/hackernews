from __future__ import annotations

from dataclasses import dataclass
import os
from typing import Optional, Sequence


OLLAMA_HOST_DEFAULT = "http://192.168.0.226:11434"
CHAT_MODEL_DEFAULT = "llama3.2:latest"
EMBED_MODEL_DEFAULT = "nomic-embed-text"
TOPK_DEFAULT = 10
MAX_SUMMARY_COMMENTS_DEFAULT = 40


@dataclass
class Config:
    ollama_host: str = OLLAMA_HOST_DEFAULT
    chat_model: str = CHAT_MODEL_DEFAULT
    embed_model: str = EMBED_MODEL_DEFAULT
    topk: int = TOPK_DEFAULT
    max_summary_comments: int = MAX_SUMMARY_COMMENTS_DEFAULT
    weights: Optional[Sequence[float]] = None  # novelty, controversy, popularity


def env_config() -> Config:
    return Config(
        ollama_host=os.getenv("OLLAMA_HOST", OLLAMA_HOST_DEFAULT),
        chat_model=os.getenv("CHAT_MODEL", CHAT_MODEL_DEFAULT),
        embed_model=os.getenv("EMBED_MODEL", EMBED_MODEL_DEFAULT),
        topk=int(os.getenv("TOPK", TOPK_DEFAULT)),
        max_summary_comments=int(os.getenv("MAX_SUMMARY_COMMENTS", MAX_SUMMARY_COMMENTS_DEFAULT)),
    )


def override_config(base: Config, **overrides) -> Config:
    data = base.__dict__.copy()
    for key, value in overrides.items():
        if value is not None:
            data[key] = value
    return Config(**data)


