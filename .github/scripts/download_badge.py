"""Write downloads.svg: release-asset downloads split by platform.

GitHub forgets a file's download count when its release (or the file) is
deleted or re-uploaded. To keep a lifetime total, every asset ever seen is
recorded in a ledger (ledger.json, stored on the `tracker-data` branch so app
uploads to main never touch it). Each asset keeps the highest count seen.

The badge counts testers' downloads: the publishers' own checks (each
computer once downloaded what it had just published, to compare it) are
listed by file name in own-downloads.json, which comes from main with the
page, and counted out here -- never out of the ledger, which keeps every
download. (Publishing checks a file by its fingerprint now, not a download.)
"""
import json
import os
import sys
import urllib.request

repo = os.environ["GITHUB_REPOSITORY"]
token = os.environ.get("GITHUB_TOKEN", "")
ledger_path = sys.argv[1] if len(sys.argv) > 1 else "ledger.json"


def platform(name: str) -> str:
    n = name.lower()
    if n.endswith((".exe", ".msi", ".msix", ".appx")) or "win" in n:
        return "Windows"
    if n.endswith((".dmg", ".pkg")) or "mac" in n or "darwin" in n:
        return "Mac"
    return "Other"


try:
    with open(ledger_path) as f:
        ledger = json.load(f)
except FileNotFoundError:
    ledger = {}

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
            key = str(a["id"])
            prev = ledger.get(key, {}).get("downloads", 0)
            ledger[key] = {
                "release": rel["tag_name"],
                "name": a["name"],
                "downloads": max(prev, a.get("download_count", 0)),
            }
    page += 1

with open(ledger_path, "w") as f:
    json.dump(ledger, f, indent=2, sort_keys=True)
    f.write("\n")

try:
    with open("own-downloads.json") as f:
        own = json.load(f).get("files", {})
except (OSError, ValueError, AttributeError):
    own = {}

by_name = {}
for entry in ledger.values():
    by_name[entry["name"]] = by_name.get(entry["name"], 0) + entry["downloads"]

counts = {"Windows": 0, "Mac": 0, "Other": 0}
for name, downloads in by_name.items():
    counts[platform(name)] += max(0, downloads - int(own.get(name, 0)))
total = sum(counts.values())

segments = [
    ("downloads", "#555"),
    (f"Windows {counts['Windows']:,}", "#0067b8"),
    (f"Mac {counts['Mac']:,}", "#6e6e73"),
]
if counts["Other"]:
    segments.append((f"Other {counts['Other']:,}", "#8a6d3b"))
segments.append((f"total {total:,}", "#2e7d32"))

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
