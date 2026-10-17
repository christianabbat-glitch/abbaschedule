"""Write downloads.svg: a badge showing release-asset downloads split by platform."""
import json
import os
import urllib.request

repo = os.environ["GITHUB_REPOSITORY"]
token = os.environ.get("GITHUB_TOKEN", "")


def platform(name: str) -> str:
    n = name.lower()
    if n.endswith((".exe", ".msi", ".msix", ".appx")) or "win" in n:
        return "Windows"
    if n.endswith((".dmg", ".pkg")) or "mac" in n or "darwin" in n:
        return "Mac"
    return "Other"


counts = {"Windows": 0, "Mac": 0, "Other": 0}
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
        if rel.get("draft"):
            continue
        for a in rel.get("assets", []):
            counts[platform(a["name"])] += a.get("download_count", 0)
    page += 1

total = sum(counts.values())

# Segments: (text, background colour). "Other" only appears if it has downloads.
segments = [
    ("downloads", "#555"),
    (f"Windows {counts['Windows']:,}", "#0067b8"),
    (f"Mac {counts['Mac']:,}", "#6e6e73"),
]
if counts["Other"]:
    segments.append((f"Other {counts['Other']:,}", "#8a6d3b"))
segments.append((f"total {total:,}", "#2e7d32"))

# Approximate text widths (Verdana 11px ~ 6.8px/char) plus padding.
widths = [int(len(t) * 6.8) + 14 for t, _ in segments]
w = sum(widths)

rects, texts, x = [], [], 0
for (text, colour), sw in zip(segments, widths):
    cx = x + sw / 2
    rects.append(f'<rect x="{x}" width="{sw}" height="20" fill="{colour}"/>')
    texts.append(f'<text x="{cx}" y="15" fill="#010101" fill-opacity=".3">{text}</text>'
                 f'<text x="{cx}" y="14">{text}</text>')
    x += sw

aria = ", ".join(t for t, _ in segments[1:])
svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="20" role="img" aria-label="downloads: {aria}">
<title>downloads: {aria}</title>
<linearGradient id="s" x2="0" y2="100%"><stop offset="0" stop-color="#bbb" stop-opacity=".1"/><stop offset="1" stop-opacity=".1"/></linearGradient>
<clipPath id="r"><rect width="{w}" height="20" rx="3" fill="#fff"/></clipPath>
<g clip-path="url(#r)">
{''.join(rects)}
<rect width="{w}" height="20" fill="url(#s)"/>
</g>
<g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" font-size="11">
{''.join(texts)}
</g>
</svg>
"""
with open("downloads.svg", "w") as f:
    f.write(svg)
print(f"Downloads: {counts} total={total}")
