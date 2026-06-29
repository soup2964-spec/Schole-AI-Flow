# Scholé AI Flow

US-targeted lead generation engine for **Scholé** (AI upskilling / L&D). Finds VP L&D, CHRO, and AI-enablement decision-makers, filters to **warm-intent** companies (AI pilots, rollouts, hiring signals), drafts personalized outbound, and pushes to **Instantly**.

Built as a Growth Engineer application artifact — same pattern as Sponsorfi (LLM scraper + lead scoring + outbound).

## Flow

```
Find people (Clay UI or Apollo)
  → warm-intent check (AI pilot / AI hiring)
  → ICP score
  → personalize email
  → Instantly sequence
  → HubSpot (manual / Clay HTTP column)
```

See `docs/` for the full Clay playbook and conceptual architecture.

## Quick start

```bash
cd schole-leadgen
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt
copy .env.example .env          # add your keys locally — never commit .env
```

### Dry-run on sample data (no API keys)

```bash
python main.py run --input data/sample_leads.csv --output data/leads_qualified.csv
```

### Verify Clay API key

```bash
python main.py verify-clay
```

> Clay's API key works for **Enterprise enrich** lookups. "Find People" runs in the Clay UI — use `push-clay` to send rows into your table webhook, or export CSV from Clay and run the pipeline.

### Source leads via Apollo

```bash
python main.py source-apollo --limit 50 --output data/leads_raw.csv
python main.py run --input data/leads_raw.csv --live
```

### Push leads into Clay table (webhook)

1. In Clay: create table → Add source → **Webhook** → copy URL into `.env` as `CLAY_WEBHOOK_URL`
2. Run:

```bash
python main.py push-clay --input data/leads_raw.csv
```

### Send to Instantly (live)

```bash
python main.py run --input data/leads_qualified.csv --live --send
```

Configure your Instantly campaign to use `{{subject}}` and `{{body}}` custom variables.

## Clay setup (recommended)

1. **Find People** in Clay with US filters + L&D/CHRO titles (see `docs/clay-playbook.md`)
2. Add **Claygent** columns for warm intent (AI pilot, AI hiring)
3. Filter to warm accounts → enrich emails
4. Add **AI column** for email copy (prompts in playbook)
5. **HTTP API column** → Instantly, or export CSV and use this repo's `run` command

## Project structure

```
main.py                 CLI entrypoint
config.py               env settings
pipeline/
  apollo_source.py      Apollo people search
  clay_client.py        Clay webhook + Enterprise API
  csv_source.py         Import Clay/Apollo CSV exports
  intent.py               Warm-intent + ICP scoring
  personalize.py          Email drafting
  deliver.py              Instantly push
  runner.py               Orchestration
docs/
  clay-playbook.md        Step-by-step Clay build
  conceptual-flow.md      Architecture + data model
```

## Security

- **Never** paste API keys in chat or commit `.env`
- Do not mass-send to Scholé prospects before you're hired — use dry-run + sample output for the application

## License

Private — personal job-search / demo project.
