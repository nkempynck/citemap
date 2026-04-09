# Citation Tracker

Track all papers that cited a specific author's work, using the [OpenAlex](https://openalex.org) open API. Generates a CSV and an interactive citation network graph.

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

## Usage

```bash
python run.py                          # interactive: prompts for author name
python run.py "Niklas Kempynck"        # search by name, pick from results
python run.py --name "..." --id "..."  # skip lookup, use OpenAlex ID directly
python run.py --agent                  # force agent mode
python run.py --script                 # script only, no agent fallback
```

When you run without `--id`, the tool searches OpenAlex for matching authors and shows you a numbered list to pick from. If there's only one match it's selected automatically.

To find an OpenAlex author ID manually, search at [openalex.org/authors](https://openalex.org/authors).

## Output

- **`citation_data.json`** — full citation network (nodes + edges), used by both viewers
- **`citations.csv`** — flat export with title, authors, year, citations, venue, DOI, URL, and which author paper was cited
- **`network.html`** — interactive force-directed graph, open in browser
- **`portal.html`** — paper portal view

## Publish to GitHub Pages

After running `run.py`, commit `network.html`, `portal.html`, and `citation_data.json` and push. All three must be in the same location that GitHub Pages serves from.

Enable GitHub Pages once in your repo: **Settings → Pages → Source: Deploy from a branch → Branch: `main` / root**

Your network will be live at `https://<username>.github.io/<repo>/network.html`.

## How it works

First run: the AI agent calls the OpenAlex API, writes a standalone script (`scrape_citations.py`), and generates all outputs.

After that: `python run.py` runs the standalone script directly — no AI, no API cost (just the free OpenAlex API).

## Cost

- **Standalone script:** Free (OpenAlex API is free)
- **Agent (first run / fallback):** ~$0.05–$0.30 via Anthropic API, only when needed
