#!/usr/bin/env python3
"""Render a social-media carousel (numbered PNGs) from a post file.

Usage:
    python3 tools/carousel.py posts/2026-11-14-skit-dji-design/post.yaml

A post file names a style (styles/<name>.yaml), a size and a list of slides.
Slide types (see each method for options):
    cover  - one image filling the frame, with kicker, title and subtitle
    art    - one image, with an optional caption and "Behind the scenes" note
    pair   - two images side by side (or stacked when they're wide), plus text
    grid   - 3 or 4 images in a grid, plus text
    end    - text-only closing slide (title, text, handle)
    plate  - one artwork filling the slide on a matching matte (crop, rows, fill, label)

Output goes to out/<post folder name>/: 01.png, 02.png, …, caption.txt, and
preview.png (all slides in a row, for a quick look).

Artwork is never scaled up past its original size.
"""
import os
import sys

import yaml
from PIL import Image, ImageColor, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

SIZES = {
    "ig-portrait": (1080, 1350),
    "ig-tall": (1080, 1440),
    "square": (1080, 1080),
    "story": (1080, 1920),
    "wide": (1920, 1080),
    # 2x versions for sharper posts (Instagram downsizes, but keeps more detail)
    "square-hd": (2160, 2160),
    "ig-portrait-hd": (2160, 2700),
    "ig-tall-hd": (2160, 2880),
}


def trim(im, matte, threshold=30, margin=0.03):
    """Crop to where the drawing is: pixels that differ clearly from the matte colour."""
    import numpy as np
    small = im.copy()
    small.thumbnail((800, 800))
    a = np.asarray(small).astype(int)
    diff = np.abs(a - np.array(matte)).max(axis=2) > threshold
    # ignore specks: a row/column needs a few marked pixels to count
    cols = np.where(diff.sum(axis=0) > 2)[0]
    rows = np.where(diff.sum(axis=1) > 2)[0]
    if len(cols) == 0 or len(rows) == 0:
        return im
    fx, fy = im.width / small.width, im.height / small.height
    m = int(margin * max(im.width, im.height))
    l, r = max(0, int(cols[0] * fx) - m), min(im.width, int((cols[-1] + 1) * fx) + m)
    t, b = max(0, int(rows[0] * fy) - m), min(im.height, int((rows[-1] + 1) * fy) + m)
    return im.crop((l, t, r, b))

FONT_DIRS = ["/usr/share/fonts/opentype/inter", "/Library/Fonts",
             os.path.expanduser("~/Library/Fonts"), "C:/Windows/Fonts",
             os.path.join(ROOT, "fonts")]


def font(family, weight, size):
    """Find e.g. Inter-SemiBold.otf; fall back to DejaVu if Inter is missing."""
    for d in FONT_DIRS:
        for ext in (".otf", ".ttf"):
            p = os.path.join(d, f"{family}-{weight}{ext}")
            if os.path.exists(p):
                return ImageFont.truetype(p, size)
    bold = weight not in ("Regular", "Medium")
    return ImageFont.truetype("DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf", size)


def wrap(draw, text, fnt, width):
    """Split text into lines that fit `width` pixels."""
    lines = []
    for para in str(text).split("\n"):
        words, line = para.split(), ""
        for w in words:
            test = f"{line} {w}".strip()
            if draw.textlength(test, font=fnt) <= width or not line:
                line = test
            else:
                lines.append(line)
                line = w
        lines.append(line)
    return lines


