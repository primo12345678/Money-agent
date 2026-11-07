"""Safe, deterministic executor for approved CSV spreadsheet tasks.

It only processes files explicitly named in a task JSON. It never sends data
to third parties, executes macros/code, or uploads customer files.
"""
import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path.cwd().resolve()
ALLOWED_TASK_TYPES = {"clean_csv", "deduplicate_csv"}


def safe_path(value):
    path = (ROOT / value).resolve()
    if ROOT not in path.parents and path != ROOT:
        raise ValueError("Path must stay inside the Money-agent working directory")
    return path


def normalize_cell(value):
    value = "" if value is None else str(value)
    value = re.sub(r"\\s+", " ", value).strip()
    return value


def run_task(task):
    task_type = task.get("type")
    if task_type not in ALLOWED_TASK_TYPES:
        raise ValueError(f"Unsupported task type: {task_type}")

    input_path = safe_path(task.get("input_file", ""))
    output_path = safe_path(task.get("output_file", ""))
    if not input_path.is_file():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if input_path.suffix.lower() != ".csv" or output_path.suffix.lower() != ".csv":
        raise ValueError("This executor currently accepts CSV input and output only")
    if input_path == output_path:
        raise ValueError("Output file must differ from input file")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with input_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames:
            raise ValueError("CSV must contain a header row")
        headers = [normalize_cell(h) for h in reader.fieldnames]
        if any(not h for h in headers) or len(set(headers)) != len(headers):
            raise ValueError("CSV headers must be non-empty and unique after trimming")
        rows = list(reader)

    cleaned = []
    seen = set()
    duplicate_count = 0
    blank_cells_before = sum(
        1 for row in rows for header in reader.fieldnames
        if row.get(header) is None or not str(row.get(header)).strip()
    )
    lowercase_columns = set(task.get("options", {}).get("lowercase_columns", []))
    unknown = lowercase_columns.difference(headers)
    if unknown:
        raise ValueError("Unknown lowercase_columns: " + ", ".join(sorted(unknown)))

    for raw in rows:
        row = {}
        for original, header in zip(reader.fieldnames, headers):
            value = normalize_cell(raw.get(original, ""))
            if header in lowercase_columns:
                value = value.lower()
            row[header] = value
        key = tuple(row[h] for h in headers)
        if task_type == "deduplicate_csv" and key in seen:
            duplicate_count += 1
            continue
        seen.add(key)
        cleaned.append(row)

    with output_path.open("w", encoding="utf-8-sig", newline="") as target:
        writer = csv.DictWriter(target, fieldnames=headers, extrasaction="raise")
        writer.writeheader()
        writer.writerows(cleaned)

    report = {
        "task_id": str(task.get("task_id", "unnamed")),
        "type": task_type,
        "status": "completed",
        "input_file": str(input_path.relative_to(ROOT)),
        "output_file": str(output_path.relative_to(ROOT)),
        "rows_in": len(rows),
        "rows_out": len(cleaned),
        "duplicates_removed": duplicate_count,
        "blank_cells_before": blank_cells_before,
        "quality_checks": {
            "header_names_unique": len(set(headers)) == len(headers),
            "row_count_non_increasing": len(cleaned) <= len(rows),
            "output_exists": output_path.is_file(),
            "output_bytes": output_path.stat().st_size,
        },
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "human_review_required": True,
        "external_upload": False,
    }
    report_path = output_path.with_suffix(".quality.json")
    report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def main():
    parser = argparse.ArgumentParser(description="Run one approved Money-agent CSV task")
    parser.add_argument("--task", required=True, help="Path to a task JSON file")
    args = parser.parse_args()
    task_path = safe_path(args.task)
    task = json.loads(task_path.read_text(encoding="utf-8"))
    report = run_task(task)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
