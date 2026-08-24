#!/usr/bin/env python3
"""
Self-hosted replacement for github-readme-stats / streak-stats / top-langs.

Why this exists: those are free shared instances (vercel.app / herokuapp.com
deployments run by one maintainer). When they go down or get rate-limited,
every README pointing at them shows a broken image. This script pulls the
same data straight from the GitHub API and renders it into SVG files that
live IN this repo, committed by the workflow in
.github/workflows/metrics.yml. Nothing in the README depends on a third
party's uptime.

Requires a token with `public_repo` (or `repo`) + `read:user` scopes,
passed as the STATS_TOKEN env var (see SETUP.md for why the default
GITHUB_TOKEN isn't enough).

Usage:
    STATS_TOKEN=xxx GITHUB_USERNAME=omkar273 python3 scripts/generate_cards.py
"""

import os
import sys
import json
import urllib.request
import urllib.error

USERNAME = os.environ.get("GITHUB_USERNAME", "omkar273")
TOKEN = os.environ.get("STATS_TOKEN") or os.environ.get("GITHUB_TOKEN")
API = "https://api.github.com"
ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")

if not TOKEN:
    print("ERROR: STATS_TOKEN (or GITHUB_TOKEN) env var is required.", file=sys.stderr)
    sys.exit(1)


def gh(path, method="GET", body=None, accept="application/vnd.github+json"):
    url = path if path.startswith("http") else f"{API}{path}"
    req = urllib.request.Request(url, method=method)
    req.add_header("Authorization", f"Bearer {TOKEN}")
    req.add_header("Accept", accept)
    req.add_header("User-Agent", f"{USERNAME}-profile-metrics")
    data = json.dumps(body).encode() if body else None
    try:
        with urllib.request.urlopen(req, data=data, timeout=30) as resp:
            headers = dict(resp.headers)
            return json.loads(resp.read().decode()), headers
    except urllib.error.HTTPError as e:
        print(f"GitHub API error {e.code} on {url}: {e.read().decode()}", file=sys.stderr)
        raise


def gh_paginated(path):
    items = []
    page = 1
    while True:
        chunk, _ = gh(f"{path}{'&' if '?' in path else '?'}per_page=100&page={page}")
        if not chunk:
            break
        items.extend(chunk)
        if len(chunk) < 100:
            break
        page += 1
    return items


def gh_graphql(query, variables):
    body, _ = gh("/graphql", method="POST", body={"query": query, "variables": variables})
    if "errors" in body:
        print(f"GraphQL errors: {body['errors']}", file=sys.stderr)
    return body.get("data", {})


def collect_stats():
    user, _ = gh(f"/users/{USERNAME}")
    repos = gh_paginated(f"/users/{USERNAME}/repos?type=owner")
    owned = [r for r in repos if not r["fork"]]

    total_stars = sum(r["stargazers_count"] for r in owned)
    total_forks = sum(r["forks_count"] for r in owned)

    query = """
    query($login: String!) {
      user(login: $login) {
        contributionsCollection {
          totalCommitContributions
          restrictedContributionsCount
        }
        repositoriesContributedTo(first: 1) { totalCount }
        pullRequests(first: 1) { totalCount }
        issues(first: 1) { totalCount }
      }
    }
    """
    data = gh_graphql(query, {"login": USERNAME})
    gql_user = data.get("user", {}) or {}
    contrib = gql_user.get("contributionsCollection", {}) or {}
    commits_this_year = contrib.get("totalCommitContributions", 0) + contrib.get(
        "restrictedContributionsCount", 0
    )

    lang_bytes = {}
    for r in owned:
        try:
            langs, _ = gh(f"/repos/{USERNAME}/{r['name']}/languages")
        except Exception:
            continue
        for lang, n in langs.items():
            lang_bytes[lang] = lang_bytes.get(lang, 0) + n

    return {
        "followers": user.get("followers", 0),
        "public_repos": user.get("public_repos", 0),
        "total_stars": total_stars,
        "total_forks": total_forks,
        "commits_this_year": commits_this_year,
        "prs": (gql_user.get("pullRequests") or {}).get("totalCount", 0),
        "issues": (gql_user.get("issues") or {}).get("totalCount", 0),
        "repos_contributed_to": (gql_user.get("repositoriesContributedTo") or {}).get(
            "totalCount", 0
        ),
        "lang_bytes": lang_bytes,
    }


