# Scholé AI Flow

Three tools. One flow.

```
Clay (get leads)  ->  Cursor (draft emails)  ->  Instantly (send)
```

## Step 1 — Clay (get leads)

In Clay UI ([playbook](docs/clay-playbook.md)):

1. **Find People** — VP/Head L&D, CHRO, AI enablement leaders, US, 500+ employees
2. **Claygent** — warm intent (AI pilot, AI hiring)
3. **Filter** warm accounts only
4. **Enrich emails**
5. **Export CSV**

Optional: push seed rows into Clay via webhook:

```powershell
python main.py push-clay --input seed.csv
```

## Step 2 — Cursor (draft emails)

Filter warm leads and generate a Cursor brief:

```powershell
python main.py filter --input your_clay_export.csv
```

This creates:

- `data/to_draft.csv` — empty `subject` / `body` columns
- `data/cursor_draft_queue.md` — paste into **Cursor chat**

In Cursor, say:

> Draft a cold email for each lead in @data/cursor_draft_queue.md. Return CSV columns: email, subject, body. Scholé sells AI upskilling to L&D teams.

Copy the drafted emails back into `data/to_draft.csv` (merge subject/body by email).

See [docs/cursor-drafting.md](docs/cursor-drafting.md).

## Step 3 — Instantly (send)

Add to `.env`:

```
INSTANTLY_API_KEY=...
INSTANTLY_CAMPAIGN_ID=...
```

Campaign template should use `{{subject}}` and `{{body}}` custom variables.

```powershell
python main.py send --input data/to_draft.csv
```

## Commands

| Command | What |
|---|---|
| `verify-clay` | Test Clay API key |
| `push-clay --input file.csv` | Push rows into Clay webhook |
| `filter --input clay_export.csv` | Warm filter + Cursor draft queue |
| `send --input to_draft.csv` | Push to Instantly |

## Setup

```powershell
cd schole-leadgen
pip install -r requirements.txt
copy .env.example .env
```

No Apollo. No OpenAI API in this repo — email drafting happens in Cursor.
