# sharing-work

This repo is where Claude prepares ready-to-post PNG images (carousels, single posts, stories, slides) from the artwork in the user's Google Drive. The user is a concept and comic artist. Their main project is **Megalith**, a comic with the characters Skit and Dji.

## Where the art lives (Google Drive)

The Google Drive connector is enabled on the user's claude.ai account, so every session can read Drive. No credentials need to live in this repo.

**Main folder: `Claude Experiments` (`13VC4VEh_5k8ke4H5AlcGx2rt8GXFfsDQ`).** This is the user's general folder for Claude. Start every search here. When the user names a project, look for it under this folder first, then search the rest of Drive.

| Folder | Drive ID | What's in it |
| --- | --- | --- |
| Claude Experiments (root) | `13VC4VEh_5k8ke4H5AlcGx2rt8GXFfsDQ` | Megalith, Sketching tool to spark ideas, Video Tools, photoshop tools |
| Megalith | `1-JJqhStkAaRG2BlksDyadWmIB7YjMjGi` | whole project, presentation video, coloring tool |
| Megalith › whole project | `1T7NjkzPD1oysEjK3oNw7N5-aWVbk0dpr` | Pages, character and environment concepts, illustrations, logo, ships, sketches, refs |
| Megalith › presentation video › Board assets | `1FjAh9UyIwOWT0_MvHu5VLmlgALGxsYCc` | Art sorted into story sections, 01 Cold open … 11 What's next |
| Megalith video 3 (board.json + images) | `1uO6-qMfksXiTyBKQsWXYJm4i2tOAST8S` | About 80 curated, captioned JPGs (sketchbook, stickers, page roughs, slide backgrounds) |

Useful Drive calls:
- List a folder: `search_files` with `parentId = '<id>'`.
- Fetch an image: `download_file_content`. The file is saved under `tool-results/` and you can see it. Copy it into `work/` before editing.
- Skip PSD and ABR files. Use JPG or PNG exports.
- Image file names often carry a caption, e.g. `Sketchbook  characters-630.jpg`. The `-NNN` suffix is an ID from the old reference board app.

## Output formats

| Use | Size (px) | Ratio |
| --- | --- | --- |
| Instagram carousel or post (default) | 1080 × 1350 | 4:5 |
| Instagram grid-native | 1080 × 1440 | 3:4 |
| Square post | 1080 × 1080 | 1:1 |
| Story, Reel cover, TikTok | 1080 × 1920 | 9:16 |
| Slides, YouTube, X, LinkedIn link | 1920 × 1080 | 16:9 |

Every slide in a carousel uses the same size. Keep text and faces out of the outer 60 px, and out of the top and bottom 250 px on 9:16.

## Workflow

1. The user names a project or a topic, such as "character designs for Dji".
2. Find the candidate images in Drive and show them a shortlist before composing.
3. Compose with Python and Pillow (already installed). The scripts live in `tools/`.
4. Write the finished PNGs to `out/<YYYY-MM-DD>-<topic>/01.png, 02.png, …`, plus a `caption.txt` holding post text and hashtags.
5. Send the PNGs to the user, and upload them to Drive only if asked.

Never upscale art past its original size. If an image is too small for the format, place it smaller on a background instead.

`work/` holds scratch downloads and stays out of git (see `.gitignore`).
