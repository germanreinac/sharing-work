#!/usr/bin/env python3
"""Pass 1: add logos to finished images without changing them.

Usage:
    python3 tools/brand.py posts/<job>/brand.yaml

Every file keeps its own proportions, crop, content and format: a JPG/PNG comes out
as a JPG, a GIF as a GIF, a video as an MP4. The only change is the logos, each placed
in the emptiest spot along the edges (plus, optionally, one line of title text on stills).
Output is for ArtStation and the website, where each image can be any shape.

brand.yaml:
    source: work/<job>-src          # folder of originals
    logos: [lockup]                 # lockup = Clash of Clans + Supercell side by side (default).
                                    # Or list supercell / clash separately; the first gets the best spot.
    logo_scale: 0.11                # Supercell width as a fraction of the short side
                                    # (other logos and the lockup are sized to the same height)
    max_side: 4000                  # longest side of the export, px (never upscaled)
    max_mb: 2.9                     # keep each file under this (upload limit from Claude's session)
    images:                         # optional per-file overrides, by file name
      "Some file.jpg": {pos: {supercell: bl, clash: br}, scale: 0.12, title: "One line of context"}
      "Other.jpg": {logos: [supercell]}
      "Third.jpg": {skip: true}

Writes out/<job>/<same file name>, plus contact-sheet.jpg and placement.txt.
"""
import io
import os
import subprocess
import sys
import tempfile

import numpy as np
import yaml
from PIL import Image, ImageDraw, ImageFont, ImageSequence

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGOS = {
    "supercell": {"light": "assets/supercell-white.png", "dark": "assets/supercell-dark.png"},
    "clash": {"light": "assets/clash-logo.png", "dark": "assets/clash-logo.png"},
}
def build_lockups():
    """Clash of Clans + Supercell side by side as one unit, so the two always sit together."""
    os.makedirs(os.path.join(ROOT, "work"), exist_ok=True)
    cl = Image.open(os.path.join(ROOT, "assets/clash-logo.png")).convert("RGBA")
    for tone in ("light", "dark"):
        sc = Image.open(os.path.join(ROOT, LOGOS["supercell"][tone])).convert("RGBA")
        h = 400
        sc2 = sc.resize((round(sc.width * h / sc.height), h), Image.LANCZOS)
        ch = round(h * 1.12)  # the Clash logo has arrows poking out the top, so it runs a little taller
        cl2 = cl.resize((round(cl.width * ch / cl.height), ch), Image.LANCZOS)
        gap = round(h * 0.38)
        im = Image.new("RGBA", (cl2.width + gap + sc2.width, ch), (0, 0, 0, 0))
        im.paste(cl2, (0, 0))
        im.paste(sc2, (cl2.width + gap, ch - h))
        im.save(os.path.join(ROOT, "work", f"lockup-{tone}.png"))
    LOGOS["lockup"] = {"light": "work/lockup-light.png", "dark": "work/lockup-dark.png"}


PREFER = {"br": 0.0, "bl": 0.6, "tr": 1.2, "tl": 1.8}  # tie-break: the samples favour the bottom corners
BUSY_WARN = 7.0
STILL = (".jpg", ".jpeg", ".png")
MOVING = (".gif", ".mp4", ".mov", ".webm")


def busyness(gray, box):
    """How much is going on in a region: contrast plus edges. Flat paper scores near 0."""
    x0, y0, x1, y1 = [int(v) for v in box]
    a = gray[max(0, y0):y1, max(0, x0):x1]
    if a.size == 0:
        return 99.0
    return float(a.std() + np.abs(np.diff(a, axis=1)).mean() * 4 + np.abs(np.diff(a, axis=0)).mean() * 4)


def logo_size(name, short, scale):
    """Supercell is `scale` of the short side wide; every other logo matches its height."""
    sc = Image.open(os.path.join(ROOT, LOGOS["supercell"]["light"]))
    h = short * scale * sc.height / sc.width
    lg = Image.open(os.path.join(ROOT, LOGOS[name]["light"]))
    return int(h * lg.width / lg.height), int(h)


