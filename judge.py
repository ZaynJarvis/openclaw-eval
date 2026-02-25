"""
Grade OpenClaw QA responses using LLM judge.

Usage:
    uv run python judge.py output/answers.txt.json
    uv run python judge.py output/answers.txt.json --output output/grades.json
    uv run python judge.py output/answers.txt.json \
        --base-url https://ark.cn-beijing.volces.com/api/v3 \
        --token $ARK_API_KEY \
        --model doubao-seed-2-0-pro-260215
"""

import argparse
import asyncio
import json
import sys

from judge_util import grade_answers, load_answers


async def run(
    input_path: str,
    output_path: str | None,
    base_url: str | None,
    token: str | None,
    model: str,
) -> None:
    answers = load_answers(input_path)
    print(f"Loaded {len(answers)} answers from {input_path}", file=sys.stderr)

    graded = await grade_answers(answers, base_url=base_url, api_key=token, model=model)

    correct = sum(1 for g in graded if g["grade"])
    total = len(graded)
    score = correct / total if total > 0 else 0.0

    print(f"\nResults: {correct}/{total} correct ({score:.2%})")

    # Per-category breakdown if categories exist
    categories = {}
    for g in graded:
        cat = g.get("category", "unknown")
        categories.setdefault(cat, {"correct": 0, "total": 0})
        categories[cat]["total"] += 1
        if g["grade"]:
            categories[cat]["correct"] += 1

    if len(categories) > 1:
        print("\nPer-category scores:")
        for cat in sorted(categories):
            c = categories[cat]
            pct = c["correct"] / c["total"] if c["total"] > 0 else 0.0
            print(f"  Category {cat}: {c['correct']}/{c['total']} ({pct:.2%})")

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(
                {"score": score, "correct": correct, "total": total, "grades": graded},
                f,
                indent=2,
                ensure_ascii=False,
            )
        print(f"\nGrades written to {output_path}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Grade QA responses with LLM judge")
    parser.add_argument("input", help="Path to answers JSON file")
    parser.add_argument("--output", default=None, help="Path to write grades JSON")
    parser.add_argument(
        "--base-url",
        default=None,
        help="LLM API base URL (or set OPENAI_BASE_URL env var)",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="LLM API key (or set OPENAI_API_KEY env var)",
    )
    parser.add_argument(
        "--model",
        default="gpt-4o-mini",
        help="Model name for grading (default: gpt-4o-mini)",
    )
    args = parser.parse_args()

    asyncio.run(run(args.input, args.output, args.base_url, args.token, args.model))


if __name__ == "__main__":
    main()
