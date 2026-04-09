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

On the first run the AI agent calls the OpenAlex API, writes a reusable script, and generates all outputs. Every run after that executes that script directly — no AI needed, no API cost beyond the free OpenAlex API.

### Cost

- **Every run after the first:** free
- **First run (agent writes the script):** ~$0.05–$0.30 via Anthropic API
