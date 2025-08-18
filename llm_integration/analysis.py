from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from sklearn.metrics.pairwise import cosine_similarity

from .config import Config
from .ollama_client import OllamaClient


SYSTEM_PROMPT = (
    "You are a precise, concise analyst. When asked to output structured data, return strictly valid JSON "
    "without any surrounding text or code fences. Do not add any extra commentary."
)

STANCE_TASK_INSTRUCTIONS = (
    "You will receive:\n- The ORIGINAL POST content (may be empty).\n- A single COMMENT.\n\n"
    "Task:\n1) STANCE: \"support\", \"oppose\", or \"neutral\" toward the post's main claim(s).\n"
    "2) INTENSITY: 1–5 (1 = calm/weak, 5 = very strong).\n"
    "3) REASONS: short phrase (≤ 12 words) explaining your judgement.\n\n"
    "Return exactly:\n{\"stance\":\"support|oppose|neutral\",\"intensity\":<1-5>,\"reasons\":\"short phrase\"}"
)

SUMMARY_TASK_INSTRUCTIONS = (
    "Given the ORIGINAL POST (may be empty) and a list of representative COMMENTS, produce a concise analysis.\n"
    "Return EXACTLY the following JSON object (no markdown, no code fences):\n"
    "{\n"
    "  \"executive_summary\": \"4–8 crisp sentences\",\n"
    "  \"key_points\": [\"bullet 1\", \"bullet 2\"],\n"
    "  \"next_steps\": [\"actionable 1\", \"actionable 2\"]\n"
    "}"
)


def embed_texts(client: OllamaClient, model: str, texts: List[str]) -> np.ndarray:
    if not texts:
        return np.zeros((0, 0), dtype=float)
    emb_list = client.embed(model=model, inputs=texts)
    return np.array(emb_list, dtype=float)


def novelty_scores(emb: np.ndarray, k: int = 10) -> np.ndarray:
    n = emb.shape[0]
    if n == 0:
        return np.array([], dtype=float)
    if n == 1:
        return np.array([0.0], dtype=float)
    sim = cosine_similarity(emb)
    np.fill_diagonal(sim, -np.inf)
    k_eff = min(k, max(1, n - 1))
    topk = np.sort(sim, axis=1)[:, -k_eff:]
    avg_sim = np.mean(topk, axis=1)
    novelty = 1.0 - avg_sim
    # min-max normalize
    min_v, max_v = float(np.min(novelty)), float(np.max(novelty))
    if max_v - min_v < 1e-9:
        return np.zeros(n, dtype=float)
    return (novelty - min_v) / (max_v - min_v)


def _extract_json_line(text: str) -> Dict[str, Any]:
    # Find the first {...} block
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return {"stance": "neutral", "intensity": 2, "reasons": "fallback"}
    import json

    try:
        return json.loads(text[start : end + 1])
    except Exception:
        return {"stance": "neutral", "intensity": 2, "reasons": "fallback"}


def classify_stance(client: OllamaClient, model: str, comment_text: str, original_post: str) -> Dict[str, Any]:
    user_prompt = (
        f"ORIGINAL POST:\n{original_post}\n\nCOMMENT:\n{comment_text}\n\n"
        f"{STANCE_TASK_INSTRUCTIONS}"
    )
    raw = client.chat(model=model, system=SYSTEM_PROMPT, user=user_prompt)
    parsed = _extract_json_line(raw)
    stance = parsed.get("stance", "neutral")
    intensity = int(parsed.get("intensity", 2))
    reasons = parsed.get("reasons", "fallback")
    if stance not in {"support", "oppose", "neutral"}:
        stance = "neutral"
    intensity = max(1, min(5, intensity))
    return {"stance": stance, "intensity": intensity, "reason": reasons}


