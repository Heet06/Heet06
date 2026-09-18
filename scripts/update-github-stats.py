#!/usr/bin/env python3
import json
import os
import re
import urllib.request
from pathlib import Path

USERNAME = os.environ.get("GITHUB_USERNAME", "Heet06")
SVG_PATH = Path(os.environ.get("SVG_PATH", "profile/whoami.svg"))

API_URL = f"https://api.franznkemaka.com/github-streak/stats/{USERNAME}"

req = urllib.request.Request(
    API_URL,
    headers={"User-Agent": "github-terminal-stats-action"},
)

with urllib.request.urlopen(req, timeout=30) as response:
    data = json.load(response)

total = int(data["totalContributions"])
current = int(data["currentStreak"]["days"])
longest = int(data["longestStreak"]["days"])

svg = SVG_PATH.read_text(encoding="utf-8")

# Only replace the numeric values belonging to the git-log block.
patterns = [
    (r'(<text x="370" y="606" class="out">)\d+(</text>)', str(total)),
    (r'(<text x="370" y="632" class="out">)\d+(?: days)?(</text>)', f"{current} days"),
    (r'(<text x="370" y="658" class="out">)\d+(?: days)?(</text>)', f"{longest} days"),
]

for pattern, replacement in patterns:
    svg, count = re.subn(pattern, rf"\g<1>{replacement}\g<2>", svg, count=1)
    if count != 1:
        raise RuntimeError(f"Could not find expected SVG stats pattern: {pattern}")

SVG_PATH.write_text(svg, encoding="utf-8")
print(f"Updated {SVG_PATH}: total={total}, current={current}, longest={longest}")
