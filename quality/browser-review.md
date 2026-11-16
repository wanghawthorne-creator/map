# Browser verification / 浏览器验证

Checked locally on 2026-11-16, v0.2. These are implementation checks performed with AI assistance, not geographic accuracy tests or the researcher's independent skill demonstration.

- Local HTTP page loaded and read 1 place, 3 materials and 5 classified exercises.
- Loopback original-review mode loaded the terrain input, 2003px-wide imagery input and 6240px-wide hand-drawn input from separate local-only routes. No original images are included in the Git package.
- Material selection, image zoom to300%, reset controls and the full-image dialog were exercised. Zoom is an image-view function, not georeferencing.
- The ordinary proposed-release page did not set a source URL for the original-image element and displayed source-label summaries instead.
- Browser-local file selection produced a `blob:` image source; removing it restored the summary view. No upload endpoint, storage or tracking is implemented.
- English/Chinese controls and the C05 evidence-pending state were observed; candidate text was synchronized to its bilingual field after review.
- A 390×844 viewport was checked; measured document width was375px (content viewport excluding the scrollbar), without horizontal page overflow. The temporary viewport override was reset.
- The README screenshot shows the ordinary page without originals or private map labels. It is a screenshot of this implementation, not evidence of a verified place or a Pages deployment.

Structural checks and JavaScript syntax checks pass locally. GitHub Actions and GitHub Pages are separate services: no successful remote run or live deployment is claimed here. Source rights, current geography and researcher contribution remain subject to review.
