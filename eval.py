"""
OpenClaw response evaluator.

Two modes:
  ingest  - Load conversations into openclaw (builds memory)
  qa      - Run QA questions against openclaw and output response vs expected answer

Usage:
    # Ingest conversations
    uv run python eval.py ingest locomo10.json --sample 0 --sessions 1-4

    # Run QA evaluation (uses same user from ingest)
    uv run python eval.py qa locomo10.json --sample 0 --output qa_results.txt

    # Original txt mode (ingest only)
    uv run python eval.py ingest example.txt --output output.txt
"""

import argparse
import json
import os
import sys
import time
import random
import string

import requests


# ---------------------------------------------------------------------------
# Txt-based test file parsing (original format)
# ---------------------------------------------------------------------------

def parse_test_file(path: str) -> list[dict]:
    """Parse txt test file into sessions.

    Each session is a dict with:
        - messages: list of user message strings
        - evals: list of eval expectation strings
    """
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    raw_sessions = content.split("---\n")
    sessions = []

    for raw in raw_sessions:
        lines = [line for line in raw.strip().splitlines() if line.strip()]
        if not lines:
            continue

        messages = []
        evals = []
        for line in lines:
            if line.startswith("eval:"):
                evals.append(line[len("eval:"):].strip())
            else:
                messages.append(line)

        if messages or evals:
            sessions.append({"messages": messages, "evals": evals})

    return sessions


# ---------------------------------------------------------------------------
# LoCoMo JSON parsing
# ---------------------------------------------------------------------------

def format_locomo_message(msg: dict) -> str:
    """Format a single LoCoMo message into a natural chat-style string.

    Output format:
        Speaker: text here
        image_url: caption
    """
    speaker = msg.get("speaker", "unknown")
    text = msg.get("text", "")
    line = f"{speaker}: {text}"

    img_urls = msg.get("img_url", [])
    if isinstance(img_urls, str):
        img_urls = [img_urls]
    blip = msg.get("blip_caption", "")

    if img_urls:
        for url in img_urls:
            caption = f": {blip}" if blip else ""
            line += f"\n{url}{caption}"
    elif blip:
        line += f"\n({blip})"

    return line


def load_locomo_data(
    path: str,
    sample_index: int | None = None,
) -> list[dict]:
    """Load LoCoMo JSON and optionally filter to one sample."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    if sample_index is not None:
        if sample_index < 0 or sample_index >= len(data):
            print(f"Error: sample index {sample_index} out of range (0-{len(data)-1})", file=sys.stderr)
            sys.exit(1)
        return [data[sample_index]]
    return data


def build_session_messages(
    item: dict,
    session_range: tuple[int, int] | None = None,
    tail: str = "[]",
) -> list[dict]:
    """Build bundled session messages for one LoCoMo sample.

    Returns list of dicts with keys: message, meta.
    """
    conv = item["conversation"]
    speakers = f"{conv['speaker_a']} & {conv['speaker_b']}"

    session_keys = sorted(
        [k for k in conv if k.startswith("session_") and not k.endswith("_date_time")],
        key=lambda k: int(k.split("_")[1]),
    )

    sessions = []
    for sk in session_keys:
        sess_num = int(sk.split("_")[1])
        if session_range:
            lo, hi = session_range
            if sess_num < lo or sess_num > hi:
                continue

        dt_key = f"{sk}_date_time"
        date_time = conv.get(dt_key, "")

        parts = ["[group chat conversation]"]
        for msg in conv[sk]:
            parts.append(format_locomo_message(msg))
        if tail:
            parts.append(tail)
        combined = "\n\n".join(parts)

        sessions.append({
            "message": combined,
            "meta": {
                "sample_id": item["sample_id"],
                "session_key": sk,
                "date_time": date_time,
                "speakers": speakers,
            },
        })

    return sessions


# ---------------------------------------------------------------------------
# API helpers
# ---------------------------------------------------------------------------

def extract_response_text(response_json: dict) -> str:
    """Extract assistant text from the /v1/responses API response."""
    try:
        for item in response_json.get("output", []):
            if item.get("type") == "message":
                for content in item.get("content", []):
                    if content.get("type") == "output_text":
                        return content.get("text", "")
        for item in response_json.get("output", []):
            if "text" in item:
                return item["text"]
            for content in item.get("content", []):
                if "text" in content:
                    return content["text"]
    except (KeyError, TypeError, IndexError):
        pass
    return f"[ERROR: could not extract text from response: {response_json}]"


def send_message(
    base_url: str, token: str, user: str, message: str
) -> str:
    """Send a single message to the OpenClaw responses API and return the assistant's reply."""
    url = f"{base_url}/v1/responses"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    payload = {
        "model": "openclaw",
        "input": message,
        "user": user,
    }

    resp = requests.post(url, json=payload, headers=headers, timeout=300)
    resp.raise_for_status()
    return extract_response_text(resp.json())


