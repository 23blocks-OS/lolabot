#!/usr/bin/env python3
"""Embed the hero images from assets/hero/ into index.html as data URIs.

Each <img> in index.html whose src is "__ASSET:<file>__" or an already embedded
data URI tagged with data-asset="<file>" is (re)filled from assets/hero/<file>.
Idempotent: run it again after changing an image.
"""
import base64, pathlib, re, sys

root = pathlib.Path(__file__).resolve().parent.parent
html_path = root / "index.html"
hero = root / "assets" / "hero"
html = html_path.read_text(encoding="utf-8")

def data_uri(name: str) -> str:
    p = hero / name
    if not p.is_file():
        sys.exit(f"missing asset: {p}")
    mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
    return f"data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"

# first run: placeholder -> data URI, and tag the img with data-asset
def fill(m):
    name = m.group(1)
    return f'data-asset="{name}" src="{data_uri(name)}"'
html, n1 = re.subn(r'src="__ASSET:([^"]+)__"', fill, html)

# CSS backgrounds: url('__ASSET:<file>__') -> data URI, tagged with data-asset-bg on first run
def fill_bg(m):
    name = m.group(1)
    return f'data-asset-bg="{name}" style="background-image:url(\'{data_uri(name)}\')"'
html, n3 = re.subn(r'style="background-image:url\(\'__ASSET:([^\']+)__\'\)"', fill_bg, html)
def refresh_bg(m):
    name = m.group(1)
    return f'data-asset-bg="{name}" style="background-image:url(\'{data_uri(name)}\')"'
html, n4 = re.subn(r'data-asset-bg="([^"]+)" style="background-image:url\(\'data:image/[^\']+\'\)"', refresh_bg, html)
# later runs: refresh tagged images
def refresh(m):
    name = m.group(1)
    return f'data-asset="{name}" src="{data_uri(name)}"'
html, n2 = re.subn(r'data-asset="([^"]+)" src="data:image/[^"]+"', refresh, html)

n1 += n3; n2 += n4
html_path.write_text(html, encoding="utf-8")
print(f"embedded {n1} new, refreshed {n2}; index.html is {html_path.stat().st_size//1024} KB")
