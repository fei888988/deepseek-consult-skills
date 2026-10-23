# DeepSeek Consultation Skills

Reusable Claude Code and Codex skills for preparing a focused question, consulting DeepSeek through its API, and reviewing the answer as an independent opinion.

## Package contents

- .claude/skills/deepseek-consult/SKILL.md — Claude Code skill.
- .agents/skills/deepseek-consult/SKILL.md — Codex skill.
- .agents/skills/deepseek-consult/agents/openai.yaml — Codex skill metadata.
- scripts/deepseek_consult.py — small Python client for DeepSeek Chat Completions. It uses only the Python standard library.

## Install

Copy the relevant skill folder into the matching project directory. Copy scripts/deepseek_consult.py to the project root under scripts/ as well.

For Claude Code, install .claude/skills/deepseek-consult/. For Codex, install .agents/skills/deepseek-consult/.

## Use

1. Install Python 3.10 or newer.
2. Set DEEPSEEK_API_KEY in the shell or your local secret manager. Never put the key in a prompt file, repository, or command argument.
3. Choose a model ID currently available to your DeepSeek API account. The script requires an explicit model ID so the package does not pin a model that may later be renamed or retired.
4. Prepare a question file and, if needed, small text attachments (.md, .txt, .csv, or .json). Review attachments for secrets and unrelated personal data before sending them.
5. Preview the exact request locally, then send it. From the project root:

    python scripts/deepseek_consult.py --model deepseek-flash --question-file question.md --attach summary.csv --title "Strategy review" --dry-run
    python scripts/deepseek_consult.py --model deepseek-flash --question-file question.md --attach summary.csv --title "Strategy review"

The default API root is https://api.deepseek.com; use --base-url to select another compatible endpoint. Optional --thinking and --reasoning-effort flags are passed through for models that support them. Check the provider's current model list and API documentation before using model-specific options.

Each successful request writes request.md, response.md, and meta.json under results/ (or the directory passed with --output-dir). The API key is never written to those files.

## Scope

This package contains no project-specific data paths, scripts, strategy assumptions, or credentials. The included client sends text to DeepSeek; it does not upload binary files or extract text from PDFs, images, or office documents.
