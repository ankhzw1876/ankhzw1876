#!/usr/bin/env python3
"""Generate self-contained GitHub profile statistics cards."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen


API_ROOT = "https://api.github.com"
REPOSITORY = os.environ.get("GITHUB_REPOSITORY", "ankhzw1876/ankhzw1876")
USERNAME = REPOSITORY.split("/", 1)[0]
TOKEN = os.environ.get("GITHUB_TOKEN", "")
ASSETS_DIR = Path(__file__).resolve().parents[1] / "assets"
BAR_WIDTH = 416

LANGUAGE_COLORS = {
    "HTML": "#e34c26",
    "Vue": "#41b883",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "CSS": "#563d7c",
    "Python": "#3572A5",
    "Shell": "#89e051",
    "Java": "#b07219",
    "C": "#555555",
    "C++": "#f34b7d",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Other": "#8b949e",
}
FALLBACK_COLORS = ("#a371f7", "#39d353", "#ff7b72", "#79c0ff", "#d2a8ff")


def api_get(path: str, params: dict[str, object] | None = None) -> object:
    url = f"{API_ROOT}{path}"
    if params:
        url = f"{url}?{urlencode(params)}"

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": f"{USERNAME}-profile-stats",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"

    request = Request(url, headers=headers)
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def owned_public_repositories() -> list[dict[str, object]]:
    repositories: list[dict[str, object]] = []
    page = 1
    while True:
        batch = api_get(
            f"/users/{USERNAME}/repos",
            {"type": "owner", "per_page": 100, "page": page, "sort": "updated"},
        )
        if not isinstance(batch, list):
            raise RuntimeError("Unexpected repositories response from GitHub")
        repositories.extend(batch)
        if len(batch) < 100:
            return repositories
        page += 1


def language_color(name: str) -> str:
    if name in LANGUAGE_COLORS:
        return LANGUAGE_COLORS[name]
    digest = hashlib.sha256(name.encode("utf-8")).digest()[0]
    return FALLBACK_COLORS[digest % len(FALLBACK_COLORS)]


def render_stats(public_repos: int, stars: int, followers: int, following: int) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="460" height="165" viewBox="0 0 460 165" role="img" aria-labelledby="title desc">
  <title id="title">{USERNAME} GitHub stats</title>
  <desc id="desc">{public_repos} public repositories, {stars} stars, {followers} followers, following {following}.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0d1117"/>
      <stop offset="1" stop-color="#111c2e"/>
    </linearGradient>
  </defs>
  <rect x="0.5" y="0.5" width="459" height="164" rx="12" fill="url(#bg)" stroke="#30363d"/>
  <text x="22" y="34" fill="#58a6ff" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="18" font-weight="700">{USERNAME}'s GitHub Stats</text>
  <g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif">
    <text x="22" y="78" fill="#8b949e" font-size="13">Public repositories</text>
    <text x="178" y="78" fill="#f0f6fc" font-size="16" font-weight="700">{public_repos}</text>
    <text x="252" y="78" fill="#8b949e" font-size="13">Total stars</text>
    <text x="356" y="78" fill="#f0f6fc" font-size="16" font-weight="700">{stars}</text>
    <text x="22" y="116" fill="#8b949e" font-size="13">Followers</text>
    <text x="178" y="116" fill="#f0f6fc" font-size="16" font-weight="700">{followers}</text>
    <text x="252" y="116" fill="#8b949e" font-size="13">Following</text>
    <text x="356" y="116" fill="#f0f6fc" font-size="16" font-weight="700">{following}</text>
    <text x="22" y="145" fill="#6e7681" font-size="11">Updated automatically every day</text>
  </g>
</svg>
'''


def render_languages(language_bytes: dict[str, int]) -> str:
    ranked_all = sorted(language_bytes.items(), key=lambda item: (-item[1], item[0]))
    if len(ranked_all) > 4:
        ranked = ranked_all[:3] + [("Other", sum(amount for _, amount in ranked_all[3:]))]
    else:
        ranked = ranked_all
    total = sum(language_bytes.values())

    if not ranked or total == 0:
        ranked = [("No code detected", 1)]
        total = 1

    percentages = [(name, amount / total * 100) for name, amount in ranked]
    bar_parts: list[str] = []
    x = 22
    for index, (name, percentage) in enumerate(percentages):
        width = BAR_WIDTH - (x - 22) if index == len(percentages) - 1 else round(BAR_WIDTH * percentage / 100)
        bar_parts.append(
            f'    <rect x="{x}" y="54" width="{max(width, 1)}" height="9" fill="{language_color(name)}"/>'
        )
        x += width

    labels: list[str] = []
    positions = ((28, 91), (238, 91), (28, 124), (238, 124))
    for (name, percentage), (circle_x, baseline) in zip(percentages, positions):
        text_x = circle_x + 13
        percentage_x = 111 if circle_x == 28 else 338
        label = name if len(name) <= 12 else f"{name[:11]}…"
        labels.append(
            f'    <circle cx="{circle_x}" cy="{baseline - 4}" r="5" fill="{language_color(name)}"/>'
            f'<text x="{text_x}" y="{baseline}" fill="#c9d1d9">{label}</text>'
            f'<text x="{percentage_x}" y="{baseline}" fill="#8b949e">{percentage:.1f}%</text>'
        )

    bar_markup = "\n".join(bar_parts)
    label_markup = "\n".join(labels)
    description = ", ".join(f"{name} {percentage:.1f}%" for name, percentage in percentages)

    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="460" height="165" viewBox="0 0 460 165" role="img" aria-labelledby="title desc">
  <title id="title">Most used languages</title>
  <desc id="desc">{description}.</desc>
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#0d1117"/>
      <stop offset="1" stop-color="#111c2e"/>
    </linearGradient>
  </defs>
  <rect x="0.5" y="0.5" width="459" height="164" rx="12" fill="url(#bg)" stroke="#30363d"/>
  <text x="22" y="34" fill="#58a6ff" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="18" font-weight="700">Most Used Languages</text>
  <clipPath id="bar"><rect x="22" y="54" width="416" height="9" rx="4.5"/></clipPath>
  <g clip-path="url(#bar)">
{bar_markup}
  </g>
  <g font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="13">
{label_markup}
  </g>
  <text x="22" y="150" fill="#6e7681" font-family="-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif" font-size="11">Based on public repository code · updated daily</text>
</svg>
'''


def main() -> None:
    profile = api_get(f"/users/{USERNAME}")
    repositories = owned_public_repositories()
    if not isinstance(profile, dict):
        raise RuntimeError("Unexpected user response from GitHub")

    language_bytes: dict[str, int] = {}
    for repository in repositories:
        if repository.get("fork") or repository.get("full_name") == REPOSITORY:
            continue
        languages = api_get(f"/repos/{repository['full_name']}/languages")
        if not isinstance(languages, dict):
            continue
        for language, amount in languages.items():
            language_bytes[str(language)] = language_bytes.get(str(language), 0) + int(amount)

    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    (ASSETS_DIR / "github-stats.svg").write_text(
        render_stats(
            public_repos=int(profile.get("public_repos", len(repositories))),
            stars=sum(int(repository.get("stargazers_count", 0)) for repository in repositories),
            followers=int(profile.get("followers", 0)),
            following=int(profile.get("following", 0)),
        ),
        encoding="utf-8",
    )
    (ASSETS_DIR / "top-languages.svg").write_text(render_languages(language_bytes), encoding="utf-8")


if __name__ == "__main__":
    main()
