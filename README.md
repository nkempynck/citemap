# Citation Tracker

Track all papers that cited a specific author's work, using the [OpenAlex](https://openalex.org) open API. Generates an interactive citation network graph and a CSV export.

**[View the live network →](https://nkempynck.github.io/scholar-citations/)**

Built with [selfhealing-agent](https://github.com/nkempynck/selfhealing-agent).

---

## Try it yourself

Want to generate this for your own citation network? Follow the steps below.

### Why OpenAlex instead of Google Scholar?

Google Scholar has no API and aggressively blocks automated access. OpenAlex is a free, open index of 250M+ scholarly works with a proper API — no scraping, no blocking, no CAPTCHAs.

### Setup

```bash
git clone https://github.com/nkempynck/scholar-citations.git
cd scholar-citations

conda create -n citations python=3.11 -y
conda activate citations
pip install -r requirements.txt

export ANTHROPIC_API_KEY="sk-ant-..."  # only needed for the first run
```

### Run

```bash
python run.py
```

You'll be prompted for an author name. The tool searches OpenAlex, shows matching authors, and you pick the right one. That's it.

You can also pass the name directly:

```bash
python run.py "Jane Smith"
```

Or skip the lookup entirely if you already know the [OpenAlex author ID](https://openalex.org/authors):

```bash
python run.py --name "Jane Smith" --id "A1234567890"
```

### View the network locally

After running, start a local server in the project folder:

```bash
python -m http.server 8000
```

Then open [http://localhost:8000/network.html](http://localhost:8000/network.html) in your browser.

> Opening `network.html` directly as a file won't work — browsers block local file requests for security reasons. The local server sidesteps this.

### Output

- **`network.html`** — interactive force-directed citation graph
- **`portal.html`** — paper portal view
- **`citations.csv`** — flat export with title, authors, year, citations, venue, DOI, and which paper was cited

### How it works

On the first run the AI agent calls the OpenAlex API, writes a reusable script (`scrape_citations.py`), and generates all outputs. Every run after that executes that script directly — no AI needed, no API cost beyond the free OpenAlex API.

### Cost

- **Every run after the first:** free
- **First run (agent writes the script):** ~$0.05–$0.30 via Anthropic API

---

### Advanced: controlling agent vs. script mode

By default `run.py` runs the generated script if it exists, and falls back to the agent only if something goes wrong. You can override this:

```bash
python run.py --script   # always run the script, never fall back to the agent
python run.py --agent    # force the agent to run (re-generates the script from scratch)
```

`--agent` is useful if the generated script has gotten out of date or is producing wrong output and you want the AI to rewrite it. You'll need a valid `ANTHROPIC_API_KEY` set in your environment for this.
