#!/usr/bin/env python3
"""
Update the custom terminal SVG using GitHub's official GraphQL API.

GitHub's own contributionCalendar is used instead of a third-party stats API.
The workflow supplies GITHUB_TOKEN, so no personal token needs to be stored.
"""

import json
import os
import re
import urllib.request
from datetime import date, timedelta
from pathlib import Path

USERNAME = os.environ.get("GITHUB_USERNAME", "Heet06")
SVG_PATH = Path(os.environ.get("SVG_PATH", "whoami.svg"))
TOKEN = os.environ["GITHUB_TOKEN"]

# GitHub's contribution graph is UTC-based. Ask for a rolling 1-year window,
# matching the period shown by the profile contribution graph.
end = date.today()
start = end - timedelta(days=365)

query = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        totalContributions
        weeks {
          contributionDays {
            date
            contributionCount
          }
        }
      }
    }
  }
}
"""

payload = json.dumps({
    "query": query,
    "variables": {
        "login": USERNAME,
        "from": f"{start.isoformat()}T00:00:00Z",
        "to": f"{end.isoformat()}T23:59:59Z",
    },
}).encode()

request = urllib.request.Request(
    "https://api.github.com/graphql",
    data=payload,
    headers={
        "Authorization": f"Bearer {TOKEN}",
        "Accept": "application/vnd.github+json",
        "Content-Type": "application/json",
        "User-Agent": "Heet06-terminal-stats",
    },
    method="POST",
)

with urllib.request.urlopen(request, timeout=30) as response:
    result = json.load(response)

if result.get("errors"):
    raise RuntimeError("GitHub GraphQL error: " + json.dumps(result["errors"]))

user = result["data"]["user"]
if user is None:
    raise RuntimeError(f"GitHub user not found: {USERNAME}")

calendar = user["contributionsCollection"]["contributionCalendar"]
total = int(calendar["totalContributions"])

days = {}
for week in calendar["weeks"]:
    for day in week["contributionDays"]:
        days[day["date"]] = int(day["contributionCount"])

# Current streak:
# - If today has contributions, include today.
# - Otherwise start from yesterday.
# This avoids showing a zero streak during the current day before a contribution.
cursor = end if days.get(end.isoformat(), 0) > 0 else end - timedelta(days=1)

current = 0
while days.get(cursor.isoformat(), 0) > 0:
    current += 1
    cursor -= timedelta(days=1)

# Longest consecutive run in the same contribution window.
longest = 0
run = 0
cursor = start

while cursor <= end:
    if days.get(cursor.isoformat(), 0) > 0:
        run += 1
        longest = max(longest, run)
    else:
        run = 0
    cursor += timedelta(days=1)

svg = SVG_PATH.read_text(encoding="utf-8")

# Update ONLY the values in the existing git-log block.
replacements = [
    (r'(<text x="370" y="606" class="out">)\d+(</text>)', str(total)),
    (r'(<text x="370" y="632" class="out">)\d+ days(</text>)', f"{current} days"),
    (r'(<text x="370" y="658" class="out">)\d+ days(</text>)', f"{longest} days"),
]

for pattern, replacement in replacements:
    svg, count = re.subn(pattern, rf"\g<1>{replacement}\g<2>", svg, count=1)
    if count != 1:
        raise RuntimeError(f"Expected SVG stat was not found: {pattern}")

SVG_PATH.write_text(svg, encoding="utf-8")

print(
    f"Updated {SVG_PATH}: "
    f"total={total}, current={current} days, longest={longest} days"
)
