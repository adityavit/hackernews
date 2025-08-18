from __future__ import annotations

import json
from typing import Dict, List, Any, Optional

import requests


class OllamaClient:
    def __init__(self, host: str) -> None:
        self.host = host.rstrip("/")

    def embed(self, model: str, inputs: List[str], timeout: int = 30, retries: int = 2) -> List[List[float]]:
        url = f"{self.host}/api/embed"
        payload = {"model": model, "input": inputs}
        last_err: Optional[Exception] = None
        for _ in range(retries + 1):
            try:
                resp = requests.post(url, json=payload, timeout=timeout)
                resp.raise_for_status()
                data = resp.json()
                return data.get("embeddings", [])
            except Exception as exc:  # noqa: BLE001
                last_err = exc
        raise RuntimeError(f"Ollama embed failed: {last_err}")

    def chat(self, model: str, system: str, user: str, timeout: int = 60, retries: int = 2) -> str:
        url = f"{self.host}/api/chat"
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "stream": False,
        }
        headers = {"Content-Type": "application/json"}
        last_err: Optional[Exception] = None
        for _ in range(retries + 1):
            try:
                resp = requests.post(url, headers=headers, data=json.dumps(payload), timeout=timeout)
                resp.raise_for_status()
                data = resp.json()
                # Expect {'message': {'content': '...'}}
                message = data.get("message", {}).get("content", "")
                if not message:
                    # Some backends return choices
                    choices = data.get("choices")
                    if choices:
                        message = choices[0].get("message", {}).get("content", "")
                return message
            except Exception as exc:  # noqa: BLE001
                last_err = exc
        raise RuntimeError(f"Ollama chat failed: {last_err}")


