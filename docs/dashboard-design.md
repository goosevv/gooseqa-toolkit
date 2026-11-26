# Dashboard redesign

Design method: [Unslop](https://github.com/heydamir/unslop) by Damir Sokolovsky (CC BY 4.0). Source-level audit: remove decorative gradients, inconsistent glyphs, tracked uppercase headings, cramped fixed sidebar and horizontal navigation. Direction: QA instrument panel; precise, calm, evidence-first; neutral surfaces, existing teal accent, stage progress as the focal point. Keep the original workflow, state and API. Iconify Lucide SVG data embedded locally; see notices in app.js. No runtime CDN or build tooling.

## Verification checklist

- Run `python -m unittest discover -s tests -v` and `node --check static/app.js`.
- Verify root assets and installed skill assets are identical.
- Open a populated demo project and exercise all seven views, theme switching, project selector, modal forms and report download.
- Check 320, 360, 480, 640, 768, 900, 1024 and desktop widths; document root scrollWidth must not exceed clientWidth. Use long paths, project names and test evidence; no horizontally scrolling navigation. Check both themes and keyboard navigation.
- In Codex/ChatGPT, confirm the actual host browser can reach the local URL and stays live. Use fallback if it cannot. The skill instructions do not create an in-app browser API.

Status: source changes prepared; browser rendering, Python/Node tests and real host preview have not been executed in this editing environment. Do not treat the checklist as passed.
