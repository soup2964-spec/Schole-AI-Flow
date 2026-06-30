# Draft emails in Cursor

After `python main.py filter --input your_clay_export.csv`:

## 1. Open the draft queue

Open `data/cursor_draft_queue.md` in Cursor.

## 2. Paste this prompt in chat

```
Draft one cold email per lead in @data/cursor_draft_queue.md.

Product: Scholé (schole.ai) — AI upskilling for enterprise L&D teams. Helps companies
turn Copilot/ChatGPT rollouts into measurable employee adoption. Role-specific lessons,
HR dashboard for adoption metrics.

Rules for each email:
- 70-90 words, plain text
- First line references their signal_evidence specifically
- Bridge: most companies stall on adoption, not access
- One CTA: 20-minute live demo with a founder
- No "I hope this finds you well"

Output as a markdown table with columns: email | subject | body
```

## 3. Merge into CSV

Copy the `subject` and `body` into `data/to_draft.csv` for each matching `email` row.

## 4. Send

```powershell
python main.py send --input data/to_draft.csv
```

## Tips

- Review every email before sending — you are the quality gate
- For the Scholé application, screenshot 2-3 drafts; do not mass-send their market uninvited
