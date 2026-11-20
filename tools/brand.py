#!/usr/bin/env python3
"""Pass 1: add logos to finished images without changing them.

Usage:
    python3 tools/brand.py posts/<job>/brand.yaml

Every image keeps its own proportions, crop and content. The only change is a
logo placed in the emptiest corner (plus, optionally, one line of title text).
Output is for ArtStation and the website, where each image can be any shape.

brand.yaml:
    source: work/<job>-src          # folder of original images
    logo: supercell                 # default logo: supercell | clash | none
    logo_scale: 0.15                # logo width as a fraction of the image's short side
    max_side: 4000                  # longest side of the export, px (never upscaled)
    max_mb: 2.9                     # keep each file under this (upload limit from Claude's session)
    images:                         # optional per-file overrides, by file name
      "Some file.jpg": {logo: clash, pos: bl, scale: 0.3, title: "One line of context"}
      "Other.jpg": {skip: true}

Writes out/<job>/<same file name>.jpg, plus contact-sheet.jpg and placement.txt
(which corner each logo went to, and a warning where no corner was really clear).
"""
import io
import os
import sys

import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGOS = {
    "supercell": {"light": "assets/supercell-white.png", "dark": "assets/supercell-dark.png"},
    "clash": {"light": "assets/clash-logo.png", "dark": "assets/clash-logo.png"},
}
PREFER = {"br": 0.0, "bl": 0.6, "tr": 1.2, "tl": 1.8}  # tie-break: the samples favour bottom-right
BUSY_WARN = 7.0


def busyness(gray, box):
    """How much is going on in a region: contrast plus edges. Flat paper scores near 0."""
    x0, y0, x1, y1 = [int(v) for v in box]
    a = gray[max(0, y0):y1, max(0, x0):x1]
    if a.size == 0:
        return 99.0
    return float(a.std() + np.abs(np.diff(a, axis=1)).mean() * 4 + np.abs(np.diff(a, axis=0)).mean() * 4)


def place_logo(im, name, scale, pos=None):
    """Paste the logo on `im` (RGB). Returns (where, score).

    Looks along all four edges, not only the corners: a corner wins when it is clear,
    otherwise the logo slides along the edge to the nearest clear stretch. If nothing
    is clear at full size it tries a smaller logo before settling.
    """
    W, H = im.size
    short = min(W, H)
    probe = Image.open(os.path.join(ROOT, LOGOS[name]["light"]))
    gray = np.asarray(im.convert("L")).astype(np.float32)
    m = int(short * 0.035)
    best = None
    for shrink in (1.0, 0.8, 0.65):
        lw = int(short * scale * shrink)
        lh = round(probe.height * lw / probe.width)
        clear = int(lw * 0.3)  # breathing room around the logo counts too
        corners = {"tl": (m, m), "tr": (W - m - lw, m), "bl": (m, H - m - lh), "br": (W - m - lw, H - m - lh)}
        if pos:
            cands = [(pos, corners[pos])]
        else:
            step = max(8, lw // 2)
            xs = list(range(m, W - m - lw, step)) + [W - m - lw]
            ys = list(range(m, H - m - lh, step)) + [H - m - lh]
            cands = [("bottom", (x, H - m - lh)) for x in xs] + [("top", (x, m)) for x in xs] \
                + [("left", (m, y)) for y in ys] + [("right", (W - m - lw, y)) for y in ys]
        for label, (x, y) in cands:
            sc = busyness(gray, (x - clear, y - clear, x + lw + clear, y + lh + clear))
            k, d = min(((k, abs(x - cx) + abs(y - cy)) for k, (cx, cy) in corners.items()), key=lambda t: t[1])
            cost = sc + PREFER[k] + 4.0 * d / short + (1 - shrink) * 6
            if best is None or cost < best[0]:
                best = (cost, sc, x, y, lw, lh, k if d < lw else f"{label} edge")
        if pos or best[1] < BUSY_WARN:
            break
    _, sc, x, y, lw, lh, where = best
    lum = gray[y:y + lh, x:x + lw].mean()
    lg = Image.open(os.path.join(ROOT, LOGOS[name]["light" if lum < 140 else "dark"])).convert("RGBA")
    lg = lg.resize((lw, lh), Image.LANCZOS)
    im.paste(lg, (x, y), lg)
    return where, sc


def add_title(im, text):
    """One line of context, top-left, in the same plain style as the user's own sheet titles."""
    W, H = im.size
    short = min(W, H)
    size = max(18, int(short * 0.028))
    try:
        f = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-Medium.otf", size)
    except OSError:
        f = ImageFont.load_default()
    m = int(short * 0.035)
    lum = np.asarray(im.convert("L").crop((m, m, min(W, m + size * 20), m + size * 2))).mean()
    ImageDraw.Draw(im).text((m, m), text, font=f, fill=(20, 20, 24) if lum > 140 else (235, 235, 238))


def save_under(im, path, max_mb):
    """Save as JPEG, lowering quality only as far as needed to fit the size limit."""
    for q in (95, 93, 91, 89, 87, 85, 82, 79, 75):
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=q, subsampling=0 if q >= 89 else 2, optimize=True)
        if buf.tell() <= max_mb * 1024 * 1024:
            break
    with open(path, "wb") as fh:
        fh.write(buf.getvalue())
    return q, buf.tell()


