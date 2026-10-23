#!/usr/bin/env python3
"""Send a reviewed text question to DeepSeek's Chat Completions API."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"{path} is not valid UTF-8 text") from exc


def slugify(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-._")
    return (slug or "consultation")[:60]


def build_prompt(question: str, attachments: list[Path], max_chars: int) -> tuple[str, list[dict[str, object]]]:
    parts = [question.strip()]
    manifest: list[dict[str, object]] = []
    for path in attachments:
        content = read_text(path)
        truncated = len(content) > max_chars
        if truncated:
            content = content[:max_chars] + "\n\n[Attachment truncated by the client.]"
        parts.append(f"\n\n--- BEGIN ATTACHMENT: {path.name} ---\n{content}\n--- END ATTACHMENT: {path.name} ---")
        manifest.append({"name": path.name, "characters_sent": len(content), "truncated": truncated})
    return "".join(parts), manifest


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--question-file", type=Path, help="UTF-8 file containing the question")
    source.add_argument("--question", help="Question text (avoid shell history for sensitive text)")
    parser.add_argument("--attach", action="append", default=[], type=Path, help="UTF-8 text attachment; may be repeated")
    parser.add_argument("--model", required=True, help="Current DeepSeek API model ID")
    parser.add_argument("--title", default="DeepSeek consultation", help="Short label for local output files")
    parser.add_argument(
        "--base-url",
        default=os.environ.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com"),
        help="API root, without /chat/completions",
    )
    parser.add_argument("--thinking", choices=("enabled", "disabled"), help="Optional thinking-mode setting")
    parser.add_argument("--reasoning-effort", help="Optional model-supported reasoning effort")
    parser.add_argument("--max-attachment-chars", type=int, default=200_000, help="Maximum characters read from each attachmment")
    parser.add_argument("--timeout", type=int, default=180, help="Request timeout in seconds")
    parser.add_argument("--output-dir", type=Path, help="Output directory; defaults to results/<timestamp>_<title>")
    parser.add_argument("--dry-run", action="store_true", help="Print the exact request JSON without calling the API")
    return parser.parse_args()


def main() -> int:
    if hasattr(ys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    args = parse_args()
    if args.max_attachment_chars < 1:
        print("Error: --max-attachment-chars must be positive", file=sys.stderr)
        return 2
    if args.timeout < 1:
        print("Error: --timeout must be positive", file=sys.stderr)
        return 2

    try:
        question = args.question if args.question is not None else read_text(args.question_file)
        if not question.strip():
            raise ValueError("The question is empty")
        prompt, manifest = build_prompt(question, args.attach, args.max_attachment_chars)
    except (OSError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    body: dict[str, object] = {
        "model": args.model,
        "messages": [{"role": "user", "content": prompt}],
    }
    if args.thinking:
        body["thinking"] = {"type": args.thinking}
    if args.reasoning_effort:
        body["reasoning_effort"] = args.reasoning_effort

    endpoint = args.base_url.rstrip("/") + "/chat/completions"
    if args.dry_run:
        print(json.dumps({"url": endpoint, "request": body, "attachments": manifest}, ensure_ascii=False, indent=2))
        return 0

    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if not api_key:
        print("Error: set DEEPSEEK_API_KEY in the environment before sending", file=sys.stderr)
        return 2

    request = urllib.request.Request(
        endpoint,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=args.timeout) as response:
            result = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace")
        print(f"API returned HTTP {exc.code}: {details[:4000]}", file=sys.stderr)
        return 1
    except urllib.error.URLError as exc:
        print(f"Network error: {exc.reason}", file=sys.stderr)
        return 1
    except (TimeoutError, json.JSONDecodeError) as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        return 1

    try:
        choice = result["choices"][0]
        message = choice["message"]
        answer = message.get("content") or ""
        if not isinstance(answer, str):
            answer = json.dumps(answer, ensure_ascii=False, indent=2)
    except (KeyError, IndexError, TypeError) as exc:
        print("Error: the API response did not contain a chat completion", file=sys.stderr)
        print(json.dumps(result, ensure_ascii=False)[:4000], file=sys.stderr)
        return 1

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    out_dir = args.output_dir or Path("results") / f"{stamp}_{slugify(args.title)}"
    try:
        out_dir.mkdir(parents=True, exist_ok=False)
        (out_dir / "request.md").write_text(prompt + "\n", encoding="utf-8")
        (out_dir / "response.md").write_text(answer.rstrip() + "\n", encoding="utf-8")
        meta = {
            "created_at": dt.datetime.now(dt.timezone.utc).isoformat(),
            "endpoint": endpoint,
            "model": result.get("model", args.model),
            "finish_reason": choice.get("finish_reason"),
            "usage": result.get("usage"),
            "attachments": manifest,
        }
        (out_dir / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"Error writing local results: {exc}", file=sys.stderr)
        print(answer)
        return 1

    print(answer)
    print(f"\nSaved response files to {out_dir}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

