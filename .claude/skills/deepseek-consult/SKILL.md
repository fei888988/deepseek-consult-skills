---
name: deepseek-consult
description: "Use when the user explicitly asks to consult DeepSeek for an independent second opinion, critique, or research review. Helps prepare a focused, evidence-checkable request and review the returned answer."
---

# DeepSeek Consultation

Treat DeepSeek's answer as an independent opinion to examine, not as a conclusion to adopt. Use this skill only when the user explicitly asks to consult DeepSeek or asks for its second opinion. If the user only wants to discuss an idea or draft a question, do not send an API request.

## Prepare the question

- Identify the exact decision, hypothesis, or claim the user wants reviewed. Make it specific enough to be answered or falsified.
- Include the minimum context needed to avoid a second paid request: relevant constraints, definitions, time period, prior tests, and results.
- Define every field, unit, timestamp, and comparison in attached data. State whether a timestamp is a signal time, observation time, or execution time when that distinction matters.
- Ask DeepSeek to separate established facts, assumptions, and conjectures; identify plausible alternative explanations; state what evidence would change its view; and propose a small test with predicted outcomes for competing explanations.
- Preserve the user's current view as a hypothesis to challenge, not as an assumed fact. Do not ask a leading question that presupposes the answer.

Suggested question file:

```markdown
# Question
<The specific decision or claim to evaluate>

# Context
<Relevant background, constraints, prior tests, and observed results>

# Data notes
<Field definitions, units, sampling and timestamp conventions>

# Current hypothesis (optional)
<The user's current view, clearly labeled as a hypothesis>

# Review requested
<Alternative explanations, evidence needed, a falsifiable test, and expected outcomes>
```

## Protect data and control cost

- Before attaching data, inspect it and remove API keys, passwords, cookies, account identifiers, personal data, and unrelated records.
- Send only the smallest useful sample or summary. Do not attach an entire dataset when aggregate statistics or a narrow extract will answer the question.
- Attachments supported by the included client are UTF-8 text files (`.md`, `.txt`, `.csv`, and `.json`). It does not parse PDFs, images, or office files.
- Review the dry-run payload before making the paid API call. Use the model ID the user selected or an ID confirmed in the current DeepSeek account model list; do not silently substitute another model.

## Send a request

The package client is `scripts/deepseek_consult.py` at the project root. Set `DEEPSEEK_API_KEY` in the environment or an approved local secret manager. Never place the key in files, prompts, output, or shell arguments.

Preview first:

```bash
python scripts/deepseek_consult.py --model <model-id> --question-file <question.md> --attach <summary.csv> --title "<short title>" --dry-run
```

After confirming the preview and the user's authorization to consult DeepSeek, send:

```bash
python scripts/deepseek_consult.py --model <model-id> --question-file <question.md> --attach <summary.csv> --title "<short title>"
```

Omit `--attach` when there are no attachments. `--thinking` and `--reasoning-effort` are optional provider parameters; use them only when supported by the selected model. The script writes the sent prompt, final response, and request metadata under `results/` and never records the API key.

## Review the answer

- Verify factual and technical claims against primary sources, the user's data, or reproducible calculations.
- Distinguish DeepSeek's suggestions from the user's established conclusions. Do not present agreement between models as proof.
- Explain where the answer is useful, where it depends on assumptions, and what should be tested next.
- If the request includes an experiment, identify its control, changed variable, measurement, and the observations that would support or weaken each explanation.
- Do not execute a proposed experiment, spend additional API credits, or change project files beyond the user's request.

