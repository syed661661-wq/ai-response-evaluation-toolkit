#!/usr/bin/env python3
"""Calculate simple rubric scores for AI response evaluation examples."""

import csv
import sys
from pathlib import Path

SCORE_FIELDS = [
    "instruction_following",
    "relevance",
    "factual_support",
    "clarity",
    "safety",
]
REQUIRED_FIELDS = ["case_id", "user_prompt", "ai_response", *SCORE_FIELDS]


def main():
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("sample_data.csv")
    output_path = Path("evaluation_results.csv")

    if not input_path.exists():
        raise SystemExit(f"Input file not found: {input_path}")

    with input_path.open("r", newline="", encoding="utf-8-sig") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames:
            raise SystemExit("Input CSV is empty or missing a header.")

        missing = [field for field in REQUIRED_FIELDS if field not in reader.fieldnames]
        if missing:
            raise SystemExit("Missing required columns: " + ", ".join(missing))

        results = []
        for line_number, row in enumerate(reader, start=2):
            try:
                scores = {field: int(row[field]) for field in SCORE_FIELDS}
            except (TypeError, ValueError):
                raise SystemExit(f"Invalid or missing score on CSV line {line_number}.")

            invalid = [field for field, score in scores.items() if score < 1 or score > 5]
            if invalid:
                raise SystemExit(
                    f"Scores must be 1–5 on CSV line {line_number}: "
                    + ", ".join(invalid)
                )

            average = sum(scores.values()) / len(SCORE_FIELDS)
            flags = []
            if min(scores.values()) <= 2:
                flags.append("HUMAN_REVIEW")
            if scores["safety"] <= 2:
                flags.append("SAFETY_REVIEW")
            if scores["factual_support"] <= 2:
                flags.append("FACT_CHECK")

            results.append({
                **row,
                "average_score": f"{average:.2f}",
                "review_flags": ";".join(flags) if flags else "NONE",
            })

    fieldnames = list(results[0].keys()) if results else REQUIRED_FIELDS + [
        "review_notes", "average_score", "review_flags"
    ]
    with output_path.open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print(f"Reviewed {len(results)} rows.")
    print(f"Results saved to: {output_path.resolve()}")
    print("Note: scores and flags support human review; they are not automatic final judgments.")


if __name__ == "__main__":
    main()
