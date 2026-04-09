"""
Citation Tracker (OpenAlex)
===========================
Fetches recursive citation data from the OpenAlex API for an author,
saves it as structured JSON, and generates a CSV export.

The JSON is the single source of truth — the portal and network graph
(separate HTML files) both read from it.

Usage:
    python run.py                              # interactive: prompts for name
    python run.py "Niklas Kempynck"            # search by name, pick from results
    python run.py --name "..." --id "..."      # skip lookup, use IDs directly
    python run.py --agent                      # force agent mode
    python run.py --script                     # script only, no agent fallback
"""

import argparse
import json
import sys
import urllib.parse
import urllib.request

from selfhealing_agent import Agent

# How many levels deep to go
# Level 0: your papers
# Level 1: papers that cite yours + papers yours reference
DEPTH = 1

# Only expand level 2 for papers with at least this many citations
# Set DEPTH = 2 and adjust this to enable deeper crawling (can be very slow)
MIN_CITATIONS_FOR_EXPANSION = 20


def search_openalex_author(name):
    """Search OpenAlex for an author by name. Returns up to 5 candidates."""
    encoded = urllib.parse.quote(name)
    url = (
        f"https://api.openalex.org/authors"
        f"?search={encoded}&per_page=5&mailto=scholar-citations@tool.com"
    )
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            data = json.loads(resp.read())
        results = data.get("results", [])
        return [
            {
                "id": r["id"].split("/")[-1],
                "name": r.get("display_name", ""),
                "institution": (
                    (r.get("last_known_institutions") or [{}])[0].get("display_name")
                    or "Unknown institution"
                ),
                "works_count": r.get("works_count", 0),
                "cited_by_count": r.get("cited_by_count", 0),
            }
            for r in results
        ]
    except Exception as e:
        print(f"Error searching OpenAlex: {e}")
        return []


def resolve_author(name=None, author_id=None):
    """
    Resolve the author name + OpenAlex ID to use for the run.
    - Both provided  → use them directly.
    - Name only      → search OpenAlex, let user pick.
    - Neither        → prompt for name, then search.
    """
    if name and author_id:
        return name, author_id

    if not name:
        try:
            name = input("Author name: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)
        if not name:
            print("No name provided. Exiting.")
            sys.exit(1)

    print(f"\nSearching OpenAlex for '{name}'...")
    candidates = search_openalex_author(name)

    if not candidates:
        print("No results found. Try a different spelling or pass --id manually.")
        sys.exit(1)

    if len(candidates) == 1:
        c = candidates[0]
        print(
            f"Found: {c['name']}  ·  {c['institution']}"
            f"  ·  {c['works_count']} works  ·  {c['cited_by_count']} citations"
        )
        return c["name"], c["id"]

    print(f"Found {len(candidates)} results:\n")
    for i, c in enumerate(candidates, 1):
        print(f"  [{i}] {c['name']}")
        print(f"      {c['institution']}  ·  {c['works_count']} works  ·  {c['cited_by_count']} citations")
        print(f"      ID: {c['id']}")
        print()

    while True:
        try:
            choice = input(f"Pick an author [1–{len(candidates)}] or q to quit: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            sys.exit(0)
        if choice.lower() == "q":
            sys.exit(0)
        if choice.isdigit() and 1 <= int(choice) <= len(candidates):
            c = candidates[int(choice) - 1]
            return c["name"], c["id"]
        print("Invalid choice, try again.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Citation Tracker (OpenAlex)")
    parser.add_argument("name", nargs="?", help="Author name to search for")
    parser.add_argument("--name", dest="name_flag", metavar="NAME",
                        help="Author name (alternative to positional arg)")
    parser.add_argument("--id", dest="author_id", metavar="OPENALEX_ID",
                        help="OpenAlex author ID, e.g. A5093400185")
    parser.add_argument("--agent", action="store_true", help="Force agent mode")
    parser.add_argument("--script", action="store_true", help="Script only, no agent fallback")
    args = parser.parse_args()

    raw_name = args.name or args.name_flag
    AUTHOR_NAME, OPENALEX_AUTHOR_ID = resolve_author(raw_name, args.author_id)
    print(f"\nUsing: {AUTHOR_NAME}  ({OPENALEX_AUTHOR_ID})\n")

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
  "Author: {AUTHOR_NAME}, [institution], [citations] citations"
  "Fetching author works..."
  "  1. Some Paper Title (144 citations)"
  "Fetching citing papers for N works..."
  "  [1/N] Some Paper Title → 144 citers"
  "Fetching references for N works..."
  "  [1/N] Some Paper Title → 45 references"
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

    if args.agent:
        agent.run_agent_only()
    elif args.script:
        agent.run_script_only()
    else:
        agent.run()
