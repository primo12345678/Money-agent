# Local task execution

Money Agent can now perform two deterministic spreadsheet tasks on approved CSV files:

- `clean_csv`: trims cell whitespace, collapses repeated spaces, optionally lowercases selected columns.
- `deduplicate_csv`: performs the same cleaning and removes exact duplicate rows.

## Run a task

1. Keep customer files on a private computer, not in this public GitHub repository.
2. Create a private working folder with an input CSV and a task JSON.
3. Run from the repository root:

```bash
python backend/executor.py --task tasks/my_task.json
```

Example task JSON:

```json
{
  "task_id": "client-001",
  "type": "deduplicate_csv",
  "input_file": "private_jobs/input.csv",
  "output_file": "private_jobs/output.csv",
  "options": {}
}
```

The executor writes the output CSV and a matching `.quality.json` report. The report is a QA aid, not proof that the result meets a client's full specification. Review the output against the task instructions before delivery.

## Boundaries

- Only CSV input/output is supported in this first executor release. Excel workbooks (.xlsx) and Google Sheets API integration are not yet implemented.
- Only the two allowlisted operations are accepted. No arbitrary Python, shell commands, macros, scraping, email, or network calls are executed.
- The executor does not upload files, contact clients, submit proposals, purchase Connects, or mark payments as received.
- Do not put customer personal data in the public GitHub repository. Use a private local folder and follow the client's data-handling instructions.
- Human review and client approval remain required before delivery.