# ---------------------------------------------------------------------------
# Ingest: load conversations into openclaw
# ---------------------------------------------------------------------------

def run_ingest(
    args: argparse.Namespace,
) -> None:
    session_range = parse_session_range(args.sessions) if args.sessions else None

    if args.input.endswith(".json"):
        samples = load_locomo_data(args.input, args.sample)
        results = []

        for item in samples:
            sample_id = item["sample_id"]
            user_key = f"eval-{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}"
            sessions = build_session_messages(item, session_range, tail=args.tail)

            print(f"\n=== Sample {sample_id} ===", file=sys.stderr)
            print(f"    user: {user_key}", file=sys.stderr)
            print(f"    {len(sessions)} session(s) to ingest", file=sys.stderr)

            for sess in sessions:
                meta = sess["meta"]
                msg = sess["message"]
                label = f"{meta['session_key']} ({meta['date_time']})"

                preview = msg.replace("\n", " | ")[:80]
                print(f"  [{label}] {preview}...", file=sys.stderr)

                try:
                    reply = send_message(args.base_url, args.token, user_key, msg)
                    print(f"    -> {reply[:80]}{'...' if len(reply) > 80 else ''}", file=sys.stderr)
                    results.append({
                        "sample_id": sample_id,
                        "session": meta["session_key"],
                        "user": user_key,
                        "reply": reply,
                    })
                except Exception as e:
                    print(f"    -> [ERROR] {e}", file=sys.stderr)
                    results.append({
                        "sample_id": sample_id,
                        "session": meta["session_key"],
                        "user": user_key,
                        "reply": f"[ERROR] {e}",
                    })

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                for r in results:
                    f.write(f"[{r['sample_id']}/{r['session']}] user={r['user']}\n")
                    f.write(f"  {r['reply']}\n\n")
            print(f"Results written to {args.output}", file=sys.stderr)

            json_path = args.output + ".json"
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"Results (JSON) written to {json_path}", file=sys.stderr)

    else:
        # Original txt mode
        sessions = parse_test_file(args.input)
        print(f"Running {len(sessions)} session(s)", file=sys.stderr)

        results = []
        for idx, session in enumerate(sessions, start=1):
            session_key = f"eval-{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}"
            print(f"--- Session {idx} (user={session_key}) ---", file=sys.stderr)

            turns = []
            for msg in session["messages"]:
                print(f"  [user] {msg}", file=sys.stderr)
                try:
                    reply = send_message(args.base_url, args.token, session_key, msg)
                    print(f"  [assistant] {reply[:80]}{'...' if len(reply) > 80 else ''}", file=sys.stderr)
                    turns.append(("user", msg))
                    turns.append(("assistant", reply))
                except Exception as e:
                    print(f"  [ERROR] {e}", file=sys.stderr)
                    turns.append(("user", msg))
                    turns.append(("error", str(e)))
                    break

            results.append({"index": idx, "turns": turns, "evals": session["evals"]})

        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                for r in results:
                    f.write(f"=== Session {r['index']} ===\n")
                    for role, text in r["turns"]:
                        f.write(f"[{role}] {text}\n")
                    for ev in r["evals"]:
                        f.write(f"[eval] {ev}\n")
                    f.write("\n")
            print(f"\nResults written to {args.output}", file=sys.stderr)


# ---------------------------------------------------------------------------
# QA: run QA questions and compare with expected answers
# ---------------------------------------------------------------------------