def find_spot(gray, name, scale, pos=None):
    """Find where a logo fits. `gray` is a float luminance array. Returns a dict.

    A corner wins when it is clear; otherwise the logo slides along an edge to the
    nearest clear stretch, and only then is a smaller size tried.
    """
    H, W = gray.shape
    short = min(W, H)
    m = int(short * 0.035)
    best = None
    for shrink in (1.0, 0.8, 0.65):
        lw, lh = logo_size(name, short, scale * shrink)
        clear = int(lh * 0.35)  # breathing room around the logo counts too
        corners = {"tl": (m, m), "tr": (W - m - lw, m), "bl": (m, H - m - lh), "br": (W - m - lw, H - m - lh)}
        if pos:
            cands = [(pos, corners[pos])]
        else:
            step = max(8, lh // 2)
            xs = list(range(m, W - m - lw, step)) + [W - m - lw]
            ys = list(range(m, H - m - lh, step)) + [H - m - lh]
            cands = [("bottom", (x, H - m - lh)) for x in xs] + [("top", (x, m)) for x in xs] \
                + [("left", (m, y)) for y in ys] + [("right", (W - m - lw, y)) for y in ys]
        for label, (x, y) in cands:
            sc = busyness(gray, (x - clear, y - clear, x + lw + clear, y + lh + clear))
            k, d = min(((k, abs(x - cx) + abs(y - cy)) for k, (cx, cy) in corners.items()), key=lambda t: t[1])
            cost = sc + PREFER[k] + 4.0 * d / short + (1 - shrink) * 6
            if best is None or cost < best[0]:
                best = (cost, sc, x, y, lw, lh, k if d < lh else f"{label} edge")
        if pos or best[1] < BUSY_WARN:
            break
    _, sc, x, y, lw, lh, where = best
    lum = gray[y:y + lh, x:x + lw].mean()
    return {"name": name, "x": x, "y": y, "w": lw, "h": lh, "where": where, "busy": sc,
            "file": os.path.join(ROOT, LOGOS[name]["light" if lum < 140 else "dark"])}


def plan_logos(gray, names, scale, pos):
    """Place each logo in turn; a placed logo's area is then off limits to the next."""
    gray = gray.copy()
    spots = []
    for n in names:
        p = pos.get(n) if isinstance(pos, dict) else (pos if n == names[0] else None)
        s = find_spot(gray, n, scale, p)
        spots.append(s)
        pad = int(s["h"] * 0.5)
        y0, y1, x0, x1 = max(0, s["y"] - pad), s["y"] + s["h"] + pad, max(0, s["x"] - pad), s["x"] + s["w"] + pad
        block = gray[y0:y1, x0:x1]
        block[:] = (np.indices(block.shape).sum(axis=0) % 2) * 255  # checkerboard = maximally busy
    return spots


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
    return f"q{q}", buf.tell()


def sample_frames(path, n=10):
    """A few frames of a GIF or video as RGB images, spread over its length."""
    if path.lower().endswith(".gif"):
        frames = [f.convert("RGB") for f in ImageSequence.Iterator(Image.open(path))]
        step = max(1, len(frames) // n)
        return frames[::step]
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-vf", "thumbnail=30", "-vsync", "vfr",
                        "-frames:v", str(n), os.path.join(td, "f%02d.png")], check=True)
        return [Image.open(os.path.join(td, f)).convert("RGB").copy() for f in sorted(os.listdir(td))]


