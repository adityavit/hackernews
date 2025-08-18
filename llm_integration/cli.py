from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Optional

import typer

from .analysis import analyze_comments
from .config import Config, env_config, override_config


app = typer.Typer(name="comments-analyze", no_args_is_help=True)


def _read_json_array(path: Optional[Path]) -> list:
    data = sys.stdin.read() if (path is None or str(path) == "-") else Path(path).read_text(encoding="utf-8")
    arr = json.loads(data)
    if not isinstance(arr, list):
        raise typer.BadParameter("Input must be a JSON array of comment objects")
    return arr


def _read_optional_text(path: Optional[Path]) -> Optional[str]:
    if path is None:
        return None
    if str(path) == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8")


@app.command("analyze")
def analyze(
    input: Optional[Path] = typer.Option(None, "--input", "-i", help="Path to JSON array file, or - for stdin"),
    original_post: Optional[Path] = typer.Option(None, "--original-post", help="Optional path to original post text"),
    ollama_host: Optional[str] = typer.Option(None, "--ollama-host", help="Ollama host, e.g. http://localhost:11434"),
    chat_model: Optional[str] = typer.Option(None, "--chat-model", help="Chat model name"),
    embed_model: Optional[str] = typer.Option(None, "--embed-model", help="Embedding model name"),
    topk: Optional[int] = typer.Option(None, "--topk", help="Top-K comments to rank"),
    max_summary_comments: Optional[int] = typer.Option(None, "--max-summary-comments", help="Max comments for summary selection"),
    weights: Optional[str] = typer.Option(None, "--weights", help="Comma-separated weights: novelty,controversy,popularity"),
    out_json: Optional[Path] = typer.Option(None, "--out-json", help="Write final JSON to file"),
    out_csv: Optional[Path] = typer.Option(None, "--out-csv", help="Write CSV of all comments"),
    out_md: Optional[Path] = typer.Option(None, "--out-md", help="Write Markdown summary/results"),
):
    comments = _read_json_array(input)
    post_text = _read_optional_text(original_post)

    base_cfg = env_config()
    weight_tuple = None
    if weights:
        try:
            parts = [float(x.strip()) for x in weights.split(",")]
            weight_tuple = (parts + [0.0, 0.0, 0.0])[:3]
        except Exception as exc:  # noqa: BLE001
            raise typer.BadParameter(f"Invalid weights: {weights}") from exc

    cfg = override_config(
        base_cfg,
        ollama_host=ollama_host,
        chat_model=chat_model,
        embed_model=embed_model,
        topk=topk,
        max_summary_comments=max_summary_comments,
        weights=weight_tuple,
    )

    result = analyze_comments(comments, post_text, cfg)

    text = json.dumps(result, indent=2, ensure_ascii=False)
    if out_json:
        Path(out_json).write_text(text, encoding="utf-8")
    else:
        typer.echo(text)

    # Optional outputs
    import pandas as pd  # local import to avoid hard dependency for JSON path

    if out_csv:
        try:
            all_comments = result.get("all_comments", [])
            pd.DataFrame(all_comments).to_csv(out_csv, index=False)
        except Exception:
            pass

    if out_md:
        try:
            summary = result.get("summary", {})
            top_comments = result.get("top_comments", [])
            lines = [
                "# Comment Analysis Results",
                "",
                "## Executive Summary",
                summary.get("executive_summary", ""),
                "",
                "## Top Comments",
            ]
            for c in top_comments:
                lines.append(f"- [{c.get('id','')}] {c.get('author','')} | stance={c.get('stance','')} | score={c.get('must_read_score',0):.3f}")
            Path(out_md).write_text("\n".join(lines), encoding="utf-8")
        except Exception:
            pass


def main():
    app()


if __name__ == "__main__":
    main()


