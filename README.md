# citemap

Map the citation network of any researcher using the [OpenAlex](https://openalex.org) open API. Generates an interactive graph and a CSV export.

**[View the live network](https://nkempynck.github.io/citemap/)**

Built with [selfhealing-agent](https://github.com/nkempynck/selfhealing-agent).

## Why OpenAlex?

Google Scholar has no API and blocks automated access. OpenAlex is a free, open index of 250M+ scholarly works with a proper API. No scraping, no CAPTCHAs.

## Setup

```bash
git clone https://github.com/nkempynck/citemap.git
cd citemap

conda create -n citemap python=3.11 -y
conda activate citemap
pip install -r requirements.txt

export ANTHROPIC_API_KEY="sk-ant-..."  # only needed for the first run
```

## Run

```bash
python run.py
```

You'll be prompted for an author name. The tool searches OpenAlex, shows matches, and you pick the right one.

You can also pass the name directly:

```bash
python run.py "Jane Smith"
```

Or skip the lookup if you already know the [OpenAlex author ID](https://openalex.org/authors):

```bash
python run.py --name "Jane Smith" --id "A1234567890"
```

## View locally

Start a local server in the project folder:

```bash
python -m http.server 8000
```

Then open [http://localhost:8000/network.html](http://localhost:8000/network.html).

Note: opening `network.html` directly as a file won't work since browsers block local file requests for security reasons.

## Output

- `network.html` — interactive citation graph
- `portal.html` — table view with search and filters
- `citations.csv` — flat export with title, authors, year, citations, venue and DOI

## How it works

On the first run the AI agent calls the OpenAlex API, writes a reusable script (`scrape_citations.py`), and generates all outputs. Every run after that executes the script directly, no AI involved and no API cost beyond the free OpenAlex API.

First run costs roughly $0.05-$0.30 via the Anthropic API. Every run after that is free.

## Advanced

By default `run.py` runs the generated script and only falls back to the agent if something goes wrong. You can override this:

```bash
python run.py --script   # always run the script
python run.py --agent    # force the agent to rewrite the script from scratch
```

`--agent` is useful if the script has gotten out of date. You'll need a valid `ANTHROPIC_API_KEY` for this.
