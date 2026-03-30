# 📚 Citation Tracker

Track all papers that cited a specific author's work, using the [OpenAlex](https://openalex.org) open API. Generates a CSV, summary report, and interactive citation network graph.

Built with [selfhealing-agent](https://github.com/nkempynck/selfhealing-agent).

## Why OpenAlex instead of Google Scholar?

Google Scholar has no API and aggressively blocks automated access. OpenAlex is a free, open index of 250M+ scholarly works with a proper API — no scraping, no blocking, no CAPTCHAs.

## Setup

```bash
git clone https://github.com/nkempynck/citation-tracker.git
cd citation-tracker

conda create -n citations python=3.11 -y
conda activate citations
pip install -r requirements.txt

export ANTHROPIC_API_KEY="sk-ant-..."  # only needed for agent mode
```

## Configure

Edit `run.py` and set `AUTHOR_NAME` (and optionally `OPENALEX_AUTHOR_ID`). To find the ID, search at [openalex.org/authors](https://openalex.org/authors).

## Usage

```bash
python run.py              # normal: script first, agent fallback
python run.py --agent      # force agent mode
python run.py --script     # script only
```

## Output

- **`citations.csv`** — all citing papers with title, authors, year, citations, venue, DOI, URL, and which paper was cited
- **`citations_summary.txt`** — author profile, totals, top papers, yearly breakdown, common venues
- **`citation_network.html`** — interactive graph visualization (open in browser)

## How it works

First run: the AI agent calls the OpenAlex API, writes a standalone script, and generates all outputs.

After that: `python run.py` runs the standalone script directly — no AI, no API cost (just the free OpenAlex API).

## Cost

- **Standalone script:** Free (OpenAlex API is free)
- **Agent (fallback):** ~$0.05–$0.30 via Anthropic API, only when needed