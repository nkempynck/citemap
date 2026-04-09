#!/usr/bin/env bash
# Deploy the citation network to GitHub Pages (docs/ folder).
# Run this after run.py, then commit and push.

set -e
cd "$(dirname "$0")"

if [ ! -f citation_data.json ]; then
  echo "Error: citation_data.json not found. Run run.py first."
  exit 1
fi

mkdir -p docs
cp network.html portal.html citation_data.json docs/

echo "docs/ updated."