def controversy_scores(stances: List[str], intensities: List[int]) -> np.ndarray:
    n = len(stances)
    if n == 0:
        return np.array([], dtype=float)

    # Polarization entropy over support/oppose only
    support_count = sum(1 for s in stances if s == "support")
    oppose_count = sum(1 for s in stances if s == "oppose")
    total = support_count + oppose_count
    if total == 0:
        entropy = 0.0
    else:
        p_support = support_count / total
        p_oppose = oppose_count / total
        # entropy base 2
        def h(p: float) -> float:
            return 0.0 if p <= 0.0 else -p * np.log2(p)

        entropy = h(p_support) + h(p_oppose)
        entropy = entropy / 1.0  # max entropy with 2 classes is 1 when p=0.5

    avg_intensity = float(np.mean([max(1, min(5, i)) for i in intensities])) / 5.0
    base = 0.5 * entropy + 0.5 * avg_intensity

    # Minority bonus per comment
    counts = {"support": support_count, "oppose": oppose_count, "neutral": len(stances) - total}
    bonus = []
    for s, i in zip(stances, intensities):
        p_stance = counts[s] / max(1, n)
        bonus.append((1 - p_stance) * (max(1, min(5, i)) / 5.0))
    bonus = np.array(bonus, dtype=float)
    per_comment = 0.5 * base + 0.5 * bonus
    # min-max normalize
    min_v, max_v = float(np.min(per_comment)), float(np.max(per_comment))
    if max_v - min_v < 1e-9:
        return np.zeros(n, dtype=float)
    return (per_comment - min_v) / (max_v - min_v)


def mmr(query_vec: np.ndarray, candidate_vecs: np.ndarray, lambda_param: float = 0.65, k: int = 12) -> List[int]:
    if candidate_vecs.shape[0] == 0:
        return []
    sim_to_query = cosine_similarity(candidate_vecs, query_vec.reshape(1, -1)).flatten()
    selected: List[int] = []
    remaining = set(range(candidate_vecs.shape[0]))
    while remaining and len(selected) < k:
        if not selected:
            next_idx = int(np.argmax(sim_to_query))
            selected.append(next_idx)
            remaining.remove(next_idx)
            continue
        selected_vecs = candidate_vecs[selected]
        sim_to_selected = cosine_similarity(candidate_vecs, selected_vecs)
        max_sim_selected = sim_to_selected.max(axis=1)
        mmr_scores = lambda_param * sim_to_query - (1 - lambda_param) * max_sim_selected
        # Avoid reselecting
        mmr_scores[list(selected)] = -np.inf
        next_idx = int(np.argmax(mmr_scores))
        if mmr_scores[next_idx] == -np.inf:
            break
        selected.append(next_idx)
        remaining.remove(next_idx)
    return selected


def _strip_code_fences(text: str) -> str:
    import re
    return re.sub(r"```[\s\S]*?```", "", text, flags=re.MULTILINE)


def _parse_summary_output(text: str) -> Dict[str, Any]:
    import json
    cleaned = _strip_code_fences(text).strip()
    parsed = _extract_json_line(cleaned)
    # Ensure keys exist and are correct types
    exec_summary = parsed.get("executive_summary") or ""
    key_points = parsed.get("key_points") or []
    next_steps = parsed.get("next_steps") or []
    if not isinstance(key_points, list):
        key_points = []
    if not isinstance(next_steps, list):
        next_steps = []
    return {
        "executive_summary": str(exec_summary).strip(),
        "key_points": [str(x).strip() for x in key_points if str(x).strip()],
        "next_steps": [str(x).strip() for x in next_steps if str(x).strip()],
    }


def generate_summary(client: OllamaClient, model: str, original_post: str, representative_comments: List[str]) -> Dict[str, Any]:
    comments_block = "\n".join(f"- {c}" for c in representative_comments)
    user_prompt = (
        f"ORIGINAL POST:\n{original_post}\n\nCOMMENTS:\n{comments_block}\n\n{SUMMARY_TASK_INSTRUCTIONS}"
    )
    content = client.chat(model=model, system=SYSTEM_PROMPT, user=user_prompt)
    print(f"User summary prompt: {user_prompt}")
    print(f"Summary content: {content}")
    try:
        return _parse_summary_output(content)
    except Exception:
        # Fallback: return entire content as summary
        return {"executive_summary": content.strip(), "key_points": [], "next_steps": []}


