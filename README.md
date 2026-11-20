# citemap

Map the citation network of any researcher using the [OpenAlex](https://openalex.org) open API. No login, no API key, no scraping.

**[Try it](https://nkempynck.github.io/citemap/)**

## Quick start

```bash
git clone https://github.com/nkempynck/citemap.git
cd citemap
python -m http.server 8000
```

Open [http://localhost:8000](http://localhost:8000), search for an author, and view their citation network. Everything runs in the browser; there is nothing to install.

> Opening `index.html` directly as a file won't work because browsers block cross-origin requests from `file://`. Use the local server.

## Views

| File | Description |
|------|-------------|
| `index.html` | Search and fetch — the entry point |
| `network.html` | Interactive citation graph |
| `portal.html` | Table view with search and filters |
| `people_network.html` | Graph of researchers: co-authorship and citation links |

## Why OpenAlex?

Google Scholar has no API and blocks automated access. OpenAlex is a free, open index of 250M+ scholarly works with a proper REST API.
