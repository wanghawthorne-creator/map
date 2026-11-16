# Run, check and deployment status

This repository contains a buildless static evidence viewer. It is a review draft, not a georeferenced navigation map. Python 3.10+ and its standard library are sufficient; no package install, account, API key or map service is needed.

## Build and check

Open a terminal inside the repository folder:

```sh
python -B scripts/qa.py
python -B -m unittest discover -s tests -v
python -B scripts/build_site.py
python -B scripts/check_site.py
```

`qa.py` checks the saved place/source/claim/issue records. It accepts documented unknowns and does not prove real-world accuracy. Use `--report quality/validation.json` to refresh its check receipt. Tests use labelled synthetic mutations, not additional real places or evidence of accuracy.

`build_site.py` combines the source tables into `site/review-data.json`. It checks IDs and source references, rejects private filesystem paths and refuses non-null place coordinates in this review version. It does not geocode, infer locations, copy original images, upload files or grant release approval.

`check_site.py` checks required static files and local HTML/CSS references. It rejects raw image/PDF assets and private directories in `site/`. Authored page screenshots may be placed in `site/assets/screenshots/` after manual review. This convention cannot establish that an image is safe or licensed: screenshots showing private originals must remain outside the repository.

## Browse locally

From the repository folder:

```sh
python -m http.server --bind 127.0.0.1 --directory . 8765
```

Open [the local viewer](http://127.0.0.1:8765/site/) while that server is running. Serve the repository root so links to `README.md`, evidence and case documents resolve. Stop the server with `Ctrl+C` when finished. Opening `index.html` directly as a local file is unsupported because browsers may block its JSON fetch.

The repository version contains material summaries and data, not the three original map images. Selecting an image through the page's local file input displays it in that browser session without an upload. It is not copied into the repository or stored by the application. Review actual browser behavior before claiming this feature was tested.

The researcher's separate local-originals preview, if started by the collaboration session, uses a private loopback server outside this repository. Its image routes are intentionally absent from this package. Adding `?review=1` on a public host does not provide original images. Do not include local originals or screenshots of them in a Git upload merely because the local preview can show them.

## GitHub checks and Pages

`.github/workflows/check.yml` runs the four build/check commands on push, pull requests or manual dispatch. It has read-only repository permission. **It does not publish the website, create a release or enable GitHub Pages.** A local pass does not demonstrate that GitHub Actions has run; confirm the actual run after upload.

The researcher approved uploading the v0.2 draft to the public repository `wanghawthorne-creator/map` after inspecting the proposed contents on 2026-11-16. Original images remain excluded. This approval does not confirm geographic facts, image rights or proficiency, and does not authorize enabling Pages in this upload. Pages has not been enabled by these files.

For a later Pages release, use **Settings → Pages → Build and deployment → Source → GitHub Actions** and add an explicitly reviewed deployment workflow that checks the sources, builds `site/review-data.json` and publishes the chosen static artifact. The artifact must preserve relative documentation/evidence links, or those links must be updated before release. The current `site/` directory is not one of GitHub's branch-source `/` or `/docs` choices, so do not select a nonexistent `/site` branch-source option.

There is no Pages deployment workflow or verified live website URL in this version. After deployment is implemented, record the actual workflow, permissions, commit, URL and verification result rather than treating this plan as a tested deployment.
