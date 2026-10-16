"""Write downloads.svg: a badge showing total release-asset downloads for this repo."""
import json
import os
import urllib.request

repo = os.environ["GITHUB_REPOSITORY"]
token = os.environ.get("GITHUB_TOKEN", "")

total = 0
page = 1
while True:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}/releases?per_page=100&page={page}",
        headers={"Accept": "application/vnd.github+json",
                 **({"Authorization": f"Bearer {token}"} if token else {})},
    )
    releases = json.load(urllib.request.urlopen(req))
    if not releases:
        break
    for rel in releases:
        if not rel.get("draft"):
            total += sum(a.get("download_count", 0) for a in rel.get("assets", []))
    page += 1

label, value = "downloads", f"{total:,}"
# Approximate text widths (Verdana 11px ~ 6.5px/char) plus padding.
lw = int(len(label) * 6.5) + 12
vw = int(len(value) * 7) + 12
w = lw + vw
svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="20" role="img" aria-label="{label}: {value}">
<title>{label}: {value}</title>
<linearGradient id="s" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient>
<clipPath id="r"><rect width="{w}" height="20" rx="3" fill="#fff"/></clipPath>
<g clip-path="url(#r)">
<rect width="{lw}" height="20" fill="#555"/>
<rect x="{lw}" width="{vw}" height="20" fill="#2e7d32"/>
<rect width="{w}" height="20" fill="url(#s)"/>
</g>
<g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">
<text x="{lw / 2}" y="15" fill="#010101" fill-opacity=".3">{label}</text>
<text x="{lw / 2}" y="14">{label}</text>
<text x="{lw + vw / 2}" y="15" fill="#010101" fill-opacity=".3">{value}</text>
<text x="{lw + vw / 2}" y="14">{value}</text>
</g>
</svg>
"""
with open("downloads.svg", "w") as f:
    f.write(svg)
print(f"Total downloads: {total}")