def run_qa(
    args: argparse.Namespace,
) -> None:
    """QA only: send questions and get responses. No ingestion.

    Requires --user to target a user that already has context from a prior ingest run.
    """
    if not args.input.endswith(".json"):
        print("Error: QA mode only works with LoCoMo JSON files", file=sys.stderr)
        sys.exit(1)

    samples = load_locomo_data(args.input, args.sample)
    user_key = args.user or f"eval-{''.join(random.choices(string.ascii_lowercase + string.digits, k=8))}"
    print(f"    user: {user_key}", file=sys.stderr)

    all_results = []

    for item in samples:
        sample_id = item["sample_id"]
        qas = item.get("qa", [])
        if args.count is not None:
            qas = qas[:args.count]

        print(f"\n=== Sample {sample_id} (user={user_key}) ===", file=sys.stderr)
        print(f"    Running {len(qas)} QA question(s)...", file=sys.stderr)

        for qi, qa in enumerate(qas, start=1):
            question = qa["question"]
            expected = str(qa["answer"])
            category = qa.get("category", "")
            evidence = qa.get("evidence", [])

            print(f"  Q{qi}/{len(qas)}: {question[:60]}{'...' if len(question) > 60 else ''}", file=sys.stderr)

            try:
                response = send_message(args.base_url, args.token, user_key, question)
                print(f"    A: {response[:60]}{'...' if len(response) > 60 else ''}", file=sys.stderr)
            except Exception as e:
                response = f"[ERROR] {e}"
                print(f"    A: {response}", file=sys.stderr)

            all_results.append({
                "sample_id": sample_id,
                "qi": qi,
                "question": question,
                "expected": expected,
                "response": response,
                "category": category,
                "evidence": evidence,
            })

    # Write output
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            for r in all_results:
                f.write(f"=== [{r['sample_id']}] Q{r['qi']} Category {r['category']} ===\n")
                f.write(f"[question] {r['question']}\n")
                f.write(f"[expected] {r['expected']}\n")
                f.write(f"[response] {r['response']}\n")
                f.write(f"[evidence] {', '.join(r['evidence'])}\n")
                f.write("\n")
        print(f"QA results written to {args.output}", file=sys.stderr)

        json_path = args.output + ".json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(all_results, f, indent=2, ensure_ascii=False)
        print(f"QA results (JSON) written to {json_path}", file=sys.stderr)
    else:
        print("\nDone (no output file requested).", file=sys.stderr)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_session_range(s: str) -> tuple[int, int]:
    """Parse '1-4' or '3' into (lo, hi) inclusive tuple."""
    if "-" in s:
        lo, hi = s.split("-", 1)
        return int(lo), int(hi)
    n = int(s)
    return n, n


def main():
    parser = argparse.ArgumentParser(description="Evaluate OpenClaw responses")
    parser.add_argument("mode", choices=["ingest", "qa"], help="Mode: ingest (load conversations) or qa (run QA eval)")
    parser.add_argument("input", help="Path to test file (.txt or .json)")
    parser.add_argument(
        "--output",
        default=None,
        help="Path to output file (omit to skip writing)",
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:18789",
        help="OpenClaw gateway base URL (default: http://127.0.0.1:18789)",
    )
    parser.add_argument(
        "--token",
        default=os.environ.get("OPENCLAW_GATEWAY_TOKEN", "xxx"),
        help="Auth token (or set OPENCLAW_GATEWAY_TOKEN env var)",
    )
    parser.add_argument(
        "--sample",
        type=int,
        default=None,
        help="LoCoMo: sample index (0-based). Default: all samples.",
    )
    parser.add_argument(
        "--sessions",
        default=None,
        help="LoCoMo: session range, e.g. '1-4' or '3'. Default: all sessions.",
    )
    parser.add_argument(
        "--tail",
        default="[]",
        help="Tail message appended after conversation messages per session (default: '[]')",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="QA mode: number of QA questions to run. Default: all.",
    )
    parser.add_argument(
        "--user",
        default=None,
        help="QA mode: user UUID from a prior ingest run to target.",
    )
    args = parser.parse_args()

    if not args.token:
        print("Error: --token or OPENCLAW_GATEWAY_TOKEN env var is required", file=sys.stderr)
        sys.exit(1)

    if args.mode == "ingest":
        run_ingest(args)
    elif args.mode == "qa":
        run_qa(args)


if __name__ == "__main__":
    main()
