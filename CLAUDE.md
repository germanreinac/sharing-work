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

- Pick the style that matches the work: `styles/clash.yaml` for Clash of Clans and Supercell work, `styles/megalith.yaml` for Megalith.
- `styles/clash.yaml` is taken from the Clash samples in `style samples`. Slides are 1080×1440 and use `plate` slides: full-bleed art on a matte that matches the art's own background, film grain, a vignette on dark slides, and one small dated label per slide.
  - `plate` options: `crop`, `rows` (split a wide sheet into stacked strips so it fits a portrait slide), `fill`, `bleed`, `pad`, `label`.
  - Logos, from `assets/`:
    - The Supercell logo goes on every slide in the plainest corner (`logo_pos: auto`), white on dark slides and dark grey on light ones. `supercell-white.png` is the official file from Drive.
    - The cover also carries the Clash of Clans logo (`logo: assets/clash-logo.png`, `logo_width: 360`). It's cut out of the Greedy Raven sample.
    - Keep logos small, so they don't cover the art.
  - Default Clash format: `square-hd` (2160×2160). Use one subject per slide with tight crops, up to 20 slides. Never shrink a whole wide sheet onto one slide. Split it into its characters instead.
  - Extra `plate` options: `erase` (paint out notes and insets, or use `"clone"` on textured backgrounds) and `tight` (auto-trim to the drawing, on by default).
- `styles/megalith.yaml` holds the colours, font and labels. It is taken from the Megalith presentation board: dark `#1c1b20` background, yellow `#f3d36b` titles, off-white `#e9e6e2` captions, orange `#fd6848` "Behind the scenes" notes, Inter. New projects can get their own style file.
- `posts/<YYYY-MM-DD>-<topic>/post.yaml` describes one post: style, size, slides and caption. Slide types are `cover`, `art`, `pair`, `grid` and `end`. A cover takes `focus`, from 0 (keep the top) to 1 (keep the bottom), to control the crop.
- `python3 tools/carousel.py posts/<folder>/post.yaml` writes `out/<folder>/01.png …`, `caption.txt` and `preview.png`, which shows every slide in a row. Always look at `preview.png` before sending.
- Captions follow the board's voice: short, plain and specific (dates, names), with one "Behind the scenes" line where it adds something. The board notes in `presentation video megalith` are good source text.

## Workflow: two kinds of request

Before building anything, work out which kind the request is.

**Option 1: something small and specific, from `new projects to share`.**
The user drops new work into `sharing work online › new projects to share` and asks for a post or slides.
- Use what is in that folder, normally all of it. Ask only if it's unclear which files belong together.
- Take the look from `style samples` and from the house style file, unless the user names a different reference.
- No shortlist step is needed, because the user already chose the images. Build it and show the result.

**Option 2: something bigger, from the art library.**
The user gives parameters (project, theme, character, period, number of slides, format, platform) and asks for a carousel or presentation drawn from `0_my projects copy for reference`.
- Search that project's folders and filter by the parameters. File and folder names, dates and any notes files are the main clues; also look at the images themselves.
- Show the user a shortlist (file names and a one-line reason each) and a proposed slide order before rendering, because here Claude is doing the picking.
- Then build it in the same style.

**For both:**
1. Download the source images to `work/<job>/`, write `posts/<job>/post.yaml` and render.
2. Check `preview.png` and fix anything that looks off.
3. **Export every job to its own folder** in `sharing work online › exports`, named `<YYYY-MM-DD> <topic> (<format>)`, e.g. `2026-11-14 skit-dji-design (instagram carousel)`. Put in it the numbered slides, `caption.txt` and `preview.png`. Nothing goes loose in `exports`. When a job is redone, replace the files in its existing folder instead of making a second one.
4. **Upload limit:** each upload can carry about 3 MB. Export slides as JPEG at quality 95 (`format: jpg` in the style), which comes to about 1.6–2.4 MB at 2160 px. Lossless PNGs at that size don't go through. Drive can't overwrite a file's contents from here, so to redo a job, trash its old files and upload the new ones into the same folder.
   To upload, create the folder with `create_file` (mimeType `application/vnd.google-apps.folder`, parent = exports ID). Then upload each file with `create_file`, setting `base64Content` to `sha256:<hash>:<absolute path>` and `disableConversionToGoogleType: true`.
5. **Add the export to the "sharing work online" board.**
   - Append the export to `boards/sharing-work-online/exports.yaml`: id, title, post, size, Drive folder ID, and the Drive file ID of each slide (from the upload results).
   - Run `python3 tools/board.py`. This rebuilds `boards/sharing-work-online/board.json` with one frame per export, newest on top: the slides in a row, plus the caption and the Drive link as a note.
   - Replace `board.json` in `My Drive › Art Direction › sharing work online` (folder `1pYpl1hOcFN01kkvfQNbpyM1WhThJ9GPB`). Drive can't overwrite a file's contents from here, so trash the old `board.json` (list the folder to find its ID) and upload the new one.
   - `Art Direction` (`1bXt_1l_s2HSq593fpX5Y4Xpv8aLrKbeG`) is where the user's board app keeps its boards, one folder per board.
   - The board's images point at the slides already in `exports` through `driveImages`, so nothing is uploaded twice.
   - The script also writes a `.refboard` (a zip with board.json + images) locally. It is over the 10 MB upload limit, so it stays out of Drive and out of git.
6. Send the user the preview and the link to the Drive folder.

Upscale art only when it would otherwise leave obvious empty space, and by at most 1.5× (`max_upscale`). Otherwise, place it smaller on its matte.

`work/` holds scratch downloads and stays out of git (see `.gitignore`).
