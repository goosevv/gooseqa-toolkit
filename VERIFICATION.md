# Verification — v0.2.0

Linux container, Python standard library:

- `python -m unittest discover -s tests -v`: 13/13 passed. All 10 original tests plus start/resume preserving mode and notes, detached HTTP launch and reuse with occupied port, browser-open request and fallback (mocked browser).
- `node --check static/app.js`: syntax validation.
- New launch uses loopback HTTP readiness and workspace/version identity. Browser opening is a best-effort OS request, not confirmation of rendering.
- Existing state schema unchanged (version 1). Existing skill installation requires moving old directory to a backup; no overwrite.

Not verified: real Windows detached process behavior, actual Codex/Claude command invocation, visual browser E2E, and long-running sandbox persistence. Previous v0.1 browser smoke was blocked by environment policy. Dashboard mode changes are read by the agent on its next state read, not pushed to the agent. The dashboard records evidence and does not independently execute AI or verify truth of results.

No user repositories modified, no deployments or external API calls by the toolkit.

## GitHub packaging
The above results refer to the original v0.2.0 source archive. Core Python, dashboard assets and test files are imported with identical Git blob hashes. The new installation paths, marketplace manifest and model policy are not yet verified inside a real Codex session. Model policy is advisory instructions; no native model enforcement or measured token savings.
