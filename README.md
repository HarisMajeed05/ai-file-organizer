# AI Smart File Organizer (local + Groq)

Watches folders on your PC (subfolders included), reads file contents, renames files and sorts them into approved folders.

## Setup
From the project root:
```
conda env create -f environment.yml
conda activate ai-file-organizer
cd helper
copy .env.example .env        (Windows)   |   cp .env.example .env
```
1. Put your key in `helper/.env` as `GROQ_API_KEY`.
2. Add your folders to `helper/config.yaml` under `watch_paths`.
3. Run: `python -m app.watcher`

The conda env installs Python 3.12, `ffmpeg` (for video) and everything in `helper/requirements.txt`.
To update an existing env after changing requirements: `conda env update -f environment.yml --prune`

`dry_run` is `true` by default. It only writes a log of what it would do. Check `<watched folder>/Organized/organizer_log.csv`, then set `dry_run: false`.

## Output
`<watched folder>/Organized/<Category>/<Subcategory>/<New_Name.ext>`
Unsure, duplicate, oversized, or executable files go to `Organized/Needs_Review/`.

## Undo
`python -m app.undo "C:/path/to/watched/folder"`

## Safety rules
- Nothing is deleted.
- Folders that look like software projects (contain `.git`, `package.json`, etc.) are skipped. Change `project_markers` to adjust.
- `node_modules`, `venv`, hidden files, temp downloads and the `Organized` folder are skipped.
- The model can only choose from the approved category list.
- Executables are never run or sent to AI. Archives are only listed, never extracted.
- `allow_external_ai: false` sends nothing to Groq.

## Models
Set in `.env`. Groq changes its model list often, so check https://console.groq.com/docs/models if a call fails.
Default `qwen/qwen3.8-27b` handles text and images. Audio uses `whisper-large-v3-turbo`.
Video needs `ffmpeg` (included in the conda env). `.rar` listing needs an `unrar` tool on your PC, otherwise those files go to Needs_Review.
