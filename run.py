"""
Citation Tracker (OpenAlex)
===========================
Uses the selfhealing-agent package to fetch citation data from the
OpenAlex API and generate a CSV + citation network graph.

OpenAlex is free, open, and doesn't block automated requests.
No scraping needed — just clean API calls.

Usage:
    python run.py              # normal: script first, agent fallback
    python run.py --agent      # force agent mode
    python run.py --script     # script only, no agent fallback
"""

import argparse

from selfhealing_agent import Agent

# ── Configure your author here ──────────────────────────────────────────────
AUTHOR_NAME = "Niklas Kempynck"
# Find your OpenAlex ID at: https://openalex.org/authors?search=YOUR+NAME
# Or let the agent find it by name
OPENALEX_AUTHOR_ID = ""  # e.g. "A1234567890" — leave empty to search by name
# ─────────────────────────────────────────────────────────────────────────────

agent = Agent(
    name="citation-tracker",
    instructions=f"""\
Fetch citation data for an author from the OpenAlex API and generate:
1. A CSV of all papers that cited this author's work
2. A summary report
3. An HTML citation network graph

Author: {AUTHOR_NAME}
OpenAlex Author ID: {OPENALEX_AUTHOR_ID or "unknown — search by name first"}

=== OPENALEX API BASICS ===

OpenAlex is a free, open API for scholarly data. No scraping needed.
API docs: https://docs.openalex.org
Note: Add an email parameter to be polite: &mailto=your@email.com

Key endpoints:
- Search author: https://api.openalex.org/authors?search={AUTHOR_NAME}
- Author's works: https://api.openalex.org/works?filter=author.id:AUTHOR_ID&sort=cited_by_count:desc&per_page=100
- Papers citing a work: https://api.openalex.org/works?filter=cites:WORK_ID&per_page=100&cursor=*
- Use cursor pagination for large result sets: add &cursor=* to first request,
  then use the "next_cursor" from the response for subsequent pages

=== STEPS ===

1. Find the author's OpenAlex ID (search by name if not provided)
   - Verify it's the right person by checking institution/works
   - Print author name, institution, total works, total citations

2. Fetch ALL works by this author
   - Use pagination if more than 100 works
   - For each work: get title, year, DOI, cited_by_count, OpenAlex ID

3. For each work, fetch ALL citing papers
   - Use cursor pagination: &cursor=* for first page, then use next_cursor
   - For each citing paper: title, authors (first author + et al), year,
     cited_by_count, venue/journal, DOI, URL
   - Track which of the author's papers it cites
   - Print progress: "Fetching citations for: [title] (N citations)..."

4. Process the data:
   - Remove duplicates (same paper may cite multiple works — merge cited_papers)
   - Sort by year (newest first), then by citation_count

5. Save citations.csv with columns:
   title, authors, year, citation_count, venue, doi, url, cited_papers

6. Save citations_summary.txt with:
   - Author profile (name, institution, h-index, total citations)
   - Total unique citing papers found
   - Expected vs actual count (from author's total citation count)
   - Top 10 most-cited citing papers
   - Breakdown by year
   - Most common venues/journals

7. Generate citation_network.html — an interactive graph visualization:
   - Use vis.js (from CDN) for the network graph
   - Nodes = papers (author's papers + citing papers)
   - Author's papers: larger nodes, colored differently
   - Node size proportional to citation count
   - Edges = citation links (from citing paper to cited paper)
   - On hover: show paper title, year, citation count
   - On click: open the paper URL
   - Include a legend and basic controls (zoom, filter by year)
   - Make it a standalone HTML file that opens in any browser

=== VALIDATION ===

- Compare your total unique citing papers with the author's total
  citation count from OpenAlex. They should be close (within 80%).
- NEVER use fake or placeholder data. Every row must come from the API.
- If the API returns errors, report them honestly — do not make up data.
- Print expected vs actual counts at the end.

=== IMPORTANT ===

- Be polite to the API: add small delays (0.5s) between requests
- Use cursor pagination for large result sets, not page numbers
- The OpenAlex API is reliable — if something fails, it's likely a
  bug in your code, not the API blocking you
""",
    output_file="citations.csv",
    script_file="scrape_citations.py",
    max_tokens=8192,
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Citation Tracker (OpenAlex)")
    parser.add_argument("--agent", action="store_true", help="Force agent mode")
    parser.add_argument("--script", action="store_true", help="Script only, no agent fallback")
    args = parser.parse_args()

    if args.agent:
        agent.run_agent_only()
    elif args.script:
        agent.run_script_only()
    else:
        agent.run()