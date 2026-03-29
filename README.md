# 📚 Google Scholar Citation Tracker

Track all articles that cited a specific author's papers on Google Scholar. Generates a CSV with citation details and a summary report.

Built with the [selfhealing-agent](https://github.com/nkempynck/selfhealing-agent) package.

## Setup

```bash
git clone https://github.com/nkempynck/scholar-citations.git
cd scholar-citations

conda create -n scholar python=3.11 -y
conda activate scholar

pip install -r requirements.txt

export ANTHROPIC_API_KEY="sk-ant-..."
```

## Configure

Edit `run.py` and set your author:

```python
AUTHOR_NAME = "Jane Doe"
SCHOLAR_PROFILE = "https://scholar.google.com/citations?user=XXXXX"
```

To find the user ID, go to the author's Google Scholar profile — the URL contains `?user=XXXXX`.

## Usage

```bash
python run.py              # normal: script first, agent fallback
python run.py --agent      # force agent mode
python run.py --script     # script only, no agent fallback
```

## Output

- **`citations.csv`** — all citing articles with title, authors, year, citation count, venue, URL, and which paper was cited
- **`citations_summary.txt`** — overview with totals, top cited papers, yearly breakdown, and common venues

## How it works

First run: the AI agent figures out how to scrape Google Scholar (using the `scholarly` Python package), writes a standalone script, and saves it as `scrape_scholar.py`.

After that: `python run.py` just runs the standalone script directly — no AI, no API cost.

If Google Scholar changes something and the script breaks, the agent automatically takes over and fixes it.

## Notes

- Google Scholar has no official API and blocks automated requests aggressively
- The agent uses the `scholarly` package which handles most anti-bot measures
- For authors with many highly-cited papers, the full scrape can take a while due to rate limits
- This tool is for personal academic use

## Cost

- **Standalone script:** Free
- **Agent (fallback):** ~$0.05–$0.30 per run via the Anthropic API