def brand_moving(path, dst, names, scale, pos, max_side, max_mb):
    """Overlay the logos on every frame with ffmpeg. GIF stays GIF; video becomes MP4."""
    frames = sample_frames(path)
    W, H = frames[0].size
    s0 = min(1.0, max_side / max(W, H))
    is_gif = dst.lower().endswith(".gif")
    for s in ([s0 * k for k in (1, 0.85, 0.7, 0.6, 0.5, 0.4)] if is_gif else [s0]):
        w, h = int(W * s) // 2 * 2, int(H * s) // 2 * 2
        stack = np.stack([np.asarray(f.resize((w, h)).convert("L"), dtype=np.float32) for f in frames])
        # where anything moves counts as busy, so a logo never sits over the animation
        gray = stack.mean(axis=0) + stack.std(axis=0) * 6 * (np.indices((h, w)).sum(axis=0) % 2 * 2 - 1)
        spots = plan_logos(np.clip(gray, 0, 255), names, scale, pos)
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", path]
        for sp in spots:
            cmd += ["-i", sp["file"]]
        fc, last = [f"[0:v]scale={w}:{h}:flags=lanczos[b0]"], "b0"
        for i, sp in enumerate(spots, 1):
            fc.append(f"[{i}:v]scale={sp['w']}:{sp['h']}:flags=lanczos[l{i}]")
            fc.append(f"[{last}][l{i}]overlay={sp['x']}:{sp['y']}[b{i}]")
            last = f"b{i}"
        if is_gif:
            fc.append(f"[{last}]split[p1][p2];[p1]palettegen=stats_mode=diff[pal];[p2][pal]paletteuse=dither=sierra2_4a[out]")
            cmd += ["-filter_complex", ";".join(fc), "-map", "[out]", dst]
        else:
            cmd += ["-filter_complex", ";".join(fc), "-map", f"[{last}]", "-map", "0:a?", "-c:v", "libx264",
                    "-crf", "17", "-preset", "slow", "-pix_fmt", "yuv420p", "-c:a", "copy", "-movflags", "+faststart", dst]
        subprocess.run(cmd, check=True)
        if os.path.getsize(dst) <= max_mb * 1024 * 1024 or not is_gif:
            break
    thumb = frames[len(frames) // 2].resize((w, h))
    for sp in spots:
        lg = Image.open(sp["file"]).convert("RGBA").resize((sp["w"], sp["h"]), Image.LANCZOS)
        thumb.paste(lg, (sp["x"], sp["y"]), lg)
    return (W, H), (w, h), spots, thumb


def main(cfg_path):
    cfg = yaml.safe_load(open(cfg_path))
    build_lockups()
    job = os.path.basename(os.path.dirname(os.path.abspath(cfg_path)))
    src = os.path.join(ROOT, cfg["source"])
    out = os.path.join(ROOT, "out", job)
    os.makedirs(out, exist_ok=True)
    over = cfg.get("images") or {}
    max_side, max_mb = cfg.get("max_side", 4000), cfg.get("max_mb", 2.9)
    report, thumbs = [], []
    for name in sorted(os.listdir(src)):
        ext = os.path.splitext(name)[1].lower()
        o = over.get(name) or {}
        if ext not in STILL + MOVING or o.get("skip"):
            continue
        names = o.get("logos", cfg.get("logos", ["lockup"]))
        scale, pos = o.get("scale", cfg.get("logo_scale", 0.11)), o.get("pos")
        path = os.path.join(src, name)
        if ext in MOVING:
            dst = os.path.splitext(name)[0] + (".gif" if ext == ".gif" else ".mp4")
            orig, size, spots, t = brand_moving(path, os.path.join(out, dst), names, scale, pos, max_side, max_mb)
            note, nbytes = "anim", os.path.getsize(os.path.join(out, dst))
        else:
            im = Image.open(path).convert("RGB")
            orig = im.size
            if max(im.size) > max_side:
                s = max_side / max(im.size)
                im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
            if o.get("title"):
                add_title(im, o["title"])
            spots = plan_logos(np.asarray(im.convert("L")).astype(np.float32), names, scale, pos)
            for sp in spots:
                lg = Image.open(sp["file"]).convert("RGBA").resize((sp["w"], sp["h"]), Image.LANCZOS)
                im.paste(lg, (sp["x"], sp["y"]), lg)
            dst = os.path.splitext(name)[0] + ".jpg"
            note, nbytes = save_under(im, os.path.join(out, dst), max_mb)
            size, t = im.size, im.copy()
        where = ", ".join(f"{sp['name']} {sp['where']} ({sp['busy']:.1f})" for sp in spots)
        warn = "  <-- check" if any(sp["busy"] > BUSY_WARN for sp in spots) else ""
        big = "  <-- OVER SIZE LIMIT" if nbytes > max_mb * 1024 * 1024 else ""
        report.append(f"{dst}: {orig[0]}x{orig[1]} -> {size[0]}x{size[1]}, {where}, {note}, {nbytes / 1e6:.1f} MB{warn}{big}")
        t.thumbnail((640, 420))
        thumbs.append(t)
    with open(os.path.join(out, "placement.txt"), "w") as fh:
        fh.write("\n".join(report) + "\n")
    print("\n".join(report))
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
