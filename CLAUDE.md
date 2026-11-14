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
| └ exports | `199Ax3vgPiBL19Vp2eyjgnfyAhudtPrMM` | Where finished PNGs go when the user asks for them in Drive |

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

## Workflow

1. The user names a project or a topic, such as "character designs for Dji".
2. Find the candidate images in Drive and show them a shortlist before composing.
3. Compose with Python and Pillow (already installed). The scripts live in `tools/`.
4. Write the finished PNGs to `out/<YYYY-MM-DD>-<topic>/01.png, 02.png, …`, plus a `caption.txt` holding post text and hashtags.
5. Send the PNGs to the user. Upload them to `sharing work online › exports` only if asked.

Never upscale art past its original size. If an image is too small for the format, place it smaller on a background instead.

`work/` holds scratch downloads and stays out of git (see `.gitignore`).