def main(cfg_path):
    cfg = yaml.safe_load(open(cfg_path))
    job = os.path.basename(os.path.dirname(os.path.abspath(cfg_path)))
    src = os.path.join(ROOT, cfg["source"])
    out = os.path.join(ROOT, "out", job)
    os.makedirs(out, exist_ok=True)
    over = cfg.get("images") or {}
    report, thumbs = [], []
    for name in sorted(os.listdir(src)):
        if not name.lower().endswith((".jpg", ".jpeg", ".png")):
            continue
        o = over.get(name) or {}
        if o.get("skip"):
            continue
        im = Image.open(os.path.join(src, name)).convert("RGB")
        orig = im.size
        ms = cfg.get("max_side", 4000)
        if max(im.size) > ms:
            s = ms / max(im.size)
            im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        if o.get("title"):
            add_title(im, o["title"])
        logo = o.get("logo", cfg.get("logo", "supercell"))
        pos, sc = ("-", 0.0)
        if logo != "none":
            default_scale = cfg.get("logo_scale", 0.15) * (2.2 if logo == "clash" else 1)
            pos, sc = place_logo(im, logo, o.get("scale", default_scale), o.get("pos"))
        dst = os.path.splitext(name)[0] + ".jpg"
        q, size = save_under(im, os.path.join(out, dst), cfg.get("max_mb", 2.9))
        warn = "  <-- check: no clear corner" if sc > BUSY_WARN and not o.get("pos") else ""
        report.append(f"{dst}: {orig[0]}x{orig[1]} -> {im.width}x{im.height}, {logo} {pos} "
                      f"(busy {sc:.1f}), q{q}, {size / 1e6:.1f} MB{warn}")
        t = im.copy()
        t.thumbnail((640, 420))
        thumbs.append(t)
    with open(os.path.join(out, "placement.txt"), "w") as fh:
        fh.write("\n".join(report) + "\n")
    print("\n".join(report))
    # contact sheet, 4 across
    cols, cw, ch, g = 4, 640, 420, 14
    rows = -(-len(thumbs) // cols)
    sheet = Image.new("RGB", (cols * cw + (cols + 1) * g, rows * ch + (rows + 1) * g), "#1a1a1d")
    for i, t in enumerate(thumbs):
        x = g + (i % cols) * (cw + g) + (cw - t.width) // 2
        y = g + (i // cols) * (ch + g) + (ch - t.height) // 2
        sheet.paste(t, (x, y))
    sheet.save(os.path.join(out, "contact-sheet.jpg"), quality=88)


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
