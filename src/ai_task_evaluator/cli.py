from __future__ import annotations

import argparse
import json
from pathlib import Path

from .evaluator import evaluate_task, load_task


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Evaluate a trusted local AI coding task submission.")
    parser.add_argument("task", type=Path, help="Path to task JSON")
    parser.add_argument("submission", type=Path, help="Submission directory")
    parser.add_argument("--report", type=Path, help="Optional JSON report output path")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    report = evaluate_task(load_task(args.task), args.submission)
    rendered = json.dumps(report.to_dict(), ensure_ascii=False, indent=2)
    print(rendered)
    if args.report:
        args.report.write_text(rendered + "\n", encoding="utf-8")
    return 0 if report.score == 100 else 1


if __name__ == "__main__":
    raise SystemExit(main())
