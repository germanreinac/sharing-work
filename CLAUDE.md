# sharing-work

This repo is where Claude prepares ready-to-post PNG images (carousels, single posts, stories, slides) from the artwork in the user's Google Drive. The user is a concept and comic artist. Their main project is **Megalith**, a comic with the characters Skit and Dji.

## Where the art lives (Google Drive)

The Google Drive connector is enabled on the user's claude.ai account, so every session can read Drive. No credentials need to live in this repo.

**Main folder: `Claude Experiments` (`13VC4VEh_5k8ke4H5AlcGx2rt8GXFfsDQ`).** This is the user's general folder for Claude, and it has two kinds of subfolder:

- **`0_my projects copy for reference`** is the art library. The user copies whole projects here, one folder per project. It is shared by all their Claude Code projects. Search here for artwork, and treat it as read-only.
- **One folder per Claude Code project, named after the tool.** This repo's folder is `sharing work online`. The others (`sketching tool to spark ideas`, `photoshop tools`, `video editor`) belong to other projects. Leave them alone.

| Folder | Drive ID | What's in it |
| --- | --- | --- |
| Claude Experiments (root) | `13VC4VEh_5k8ke4H5AlcGx2rt8GXFfsDQ` | The art library and the per-tool folders |
| 0_my projects copy for reference | `18Jgg1mVAR2GZ5lJYX7CGdNMCC4EskVk3` | Art library: one folder per project. List it to see which projects are in it now. |
| └ megalith | `1T7NjkzPD1oysEjK3oNw7N5-aWVbk0dpr` | Pages, character and environment concepts, illustrations, logo, ships, sketches, refs, Patreon, pitch |
| **sharing work online** (this repo) | `1dlQnVZyjifqCNbS2TablzSAXC_DdB_lp` | This project's working folder |
| └ new projects to share | `1kCrB311IpK3bx0Rdv_P-jCvflLKQrFft` | Inbox: new work the user wants posted. Check it first when asked what to post. |
| └ style samples | `1JSWqufoC1PpfwFHpuTlgQCAPipIcexo5` | Posts and carousels whose look the user likes. Match their style. |
| └ exports | `199Ax3vgPiBL19Vp2eyjgnfyAhudtPrMM` | Finished work. Holds `presentation video megalith` (`16CPIjctstJgu2oUim8Mcqt6__zKIQKb3`), the 27-slide Megalith deck made in an earlier Claude project to present in artdirection.io: `.refboard` files plus `Board assets` sorted 01 Cold open … 11 What's next. It is the source of the house style. |

Outside the root, `Megalith video` (`1uO6-qMfksXiTyBKQsWXYJm4i2tOAST8S`) holds about 80 curated, captioned Megalith JPGs. They are good for quick picks.

Project folders change as the user adds them, so list them fresh. Don't rely only on this table.

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

## What this project is for

The user loses a lot of time adapting each new piece of work to a template. This repo does that repetitive part for two kinds of output:
1. **Social posts:** Instagram carousels, single posts and stories, later with video.
2. **Virtual board presentations:** slides to present in artdirection.io or a `.refboard`, like the Megalith deck.

Both use the same house style, so the user's work always looks consistent.

## House style and the carousel tool

- `styles/megalith.yaml` holds the colours, font and labels. It is taken from the Megalith presentation board: dark `#1c1b20` background, yellow `#f3d36b` titles, off-white `#e9e6e2` captions, orange `#fd6848` "Behind the scenes" notes, Inter. New projects can get their own style file.
- `posts/<YYYY-MM-DD>-<topic>/post.yaml` describes one post: style, size, slides and caption. Slide types are `cover`, `art`, `pair`, `grid` and `end`. A cover takes `focus`, from 0 (keep the top) to 1 (keep the bottom), to control the crop.
- `python3 tools/carousel.py posts/<folder>/post.yaml` writes `out/<folder>/01.png …`, `caption.txt` and `preview.png`, which shows every slide in a row. Always look at `preview.png` before sending.
- Captions follow the board's voice: short, plain and specific (dates, names), with one "Behind the scenes" line where it adds something. The board notes in `presentation video megalith` are good source text.

## Workflow

1. The user names a project or a topic, such as "character designs for Dji".
2. Find the candidate images in Drive (check `new projects to share` first) and show the user a shortlist before composing.
3. Download them to `work/<topic>/`, write the post file, and render it.
4. Check `preview.png` and fix anything that looks off.
5. Send the PNGs to the user. Upload them to `sharing work online › exports` only if asked.

Never upscale art past its original size. If an image is too small for the format, place it smaller on a background instead.

`work/` holds scratch downloads and stays out of git (see `.gitignore`).