class Slide:
    def __init__(self, style, size, index, total):
        self.s, self.W, self.H = style, size[0], size[1]
        self.k = self.W / 1080  # scale factor so wide/story sizes stay proportional
        self.m = int(60 * self.k)  # safe margin
        if size == SIZES["story"]:
            self.top_safe, self.bottom_safe = 250, 250
        else:
            self.top_safe, self.bottom_safe = self.m, self.m
        self.img = Image.new("RGB", size, style["colors"]["background"])
        self.d = ImageDraw.Draw(self.img)
        self.index, self.total = index, total
        self.fam = style.get("font", "Inter")

    def f(self, weight, px):
        return font(self.fam, weight, int(px * self.k))

    def c(self, name):
        return self.s["colors"][name]

    # ---------- pieces ----------
    def header(self, light_bg=False):
        """Series label top-left, counter top-right."""
        col = self.c("muted")
        fnt = self.f("SemiBold", 24)
        y = self.top_safe
        self.d.text((self.m, y), self.s.get("series", ""), font=fnt, fill=col)
        cnt = f"{self.index:02d} / {self.total:02d}"
        self.d.text((self.W - self.m - self.d.textlength(cnt, font=fnt), y), cnt, font=fnt, fill=col)
        return y + int(24 * self.k) + int(36 * self.k)

    def text_block(self, caption=None, bts=None, measure=False):
        """Caption (off-white) + Behind the scenes (orange). Returns height."""
        width = self.W - 2 * self.m
        cap_f, bts_lab_f, bts_f = self.f("Medium", 38), self.f("Bold", 22), self.f("Regular", 32)
        gap = int(14 * self.k)
        parts = []
        if caption:
            for ln in wrap(self.d, caption, cap_f, width):
                parts.append((ln, cap_f, self.c("text"), int(50 * self.k)))
        if bts:
            if parts:
                parts.append(("", None, None, int(26 * self.k)))
            parts.append(("BEHIND THE SCENES", bts_lab_f, self.c("accent"), int(34 * self.k)))
            for ln in wrap(self.d, bts, bts_f, width):
                parts.append((ln, bts_f, self.c("accent"), int(43 * self.k)))
        h = sum(p[3] for p in parts)
        if measure or not parts:
            return h + (gap if parts else 0)
        y = self.H - self.bottom_safe - h
        for ln, fnt, col, lh in parts:
            if fnt:
                self.d.text((self.m, y), ln, font=fnt, fill=col)
            y += lh
        return h + gap

    def place(self, path, box, cover=False, focus=0.5):
        """Fit an image into box=(x, y, w, h). Never upscale. Rounded corners."""
        x, y, w, h = box
        im = Image.open(path).convert("RGB")
        if cover:
            s = max(w / im.width, h / im.height)
            im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
            # focus: 0 = keep the top, 0.5 = centre, 1 = keep the bottom
            l, t = (im.width - w) // 2, int((im.height - h) * focus)
            im = im.crop((l, t, l + w, t + h))
        else:
            s = min(w / im.width, h / im.height, 1.0)
            im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
            x, y = x + (w - im.width) // 2, y + (h - im.height) // 2
        r = int(self.s.get("art_radius", 18) * self.k) if not cover else 0
        mask = Image.new("L", im.size, 0)
        ImageDraw.Draw(mask).rounded_rectangle((0, 0, im.width - 1, im.height - 1), r, fill=255)
        self.img.paste(im, (x, y), mask)

    # ---------- plate: one artwork as the whole slide (Clash-style) ----------
    def plate(self, sl):
        """The art fills the slide on a matte that matches the art's own background.

        Options (all optional; boxes are [left, top, right, bottom] fractions of the source image):
          crop:   the region to show
          erase:  list of boxes painted over with the matte first (notes, insets, logos);
                  add "clone" as a 5th value to copy the texture just below instead
          tight:  trim to the drawing itself (default true, from the style), so there's no empty paper
          rows:   cut points (fractions of width) to stack a wide sheet as strips (use sparingly)
          fill:   true = crop to fill the whole slide (good for covers); focus: [x, y] 0..1
          bleed:  "left" / "right" / "bottom" = put a cropped edge flush with the slide edge
          pad:    space around the art, in px at 1080 wide (default from style, 40)
          matte:  a colour, or "auto" (default) = taken from the art's corners
          label:  small text at the bottom-left
          grain:  true/false, overrides the style
        Art is only scaled up when it would otherwise leave empty space, and never past
        the style's max_upscale (default 1.0 = never).
        """
        im = Image.open(sl["image"]).convert("RGB")

        def box(b, img):
            l, t, r, bt = b
            return (int(l * img.width), int(t * img.height), int(r * img.width), int(bt * img.height))

        matte = sl.get("matte", self.s.get("matte", "auto"))
        if matte == "auto":  # median of the four corners
            px = [im.getpixel(p) for p in [(2, 2), (im.width - 3, 2), (2, im.height - 3), (im.width - 3, im.height - 3)]]
            matte = tuple(sorted(c[i] for c in px)[1] for i in range(3))
        elif isinstance(matte, str):
            matte = ImageColor.getrgb(matte)
        for e in sl.get("erase", []):
            bx = box(e[:4], im)
            if len(e) > 4 and e[4] == "clone":  # textured background: copy the patch just below
                h = bx[3] - bx[1]
                im.paste(im.crop((bx[0], bx[3], bx[2], bx[3] + h)), (bx[0], bx[1]))
            else:
                ImageDraw.Draw(im).rectangle(bx, fill=matte)
        if sl.get("crop"):
            im = im.crop(box(sl["crop"], im))
        if sl.get("tight", self.s.get("tight", True)):
            im = trim(im, matte)
        if sl.get("rows"):  # split a wide sheet into strips, stack them
            cuts = [0] + list(sl["rows"]) + [1]
            strips = [im.crop((int(a * im.width), 0, int(b * im.width), im.height)) for a, b in zip(cuts, cuts[1:])]
            w = max(s.width for s in strips)
            gap = int(im.height * 0.04)
            sheet = Image.new("RGB", (w, sum(s.height for s in strips) + gap * (len(strips) - 1)), matte)
            y = 0
            for s in strips:
                sheet.paste(s, ((w - s.width) // 2, y))
                y += s.height + gap
            im = sheet
        self.img.paste(Image.new("RGB", (self.W, self.H), matte))
        label = sl.get("label")
        light = sum(matte) / 3 > 140
        lab_f = self.f("SemiBold", 24)
        lab_h = int(60 * self.k) if label else 0
        if sl.get("fill"):
            fx, fy = sl.get("focus", [0.5, 0.5])
            s = max(self.W / im.width, self.H / im.height)
            im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
            l, t = int((im.width - self.W) * fx), int((im.height - self.H) * fy)
            self.img.paste(im.crop((l, t, l + self.W, t + self.H)), (0, 0))
        else:
            pad = int(sl.get("pad", self.s.get("pad", 40)) * self.k)
            bw, bh = self.W - 2 * pad, self.H - 2 * pad - lab_h
            s = min(bw / im.width, bh / im.height, float(sl.get("max_upscale", self.s.get("max_upscale", 1.0))))
            im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
            x, y = (self.W - im.width) // 2, pad + (bh - im.height) // 2
            bleed = sl.get("bleed")  # push a cropped edge flush to the slide edge
            if bleed == "right":
                x = self.W - im.width
            elif bleed == "left":
                x = 0
            elif bleed == "bottom":
                y = self.H - im.height
            self.img.paste(im, (x, y))
        if sl.get("grain", self.s.get("grain", False)):
            self.add_grain(light)
        if label:
            col = (60, 60, 64) if light else (225, 225, 228)
            self.d = ImageDraw.Draw(self.img)
            self.d.text((self.m, self.H - self.m - int(24 * self.k)), label, font=lab_f, fill=col)
        self.add_logo(sl)

    def add_grain(self, light):
        """Film grain + soft vignette, like the Clash samples."""
        import numpy as np
        a = np.asarray(self.img).astype(np.float32)
        rng = np.random.default_rng(7)
        a += rng.normal(0, 9 if not light else 5, a.shape[:2])[..., None]
        if not light:  # darken the edges a little
            yy, xx = np.mgrid[0:self.H, 0:self.W]
            r = np.sqrt(((xx - self.W / 2) / (self.W / 2)) ** 2 + ((yy - self.H / 2) / (self.H / 2)) ** 2)
            a *= (1 - 0.22 * np.clip(r - 0.55, 0, 1))[..., None]
        self.img = Image.fromarray(np.clip(a, 0, 255).astype("uint8"))
        self.d = ImageDraw.Draw(self.img)

    def add_logo(self, sl):
        """Logo in a corner, like the Clash samples.

        Style or slide keys:
          logo:        one PNG for every background, or
          logo_light / logo_dark: PNGs for dark / light slides (picked from the matte)
          logo_width:  px at 1080 wide
          logo_pos:    tl / tr / bl / br / bottom / auto (default: auto = emptiest corner,
                       skipping the label corner)
          logo_opacity: 0..1
        A slide can turn it off with logo: false.
        """
        if sl.get("logo") is False:
            return
        dark_bg = sum(self.img.resize((1, 1)).getpixel((0, 0))) / 3 < 140
        path = sl.get("logo") or self.s.get("logo") or \
            (sl.get("logo_light", self.s.get("logo_light")) if dark_bg else sl.get("logo_dark", self.s.get("logo_dark")))
        if not path or not os.path.exists(os.path.join(ROOT, path)):
            return
        lg = Image.open(os.path.join(ROOT, path)).convert("RGBA")
        w = int(sl.get("logo_width", self.s.get("logo_width", 110)) * self.k)
        lg = lg.resize((w, round(lg.height * w / lg.width)), Image.LANCZOS)
        op = sl.get("logo_opacity", self.s.get("logo_opacity", 1.0))
        if op < 1:
            lg.putalpha(lg.getchannel("A").point(lambda v: int(v * op)))
        m = self.m
        spots = {"tl": (m, m), "tr": (self.W - m - w, m),
                 "bl": (m, self.H - m - lg.height), "br": (self.W - m - w, self.H - m - lg.height),
                 "bottom": ((self.W - w) // 2, self.H - m - lg.height)}
        pos = sl.get("logo_pos", self.s.get("logo_pos", "auto"))
        if pos == "auto":  # the corner where the slide is plainest
            import numpy as np
            cands = ["br", "tr", "tl"] + ([] if sl.get("label") else ["bl"])
            def busy(k):
                x, y = spots[k]
                a = np.asarray(self.img.crop((x, y, x + w, y + lg.height)).convert("L")).astype(float)
                return a.std() + np.abs(np.diff(a, axis=1)).mean() * 4
            pos = min(cands, key=busy)
        self.img.paste(lg, spots[pos], lg)

    # ---------- slide types ----------
    def cover(self, sl):
        # Measure the text first, so the art can sit above it, not under it.
        width = self.W - 2 * self.m
        title_f, sub_f = self.f("ExtraBold", 96), self.f("Medium", 36)
        n_title = len(wrap(self.d, sl.get("title", ""), title_f, width))
        n_sub = len(wrap(self.d, sl["subtitle"], sub_f, width)) if sl.get("subtitle") else 0
        text_h = (int(48 * self.k) if sl.get("kicker") else 0) + n_title * int(104 * self.k) \
            + (int(18 * self.k) + n_sub * int(48 * self.k) if n_sub else 0)
        art_h = self.H - self.bottom_safe - text_h - int(50 * self.k)
        # Art fills the top part; it runs a little under the fade for a soft edge.
        fade_h = int(220 * self.k)
        self.place(sl["image"], (0, 0, self.W, art_h + fade_h // 2), cover=True, focus=sl.get("focus", 0.5))
        grad = Image.new("L", (1, fade_h))
        for i in range(fade_h):
            grad.putpixel((0, i), int(255 * (i / fade_h) ** 1.2))
        grad = grad.resize((self.W, fade_h))
        shade = Image.new("RGB", (self.W, fade_h), self.c("background"))
        self.img.paste(shade, (0, art_h + fade_h // 2 - fade_h), grad)
        y = self.H - self.bottom_safe
        lines = []
        if sl.get("subtitle"):
            lines += [(l, self.f("Medium", 36), self.c("text"), int(48 * self.k))
                      for l in wrap(self.d, sl["subtitle"], self.f("Medium", 36), self.W - 2 * self.m)]
        title_f = self.f("ExtraBold", 96)
        tl = [(l, title_f, self.c("title"), int(104 * self.k))
              for l in wrap(self.d, sl.get("title", ""), title_f, self.W - 2 * self.m)]
        kick = [(sl["kicker"].upper(), self.f("Bold", 26), self.c("accent"), int(48 * self.k))] if sl.get("kicker") else []
        block = kick + tl + ([("", None, None, int(18 * self.k))] if lines else []) + lines
        y -= sum(b[3] for b in block)
        for ln, fnt, col, lh in block:
            if fnt:
                self.d.text((self.m, y), ln, font=fnt, fill=col)
            y += lh
        if sl.get("swipe", True):
            fnt = self.f("SemiBold", 24)
            t = "SWIPE  →"
            self.d.text((self.W - self.m - self.d.textlength(t, font=fnt), self.top_safe), t, font=fnt, fill=self.c("text"))

    def _art_area(self, sl):
        top = self.header()
        th = self.text_block(sl.get("caption"), sl.get("bts"), measure=True)
        bottom = self.H - self.bottom_safe - th - int(30 * self.k)
        return top, bottom

    def art(self, sl):
        top, bottom = self._art_area(sl)
        self.place(sl["image"], (self.m, top, self.W - 2 * self.m, bottom - top))
        self.text_block(sl.get("caption"), sl.get("bts"))

    def pair(self, sl):
        top, bottom = self._art_area(sl)
        a, b = sl["images"][:2]
        gap = int(24 * self.k)
        w, h = self.W - 2 * self.m, bottom - top
        ims = [Image.open(p) for p in (a, b)]

        def shown_area(bw, bh):  # how much art is visible if each sits in a bw×bh box
            return sum(min(bw / i.width, bh / i.height, 1.0) ** 2 * i.width * i.height for i in ims)

        if shown_area(w, (h - gap) / 2) > shown_area((w - gap) / 2, h):  # stack when that shows more art
            hh = (h - gap) // 2
            self.place(a, (self.m, top, w, hh))
            self.place(b, (self.m, top + hh + gap, w, hh))
        else:
            ww = (w - gap) // 2
            self.place(a, (self.m, top, ww, h))
            self.place(b, (self.m + ww + gap, top, ww, h))
        self.text_block(sl.get("caption"), sl.get("bts"))

    def grid(self, sl):
        top, bottom = self._art_area(sl)
        ims = sl["images"][:4]
        gap = int(20 * self.k)
        w, h = self.W - 2 * self.m, bottom - top
        cw, ch = (w - gap) // 2, (h - gap) // 2
        cells = [(0, 0), (1, 0), (0, 1), (1, 1)]
        if len(ims) == 3:  # big one on top, two below
            self.place(ims[0], (self.m, top, w, ch))
            cells, ims = [(0, 1), (1, 1)], ims[1:]
        for p, (cx, cy) in zip(ims, cells):
            self.place(p, (self.m + cx * (cw + gap), top + cy * (ch + gap), cw, ch))
        self.text_block(sl.get("caption"), sl.get("bts"))

    def end(self, sl):
        self.header()
        width = self.W - 2 * self.m
        block = []
        tf = self.f("ExtraBold", 80)
        block += [(l, tf, self.c("title"), int(92 * self.k)) for l in wrap(self.d, sl.get("title", ""), tf, width)]
        if sl.get("text"):
            block.append(("", None, None, int(28 * self.k)))
            xf = self.f("Medium", 38)
            block += [(l, xf, self.c("text"), int(52 * self.k)) for l in wrap(self.d, sl["text"], xf, width)]
        handle = sl.get("handle", self.s.get("handle"))
        if handle:
            block.append(("", None, None, int(40 * self.k)))
            block.append((handle, self.f("Bold", 34), self.c("accent"), int(46 * self.k)))
        y = (self.H - sum(b[3] for b in block)) // 2
        for ln, fnt, col, lh in block:
            if fnt:
                self.d.text((self.m, y), ln, font=fnt, fill=col)
            y += lh


def render(post_path):
    post_dir = os.path.dirname(os.path.abspath(post_path))
    post = yaml.safe_load(open(post_path))
    style = yaml.safe_load(open(os.path.join(ROOT, "styles", f"{post.get('style', 'megalith')}.yaml")))
    style.update(post.get("style_overrides", {}))
    size = SIZES[post.get("size", "ig-portrait")]
    out = os.path.join(ROOT, "out", os.path.basename(post_dir))
    os.makedirs(out, exist_ok=True)

    def resolve(p):  # image paths are relative to the post file, or to the repo
        for base in (post_dir, ROOT):
            q = os.path.join(base, p)
            if os.path.exists(q):
                return q
        sys.exit(f"Missing image: {p}")

    slides = post["slides"]
    files = []
    for i, sl in enumerate(slides, 1):
        sl = dict(sl)
        if "image" in sl:
            sl["image"] = resolve(sl["image"])
        if "images" in sl:
            sl["images"] = [resolve(p) for p in sl["images"]]
        s = Slide(style, size, i, len(slides))
        getattr(s, sl.get("type", "art"))(sl)
        ext = style.get("format", "png")
        f = os.path.join(out, f"{i:02d}.{ext}")
        if ext == "jpg":
            s.img.convert("RGB").save(f, quality=style.get("quality", 95), subsampling=0, optimize=True)
        else:
            s.img.save(f, optimize=True)
        files.append(f)
        print("wrote", os.path.relpath(f, ROOT))

    if post.get("caption"):
        with open(os.path.join(out, "caption.txt"), "w") as fh:
            fh.write(post["caption"].strip() + "\n")
        print("wrote", os.path.relpath(os.path.join(out, "caption.txt"), ROOT))

    # preview strip: every slide side by side, small
    th = 540
    thumbs = [Image.open(f).resize((round(size[0] * th / size[1]), th), Image.LANCZOS) for f in files]
    gap = 16
    strip = Image.new("RGB", (sum(t.width for t in thumbs) + gap * (len(thumbs) + 1), th + 2 * gap), "#111014")
    x = gap
    for t in thumbs:
        strip.paste(t, (x, gap))
        x += t.width + gap
    strip.save(os.path.join(out, "preview.jpg"), quality=90)
    print("wrote", os.path.relpath(os.path.join(out, "preview.jpg"), ROOT))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    render(sys.argv[1])
