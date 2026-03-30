"""
Citation Tracker (OpenAlex)
===========================
Fetches recursive citation data from the OpenAlex API for an author,
saves it as structured JSON, and generates a CSV export.

The JSON is the single source of truth — the portal and network graph
(separate HTML files) both read from it.

Usage:
    python run.py              # normal: script first, agent fallback
    python run.py --agent      # force agent mode
    python run.py --script     # script only, no agent fallback
"""

import argparse

from selfhealing_agent import Agent

# ── Configure your author here ──────────────────────────────────────────────
AUTHOR_NAME = "Niklas Kempynck"
OPENALEX_AUTHOR_ID = "A5093400185"  # Find at https://openalex.org/authors
# ─────────────────────────────────────────────────────────────────────────────

# How many levels deep to go
# Level 0: your papers
# Level 1: papers that cite yours + papers yours reference
# Level 1: papers that cite yours + papers yours reference
DEPTH = 1

# Only expand level 2 for papers with at least this many citations
# Set DEPTH = 2 and adjust this to enable deeper crawling (can be very slow)
MIN_CITATIONS_FOR_EXPANSION = 20

agent = Agent(
    name="citation-tracker",
    instructions=f"""\
Fetch recursive citation network data for an author from the OpenAlex API
and save it as a structured JSON file.

Author: {AUTHOR_NAME}
OpenAlex Author ID: {OPENALEX_AUTHOR_ID}
Recursion depth: {DEPTH}
Min citations for level 2 expansion: {MIN_CITATIONS_FOR_EXPANSION}

=== OPENALEX API BASICS ===

OpenAlex is a free, open API. No scraping needed.
Add &mailto=your@email.com to be polite.

Key endpoints:
- Author info: https://api.openalex.org/authors/{OPENALEX_AUTHOR_ID}?mailto=your@email.com
- Author's works: https://api.openalex.org/works?filter=author.id:{OPENALEX_AUTHOR_ID}&sort=cited_by_count:desc&per_page=100&mailto=your@email.com
- Papers citing a work: https://api.openalex.org/works?filter=cites:WORK_ID&per_page=100&cursor=*&mailto=your@email.com
- Papers referenced by a work: https://api.openalex.org/works?filter=cited_by:WORK_ID&per_page=100&cursor=*&mailto=your@email.com
  NOTE: "cited_by" filter means "works that are cited BY this work" = its references
- Use cursor pagination: &cursor=* for first page, then use next_cursor from response

=== OUTPUT FORMAT ===

Save as citation_data.json with this exact structure:

{{{{
  "author": {{{{
    "name": "...",
    "openalex_id": "...",
    "institution": "...",
    "total_citations": N,
    "h_index": N,
    "works_count": N
  }}}},
  "nodes": [
    {{{{
      "id": "W1234567890",          // OpenAlex work ID (just the W number)
      "title": "...",
      "authors": "First Author et al.",
      "year": 2024,
      "date": "2024-03-15",          // publication_date from OpenAlex, or null
      "cited_by_count": 215,
      "venue": "Nature",
      "doi": "https://doi.org/...",
      "url": "https://openalex.org/W...",
      "type": "author"               // "author" | "citing" | "reference" | "level2"
    }}}}
  ],
  "edges": [
    {{{{
      "from": "W111",    // the citing paper
      "to": "W222"       // the cited paper
    }}}}
  ],
  "metadata": {{{{
    "depth": {DEPTH},
    "fetched_at": "2026-03-30T12:00:00",
    "total_nodes": N,
    "total_edges": N,
    "min_citations_for_expansion": {MIN_CITATIONS_FOR_EXPANSION}
  }}}}
}}}}

=== STEPS ===

1. Fetch author profile info
   - Print: "Author: [name], [institution], [citations] citations, h-index [N]"

2. Fetch ALL works by this author (level 0)
   - Type: "author"
   - For each: id, title, authors, year, date, cited_by_count, venue, doi, url
   - Print: "Found [N] author works"
   - Print each work title and citation count

3. For each author work, fetch citing papers (level 1 — "citing")
   - These are papers that cite the author's work
   - Edge: from citing_paper to author_work
   - Use cursor pagination for complete results
   - Print progress: "  Fetching citers for: [title]... [N] found"

4. For each author work, get referenced papers (level 1 — "reference")
   - Use the "referenced_works" field from the work object — this is a list
     of OpenAlex IDs already included in the works response. No extra API
     call needed for the IDs, but you DO need to fetch each work's metadata
     (title, year, etc.) in bulk.
   - Bulk fetch: https://api.openalex.org/works?filter=openalex:W1|W2|W3&per_page=100
     (pipe-separated list of IDs, up to 50 per request)
   - Edge: from author_work to referenced_paper
   - Print progress: "  Fetching references for: [title]... [N] found"

5. Skip level 2 if DEPTH == 1. Only do level 2 if DEPTH >= 2.

6. Deduplicate:
   - Nodes: use OpenAlex work ID as unique key
   - Edges: deduplicate by (from, to) pair
   - If a node appears at multiple levels, keep the "closest" type
     (author > citing/reference > level2)

7. Save citation_data.json
   - Print: "Saved citation_data.json ([N] nodes, [M] edges)"

8. Also save citations.csv with columns:
   title, authors, year, date, citation_count, venue, doi, url, type, cited_papers
   (cited_papers = semicolon-separated titles of which author papers it cites)

9. Print final summary:
   - Author profile info
   - Number of author works
   - Number of citing papers
   - Number of referenced papers
   - Total unique nodes and edges
   - Expected vs actual coverage

=== CRITICAL: LOGGING ===

Your code MUST print progress at every step. The user needs to see what's
happening because this can take minutes. Specifically:
- Print before each API call: what you're fetching
- Print after each API call: how many results
- Print a running total every 10 papers processed
- Print any errors immediately
- Print timing: how long the whole thing took

Example output the user should see:
  "Fetching author profile..."
  "Author: Niklas Kempynck, KU Leuven, 230 citations"
  "Fetching 18 author works..."
  "  1. Cell-type-directed design of synthetic enhancers (144 citations)"
  "  2. Enhancer-driven cell type comparison... (33 citations)"
  "Fetching citing papers for 18 works..."
  "  [1/18] Cell-type-directed design... → 144 citers"
  "  [2/18] Enhancer-driven cell type... → 33 citers"
  "Fetching references for 18 works..."
  "  [1/18] Cell-type-directed design... → 45 references"
  "Total: 450 nodes, 520 edges. Took 2m 15s."

=== IMPORTANT ===

- Be polite: 0.5s delay between API requests
- Use cursor pagination for list endpoints
- NEVER use fake or placeholder data
- Handle None values safely — venue, date, doi can all be None
- Extract the "date" field (publication_date) from each work
- For authors field: use first author + "et al." if multiple authors
- The OpenAlex work ID format is "https://openalex.org/W1234567890" —
  store just "W1234567890" as the node id
- If any API call fails, print the error and continue with the next paper.
  Do not crash the whole script because one request failed.
""",
    output_file="citation_data.json",
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