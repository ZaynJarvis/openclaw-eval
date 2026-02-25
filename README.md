# openclaw-eval

Evaluate OpenClaw responses using multi-round conversations from txt files or [LoCoMo](https://github.com/snap-research/locomo) JSON datasets.

## Run

```bash
uv sync
uv run eval.py ./locomo10_small.json --output output/trial.txt --tail "[try to remember what's said in the group]"
uv run eval.py qa ./locomo10_small.json --output output/answers.txt --count 10
export OPENAI_API_KEY=sk-proj-Bc..
uv run judge.py output/answers.txt.json
uv run judge.py output/answers.txt.json \
      --base-url https://ark.cn-beijing.volces.com/api/v3 \
      --token 024341c1-... \
      --model doubao-seed-2-0-pro-260215
```

## Dataset: LoCoMo10

`locomo10.json` contains 10 conversation samples with:

| Metric | Total |
|--------|-------|
| Conversations (samples) | 10 |
| Sessions | 272 |
| Messages | 5,882 |
| Images | 910 |
| QA pairs | 1,986 |

### Structure

```
locomo10.json  ->  list of samples
  sample
    ├── sample_id          # e.g. "conv-26"
    ├── conversation
    │   ├── speaker_a / speaker_b
    │   ├── session_N_date_time
    │   └── session_N      # list of messages
    │       └── { speaker, dia_id, text, img_url?, blip_caption?, query? }
    ├── qa                 # list of { question, answer, evidence, category }
    ├── event_summary
    ├── observation
    └── session_summary
```

## Two Modes

### `ingest` - Load conversations into openclaw

Sends conversation sessions to openclaw to build up memory/context. All sessions within a sample share one user UUID so context accumulates.

```bash
# Ingest specific sample, sessions 1-4
uv run python eval.py ingest ./locomo10.json --sample 0 --sessions 1-4

# Ingest with output log
uv run python eval.py ingest ./locomo10.json --sample 0 --sessions 1-4 --output ingest.txt

# Original txt mode
uv run python eval.py ingest example.txt --output output.txt
```

Ingest prints the user UUID for each sample:

```
=== Sample conv-26 ===
    user: f5d94f68-24aa-4bcc-a667-9ab11bf5edab
    4 session(s) to ingest
```

Each session is bundled into a single user message:

```
[group chat conversation]

Caroline: Hey Mel! Good to see you!

Melanie: Hey Caroline! What's up?

Caroline: The transgender stories were so inspiring!
https://example.com/image.jpg: a photo of a dog walking past a wall

[]
```

### `qa` - Run QA evaluation

Sends QA questions to openclaw and records responses alongside expected answers. **No ingestion** - requires `--user` UUID from a prior ingest run.

```bash
# Run all QAs for sample 0 using user from ingest
uv run python eval.py qa ./locomo10.json --sample 0 --user f5d94f68-... --output qa_results.txt

# Run first 10 QAs only
uv run python eval.py qa ./locomo10.json --sample 0 --user f5d94f68-... --count 10 --output qa_results.txt
```

Output format:

```
=== [conv-26] Q1 Category 5 ===
[question] What did Caroline realize after her charity race?
[expected] self-care is important
[response] <openclaw's response>
[evidence] D2:3
```

## Typical Workflow

```bash
# Step 1: ingest conversations (note the user UUID printed)
uv run python eval.py ingest ./locomo10.json --sample 0 --sessions 1-4

# Step 2: run QA using that user UUID
uv run python eval.py qa ./locomo10.json --sample 0 --user <UUID> --output qa_results.txt
```

## CLI Options

| Flag | Default | Description |
|------|---------|-------------|
| `mode` (positional) | required | `ingest` or `qa` |
| `input` (positional) | required | Path to `.txt` or `.json` input file |
| `--output` | none | Path to output file. Omit to skip writing |
| `--base-url` | `http://127.0.0.1:18789` | OpenClaw gateway URL |
| `--token` | `xxx` | Auth token (or `OPENCLAW_GATEWAY_TOKEN` env var) |
| `--sample` | all | LoCoMo: sample index (0-based) |
| `--sessions` | all | Ingest: session range, e.g. `1-4` or `3` |
| `--tail` | `[]` | Ingest: tail message appended per session |
| `--user` | none | QA: user UUID from a prior ingest run (required) |
| `--count` | all | QA: number of questions to run |
