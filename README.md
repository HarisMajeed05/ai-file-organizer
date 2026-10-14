# AI File Organizer

Watches folders on your PC (including subfolders), reads the contents of each file, renames it and sorts it into an approved folder structure. Text, image and audio understanding goes through Groq.

## Setup

From the project root:

```bash
conda env create -f environment.yml
conda activate ai-file-organizer
cd helper
copy .env.example .env     # Windows
cp .env.example .env       # macOS or Linux
```

1. Put your key in `helper/.env` as `GROQ_API_KEY`.
2. Add your folders under `watch_paths` in `helper/config.yaml`.
3. Run `python -m app.watcher`.

The conda environment installs Python 3.12, `ffmpeg` (for video) and everything in `helper/requirements.txt`. To update it after changing the requirements:

```bash
conda env update -f environment.yml --prune
```

## Dry run

`dry_run` is `true` by default. In this mode the tool only writes a log of what it would do. Check `<watched folder>/Organized/organizer_log.csv`, then set `dry_run: false` to apply the changes.

## Output

```
<watched folder>/Organized/<Category>/<Subcategory>/<New_Name.ext>
```

Files that are unsure, duplicates, too large or executable go to `Organized/Needs_Review/`.

## Undo

```bash
python -m app.undo "C:/path/to/watched/folder"
```

## Safety

- Nothing is deleted.
- Folders that look like software projects (they contain `.git`, `package.json` and similar) are skipped. Change `project_markers` to adjust this.
- `node_modules`, `venv`, hidden files, temporary downloads and the `Organized` folder are skipped.
- The model can only pick from the approved category list.
- Executables are never run or sent to the AI. Archives are listed, not extracted.
- Set `allow_external_ai: false` to send nothing to Groq.

## Models

Models are set in `helper/.env`. The example file uses `qwen/qwen3.6-27b` for text and images and `whisper-large-v3-turbo` for audio. Groq changes its model list often, so check the [supported models page](https://console.groq.com/docs/models) if a call fails.

Video needs `ffmpeg`, which is included in the conda environment. To list `.rar` files you need an `unrar` tool on your PC. Without it, those files go to `Needs_Review`.
