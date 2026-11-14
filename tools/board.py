#!/usr/bin/env python3
"""Build the "sharing work online" board from boards/sharing-work-online/exports.yaml.

Usage:
    python3 tools/board.py

Writes, in boards/sharing-work-online/:
    board.json                      the board in the reference-board format (version 1)
                                    used by the user's art-direction board app. Images are
                                    found through "driveImages" (item id -> Drive file id).
    sharing work online.refboard    the same board as a self-contained file (zip with
                                    board.json + images/), for importing by hand.

Layout: one frame per export, newest at the top. Inside each frame the slides sit in
a row, in order, with the caption next to them as a note. Item ids are stable
(export index * 1000 + slide number) so re-running only adds what's new.
"""
import json
import os
import time
import zipfile

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOARD_DIR = os.path.join(ROOT, "boards", "sharing-work-online")

GAP = 60          # between slides
PAD = 160         # inside a frame, around the slides
TITLE = 140       # frame title size
FRAME_GAP = 500   # between frames
NOTE_W = 1400     # width kept for the caption note


def build():
    reg = yaml.safe_load(open(os.path.join(BOARD_DIR, "exports.yaml")))
    exports = reg["exports"]
    items, notes, frames, drive = [], [], [], {}
    y = 0
    # newest export on top
    for n, ex in reversed(list(enumerate(exports, 1))):
        sw, sh = ex.get("size", [1080, 1350])
        sc = 1080 / sw            # show every slide 1080 wide on the board, whatever its pixel size
        w, h = round(sw * sc), round(sh * sc)
        slides = sorted(ex["drive"])
        row_w = len(slides) * w + (len(slides) - 1) * GAP
        fx, fy = 0, y
        fw = PAD + row_w + GAP * 2 + NOTE_W + PAD
        fh = PAD + TITLE + h + PAD
        frames.append({"id": n * 1000, "x": fx, "y": fy, "w": fw, "h": fh, "name": ex["title"],
                       "titleSize": TITLE, "titleBase": TITLE, "level": "body", "font": "Inter", "weight": 600})
        for i, name in enumerate(slides, 1):
            iid = n * 1000 + i
            items.append({"id": iid, "name": f"{ex['id']} {name[:-4]}", "sourceUrl": "",
                          "x": fx + PAD + (i - 1) * (w + GAP), "y": fy + PAD + TITLE,
                          "scaleX": sc, "scaleY": sc, "rotation": 0, "alpha": 1,
                          "file": f"images/{iid}{os.path.splitext(name)[1]}"})
            drive[str(iid)] = ex["drive"][name]
        cap_path = os.path.join(ROOT, "out", ex["id"], "caption.txt")
        caption = open(cap_path).read().strip() if os.path.exists(cap_path) else ""
        notes.append({"id": n * 1000 + 999, "x": fx + PAD + row_w + GAP * 2, "y": fy + PAD + TITLE,
                      "text": caption + f"\n\nDrive folder: https://drive.google.com/drive/folders/{ex['folder']}",
                      "color": "#e9e6e2", "fontSize": 40})
        y += fh + FRAME_GAP

    now = int(time.time() * 1000)
    top = frames[0]
    board = {
        "name": "sharing work online", "created": reg.get("created", now), "updated": now, "changed": now,
        "group": "", "look": {"theme": "dark", "pastel": 1},
        "board": {"format": "reference-board", "version": 1, "items": items, "strokes": [], "notes": notes,
                  "shapes": [], "frames": frames, "palettes": [], "storyboards": [],
                  "layout": {"pane": {"cx": top["x"] + top["w"] / 2, "cy": top["y"] + top["h"] / 2,
                                      "zoom": 0.12, "maximized": False, "type": "board", "state": {}}}},
        "driveImages": drive,
    }
    with open(os.path.join(BOARD_DIR, "board.json"), "w") as fh:
        json.dump(board, fh, ensure_ascii=False)
    print("wrote boards/sharing-work-online/board.json:", len(frames), "frames,", len(items), "slides")

    # self-contained copy: board.json + images/<id>.png from out/
    ref = os.path.join(BOARD_DIR, "sharing work online.refboard")
    with zipfile.ZipFile(ref, "w", zipfile.ZIP_STORED) as z:
        z.writestr("board.json", json.dumps({k: v for k, v in board.items() if k != "driveImages"}, ensure_ascii=False))
        for n, ex in enumerate(exports, 1):
            for i, name in enumerate(sorted(ex["drive"]), 1):
                z.write(os.path.join(ROOT, "out", ex["id"], name), f"images/{n * 1000 + i}{os.path.splitext(name)[1]}")
    print("wrote", os.path.relpath(ref, ROOT), f"({os.path.getsize(ref) // 1024 // 1024} MB)")


if __name__ == "__main__":
    build()
