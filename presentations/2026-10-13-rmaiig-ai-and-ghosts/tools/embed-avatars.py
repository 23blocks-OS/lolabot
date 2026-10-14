#!/usr/bin/env python3
"""Embed avatars into index.html as data URIs.

- S06: the large Lola avatar (assets/lola.png, resized to 512 px) replaces the
  __LOLA_DATA__ placeholder, or the existing data URI on the S06 <img class="avatar">.
- S07: every agent in evidence/avatars/MAP.json (fields name, label, avatar_file)
  is resized to 128 px (Lola 256 px) and written into the JSON block
  <script type="application/json" id="avatars">.

Run from the presentation folder with the lola venv (needs Pillow):
  python3 tools/embed-avatars.py   (needs Pillow)
Idempotent: run it again after changing MAP.json or the avatar files.
"""
import base64, io, json, os, re, sys
from PIL import Image

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX = os.path.join(HERE, "index.html")
LOLA = os.path.join(HERE, "assets", "lola.png")
MAP = os.path.join(HERE, "evidence", "avatars", "MAP.json")
AVDIR = os.path.join(HERE, "evidence", "avatars")


def data_uri(path, size, quality=84):
    im = Image.open(path).convert("RGB")
    w, h = im.size
    s = min(w, h)
    im = im.crop(((w - s) // 2, (h - s) // 2, (w - s) // 2 + s, (h - s) // 2 + s))
    im = im.resize((size, size), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode("ascii")


def main():
    html = open(INDEX, encoding="utf-8").read()

    # S06 Lola
    if os.path.exists(LOLA):
        lola = data_uri(LOLA, 512)
        if "__LOLA_DATA__" in html:
            html = html.replace("__LOLA_DATA__", lola)
        else:
            html = re.sub(r'(<img class="avatar" src=")[^"]*(")', lambda m: m.group(1) + lola + m.group(2), html, count=1)
        print("S06 Lola embedded: %d KB" % (len(lola) // 1024))
    else:
        print("assets/lola.png missing; S06 untouched", file=sys.stderr)

    # S07 wall
    entries = []
    if os.path.exists(MAP):
        m = json.load(open(MAP, encoding="utf-8"))
        agents = m.get("agents", m if isinstance(m, list) else [])
        for a in agents:
            f = a.get("avatar_file") or a.get("avatar") or a.get("file")
            if not f:
                continue
            path = os.path.join(AVDIR, f)
            if not os.path.exists(path):
                print("missing avatar file:", f, file=sys.stderr)
                continue
            name = a.get("name", "")
            lead = name == "pas-lola" or bool(a.get("lead"))
            entries.append({
                "name": name,
                "label": a.get("label", name),
                "kind": a.get("kind", "agent"),
                "lead": lead,
                "avatar": data_uri(path, 256 if lead else 128, 82),
            })
        # Lola first, then the rest in MAP order
        entries.sort(key=lambda e: 0 if e["lead"] else 1)
    block = '<script type="application/json" id="avatars">' + json.dumps(entries, ensure_ascii=False, separators=(",", ":")) + "</script>"
    html, n = re.subn(r'<script type="application/json" id="avatars">.*?</script>', lambda m: block, html, count=1, flags=re.S)
    if n != 1:
        print("avatars JSON block not found in index.html", file=sys.stderr)
        sys.exit(1)
    open(INDEX, "w", encoding="utf-8").write(html)
    print("S07 wall: %d avatars embedded (%d KB). index.html is %d KB." % (len(entries), len(block) // 1024, len(html.encode("utf-8")) // 1024))


if __name__ == "__main__":
    main()
