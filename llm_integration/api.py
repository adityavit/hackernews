from __future__ import annotations

import os
from typing import List, Optional, Sequence

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .analysis import analyze_comments
from .config import Config, env_config, override_config


class Comment(BaseModel):
    id: Optional[str] = None
    author: Optional[str] = None
    text: str
    age: Optional[str] = None
    timestamp: Optional[str] = None
    depth: Optional[int] = None
    parent_id: Optional[str] = None
    upvotes: Optional[float] = None


class AnalyzeRequest(BaseModel):
    comments: List[Comment] = Field(default_factory=list)
    original_post: Optional[str] = None
    ollama_host: Optional[str] = None
    chat_model: Optional[str] = None
    embed_model: Optional[str] = None
    topk: Optional[int] = None
    max_summary_comments: Optional[int] = None
    weights: Optional[Sequence[float]] = None


app = FastAPI(title="Local Comment Analysis Service")

# CORS allow-list via env var (comma-separated origins)
allow_origins = os.getenv("LLM_CORS_ALLOW_ORIGINS", "").split(",") if os.getenv("LLM_CORS_ALLOW_ORIGINS") else []
if allow_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in allow_origins if o.strip()],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/analyze")
def analyze(req: AnalyzeRequest):
    base_cfg = env_config()
    cfg = override_config(
        base_cfg,
        ollama_host=req.ollama_host,
        chat_model=req.chat_model,
        embed_model=req.embed_model,
        topk=req.topk,
        max_summary_comments=req.max_summary_comments,
        weights=req.weights,
    )
    result = analyze_comments([c.model_dump() for c in req.comments], req.original_post, cfg)
    return result


def main():
    import uvicorn

    uvicorn.run("llm_integration.api:app", host="0.0.0.0", port=8080, reload=False)


if __name__ == "__main__":
    main()


