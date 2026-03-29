"""
Google Scholar Citation Tracker
===============================
Uses the selfhealing-agent package to scrape Google Scholar citations
for a specific author and generate a CSV overview.

First run:  Claude figures out how to scrape the data and writes scrape_scholar.py
Next runs:  Runs scrape_scholar.py directly (no API cost)
If broken:  Agent takes over, reads the script, fixes it

Usage:
    python run.py              # normal: script first, agent fallback
    python run.py --agent      # force agent mode (re-explore everything)
    python run.py --script     # script only, no agent fallback
"""

import argparse

from selfhealing_agent import Agent

# ── Configure your author here ──────────────────────────────────────────────
AUTHOR_NAME = "Niklas Kempynck"
SCHOLAR_PROFILE = "https://scholar.google.com/citations?user=u3ooblkAAAAJ&hl=en"
# Find your user ID: go to your Google Scholar profile, the URL contains ?user=XXXXX
# ─────────────────────────────────────────────────────────────────────────────

agent = Agent(
    name="scholar-citations",
    instructions=f"""\
Scrape Google Scholar to find all articles that cited papers by a specific author
and generate a comprehensive CSV overview.

Author: {AUTHOR_NAME}
Google Scholar profile: {SCHOLAR_PROFILE}

Steps:
1. Get all publications by this author from their Google Scholar profile
2. For each publication, find all articles that cited it
3. Collect for each citing article: title, authors, year, citation count, \
journal/venue, URL, and which paper of the author it cited
4. Remove duplicates (same article may cite multiple papers by the author — \
in that case, combine the cited_papers into a comma-separated list)
5. Save the results as a CSV file

Output file: citations.csv
Columns: title, authors, year, citation_count, venue, url, cited_papers

Also generate a summary file: citations_summary.txt with:
- Total number of unique citing papers
- Top 10 most-cited citing papers
- Breakdown by year (how many citations per year)
- Most common venues/journals

Important technical notes:
- Google Scholar blocks automated requests aggressively
- Try the 'scholarly' Python package first (pip install scholarly) — it has \
built-in handling for Google Scholar's anti-bot measures
- If scholarly doesn't work, try Selenium with random delays (2-5 seconds \
between requests)
- Handle pagination — authors with popular papers can have thousands of citations
- Be patient with rate limits — add delays between requests
- Some citing articles won't have full metadata — include what's available
- Sort the final CSV by year (newest first), then by citation count

Print progress as you go:
- "Fetching publications for [author]..."
- "Found X publications"
- "Fetching citations for: [paper title] (Y citations)..."
- "Page Z of citations for [paper title]..."
- "Total unique citing papers found: N"
""",
    output_file="citations.csv",
    script_file="scrape_scholar.py",
)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Google Scholar Citation Tracker")
    parser.add_argument("--agent", action="store_true", help="Force agent mode (re-explore everything)")
    parser.add_argument("--script", action="store_true", help="Script only, no agent fallback")
    args = parser.parse_args()

    if AUTHOR_NAME == "YOUR NAME HERE":
        print("Please configure your author in run.py first:")
        print("  1. Set AUTHOR_NAME to the author's name")
        print("  2. Set SCHOLAR_PROFILE to their Google Scholar profile URL")
        print("     (go to scholar.google.com, find the profile, copy the URL)")
        exit(1)

    if args.agent:
        agent.run_agent_only()
    elif args.script:
        agent.run_script_only()
    else:
        agent.run()