def score_and_rank(
    comments: List[Dict[str, Any]],
    novelty: np.ndarray,
    controversy: np.ndarray,
    weights: Sequence[float],
    topk: int,
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    df = pd.DataFrame(comments)
    # Popularity via upvotes if present
    if "upvotes" in df.columns:
        pop = df["upvotes"].fillna(0).astype(float).to_numpy()
        if pop.size > 0:
            min_v, max_v = float(np.min(pop)), float(np.max(pop))
            pop = np.zeros_like(pop) if max_v - min_v < 1e-9 else (pop - min_v) / (max_v - min_v)
    else:
        pop = np.zeros(len(df), dtype=float)

    df["novelty"] = novelty
    df["controversy"] = controversy
    df["popularity"] = pop

    w1, w2, w3 = (list(weights) + [0, 0, 0])[:3]
    df["must_read_score"] = w1 * df["novelty"] + w2 * df["controversy"] + w3 * df["popularity"]
    df_sorted = df.sort_values(by=["must_read_score"], ascending=False)
    top_df = df_sorted.head(topk).copy()
    return df_sorted, top_df


def analyze_comments(comments: List[Dict[str, Any]], original_post: Optional[str], cfg: Config) -> Dict[str, Any]:
    # Prepare client
    client = OllamaClient(cfg.ollama_host)

    texts = [c.get("text", "") for c in comments if c.get("text")]
    if not texts:
        return {
            "summary": {"executive_summary": "", "key_points": [], "next_steps": []},
            "top_comments": [],
            "all_comments": [],
            "config_used": {
                "ollama_host": cfg.ollama_host,
                "chat_model": cfg.chat_model,
                "embed_model": cfg.embed_model,
                "topk": cfg.topk,
                "max_summary_comments": cfg.max_summary_comments,
            },
        }

    # Embeddings
    emb = embed_texts(client, cfg.embed_model, texts)
    # Novelty
    novelty = novelty_scores(emb, k=min(cfg.topk, 10))

    # Classify stance
    stance_records: List[Dict[str, Any]] = []
    for c in comments:
        text = c.get("text")
        if not text:
            stance_records.append({"stance": "neutral", "intensity": 2, "reason": ""})
            continue
        res = classify_stance(client, cfg.chat_model, text, original_post or "")
        stance_records.append(res)

    stances = [r["stance"] for r in stance_records]
    intensities = [r["intensity"] for r in stance_records]
    controversy = controversy_scores(stances, intensities)

    # Representative selection for summary
    centroid = np.mean(emb, axis=0) if emb.size else np.zeros((emb.shape[1],), dtype=float)
    rep_idx = mmr(centroid, emb, k=min(cfg.max_summary_comments, len(texts)))
    representative_comments = [texts[i] for i in rep_idx]

    print(f"representative_comments: {representative_comments}")
    print(f"original_post: {original_post}")
    print(f"Generating summary...")
    # Summary
    summary_dict = generate_summary(client, cfg.chat_model, original_post or "", representative_comments)

    # Aggregate
    merged_comments: List[Dict[str, Any]] = []
    for c, s, nov, con in zip(comments, stance_records, novelty, controversy):
        item = {**c}
        item.update({
            "stance": s["stance"],
            "intensity": s["intensity"],
            "reason": s.get("reason", ""),
            "novelty": float(nov),
            "controversy": float(con),
        })
        merged_comments.append(item)

    weights = cfg.weights or (0.45, 0.45, 0.10)
    all_df, top_df = score_and_rank(merged_comments, novelty, controversy, weights, cfg.topk)

    def df_to_list(df: pd.DataFrame) -> List[Dict[str, Any]]:
        cols = [
            "id", "author", "text", "stance", "intensity", "reason",
            "novelty", "controversy", "popularity", "must_read_score",
        ]
        existing = [c for c in cols if c in df.columns]
        return df[existing].to_dict(orient="records")

    return {
        "summary": summary_dict,
        "top_comments": df_to_list(top_df),
        "all_comments": df_to_list(all_df),
        "config_used": {
            "ollama_host": cfg.ollama_host,
            "chat_model": cfg.chat_model,
            "embed_model": cfg.embed_model,
            "topk": cfg.topk,
            "max_summary_comments": cfg.max_summary_comments,
        },
    }