# ---------------------------------------------------------------------------
# SVG rendering — small, dependency-free, monospace terminal look to match
# the README. Two palettes so the picture/source dark|light switch works.
# ---------------------------------------------------------------------------

PALETTES = {
    "dark": {"bg": "#0d1117", "border": "#30363d", "text": "#c9d1d9", "dim": "#8b949e", "accent": "#39d353"},
    "light": {"bg": "#ffffff", "border": "#d0d7de", "text": "#1f2328", "dim": "#57606a", "accent": "#2da44e"},
}

LANG_COLORS = {
    "Go": "#00ADD8", "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "Python": "#3572A5",
    "Java": "#b07219", "Dart": "#00B4AB", "HTML": "#e34c26", "CSS": "#563d7c",
    "Shell": "#89e051", "Dockerfile": "#384d54", "Makefile": "#427819", "Rust": "#dea584",
}
DEFAULT_LANG_COLOR = "#8b949e"


def esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def stat_card_svg(stats, theme):
    p = PALETTES[theme]
    rows = [
        ("followers", stats["followers"]),
        ("public repos", stats["public_repos"]),
        ("total stars", stats["total_stars"]),
        ("total forks", stats["total_forks"]),
        ("commits (last yr)", stats["commits_this_year"]),
        ("pull requests", stats["prs"]),
    ]
    width, row_h, top_pad = 420, 28, 56
    height = top_pad + row_h * len(rows) + 20

    lines = []
    for i, (label, value) in enumerate(rows):
        y = top_pad + i * row_h
        lines.append(
            f'<text x="24" y="{y}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" '
            f'font-size="14" fill="{p["dim"]}">{esc(label)}</text>'
        )
        lines.append(
            f'<text x="{width - 24}" y="{y}" text-anchor="end" '
            f'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="14" '
            f'font-weight="600" fill="{p["text"]}">{esc(value)}</text>'
        )

    return f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="GitHub statistics">
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" fill="{p["bg"]}" stroke="{p["border"]}"/>
  <text x="24" y="32" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="13" fill="{p["accent"]}">$ gh stats --user {esc(USERNAME)}</text>
  {"".join(lines)}
</svg>'''


def top_langs_svg(stats, theme, top_n=6):
    p = PALETTES[theme]
    langs = sorted(stats["lang_bytes"].items(), key=lambda kv: kv[1], reverse=True)[:top_n]
    total = sum(n for _, n in langs) or 1

    width, row_h, top_pad = 420, 30, 56
    height = top_pad + row_h * len(langs) + 20
    bar_w = width - 48

    lines = []
    for i, (lang, n) in enumerate(langs):
        pct = n / total * 100
        y = top_pad + i * row_h
        color = LANG_COLORS.get(lang, DEFAULT_LANG_COLOR)
        filled = max(2, bar_w * n / total)
        lines.append(
            f'<text x="24" y="{y}" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" '
            f'font-size="13" fill="{p["text"]}">{esc(lang)}</text>'
        )
        lines.append(
            f'<text x="{width - 24}" y="{y}" text-anchor="end" '
            f'font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="12" '
            f'fill="{p["dim"]}">{pct:.1f}%</text>'
        )
        bar_y = y + 6
        lines.append(f'<rect x="24" y="{bar_y}" width="{bar_w}" height="6" rx="3" fill="{p["border"]}"/>')
        lines.append(f'<rect x="24" y="{bar_y}" width="{filled:.1f}" height="6" rx="3" fill="{color}"/>')

    return f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Most used languages">
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" fill="{p["bg"]}" stroke="{p["border"]}"/>
  <text x="24" y="32" font-family="ui-monospace,SFMono-Regular,Consolas,monospace" font-size="13" fill="{p["accent"]}">$ gh langs --user {esc(USERNAME)}</text>
  {"".join(lines)}
</svg>'''


def write(name, content):
    os.makedirs(ASSETS_DIR, exist_ok=True)
    path = os.path.join(ASSETS_DIR, name)
    with open(path, "w") as f:
        f.write(content)
    print(f"wrote {path}")


def main():
    stats = collect_stats()
    print(json.dumps(stats, indent=2, default=str), file=sys.stderr)
    for theme in ("dark", "light"):
        write(f"card-stats-{theme}.svg", stat_card_svg(stats, theme))
        write(f"top-langs-{theme}.svg", top_langs_svg(stats, theme))


if __name__ == "__main__":
    main()
