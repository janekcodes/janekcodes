# Setup

## 1. Create the repo
1. On GitHub: **New repository** → name it exactly `janekcodes` → **Public** → don't add a README/license (this repo has them).
2. In a terminal, from inside this folder:
   ```
   git init -b main
   git add .
   git commit -m "Initial profile"
   git remote add origin https://github.com/janekcodes/janekcodes.git
   git push -u origin main
   ```
   Only run these inside this folder, never from your home directory.

## 2. Turn on the daily heatmap
1. Repo → **Actions** tab → enable workflows if asked.
2. Open **Update contribution heatmap** → **Run workflow**. After ~30 seconds `contrib-heatmap.svg` is replaced with your real data and it refreshes daily after that.
3. Optional, to include private contributions: create a classic Personal Access Token with the `read:user` scope, save it as a repo secret named `PROFILE_TOKEN`, and also enable *Include private contributions on my profile* in your GitHub profile settings.

## 3. Make it yours
- **Tagline / badges:** edit `README.md`.
- **Portrait:** replace `source-photo.png` with another photo, then
  `pip install pillow numpy` and `python scripts/make_portrait.py --crop none`
  (or pass `--crop L,T,R,B` to zoom in on your head and shoulders). Front-facing, good light and a plain background work best.
- **Wordmark:** `python scripts/make_wordmark.py --text JANEK` (letters A–Z, keep it to about 6).
- **Labels:** both scripts accept `--handle` and the portrait also takes `--name`.

Commit and push after regenerating. GitHub caches images for a few minutes, so hard-refresh your profile.
