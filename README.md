<div align="center">

# 🪿 GooseQA Toolkit

**From an unfamiliar codebase to a reliable test suite.**

An AI-assisted QA workflow and local dashboard for learning, writing, running, and reviewing automated tests.

![Version](https://img.shields.io/badge/version-0.2.0-087f73)
![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB)
![Codex](https://img.shields.io/badge/Agent-Codex-18181B)
![Local first](https://img.shields.io/badge/local--first-yes-087f73)

[Install](#installation) · [Quick start](#quick-start) · [Workflow](#workflow) · [Commands](#commands) · [Documentation](#documentation)

</div>

---

## Installation

**Requirements:** Python 3.10+, Git, and Node.js for the skills CLI.

Install globally as a Codex skill:

```sh
npx skills add goosevv/gooseqa-toolkit --skill gooseqa -g -y -a codex
```

<details>
<summary>Alternative installation methods</summary>

**Local installer**

```sh
git clone https://github.com/goosevv/gooseqa-toolkit.git
cd gooseqa-toolkit
python qa.py install-skill codex --global
```

Use `py -3` on Windows or `python3` on Linux/macOS if needed. Replace `--global` with `--project /path/to/project` for project-level installation.

**Codex plugin (experimental)**

```sh
codex plugin marketplace add goosevv/gooseqa-toolkit
```

Install GooseQA Toolkit from the added marketplace in Codex. Native marketplace installation has not yet been verified.

**Claude Code (experimental)**

```sh
python qa.py install-skill claude --global
```

Run `/gooseqa start` inside Claude Code. A separate Claude model policy is planned.

Choose one installation method per agent to avoid duplicate skills.

</details>

## Quick start

Open a target project in Codex and invoke:

```text
$gooseqa start
```

GooseQA creates or resumes the QA workspace, starts a local dashboard, requests browser opening, and guides the agent through the next QA stage.

| Mode | Purpose |
| --- | --- |
| **LEARN** | Guided exercises, hints, and feedback. |
| **PAIR** | Collaborate on test design and implementation. |
| **AUTO** | Delegate an approved testing scope to the agent. |

```text
$gooseqa start LEARN
$gooseqa start PAIR
$gooseqa start AUTO
```

New workspaces default to LEARN. Existing workspaces retain their progress and mode.

## Workflow

```mermaid
flowchart TD
    A[Project discovery] --> B[Risk analysis]
    B --> C[Test design]
    C --> D[Automation plan]
    D --> E[Implementation]
    E --> F[Execution]
    F --> G[Review]
    G --> H[CI & reporting]
```

Choose the right testing level for the project: UI, API, unit, integration, visual, desktop, game, or AI evaluation. Playwright and TypeScript are the recommended starting point for web automation.

## Features

| Capability | Description |
| --- | --- |
| Project analysis | Discover architecture, requirements, risks, and existing coverage. |
| QA dashboard | Track stages, risks, test cases, execution evidence, defects, and learning tasks. |
| Quality gates | Check required records and evidence before advancing stages. |
| Learning mode | Practice automation through real project tasks. |
| Persistent workspace | Resume across agent sessions without losing progress. |
| Local-first runtime | Python standard library, no additional AI API keys or hosted backend. |
| Reporting | Export a Markdown QA report. |

The dashboard refreshes every three seconds, includes light and dark themes, and currently uses a Russian-language interface.

## Commands

| Command | Action |
| --- | --- |
| `$gooseqa start [MODE]` | Start or resume a workspace and open the dashboard. |
| `$gooseqa dashboard` | Open the dashboard. |
| `$gooseqa status` | Inspect progress and blockers. |
| `$gooseqa plan` | Design a risk-based test plan. |
| `$gooseqa next` | Continue the workflow. |
| `$gooseqa run` | Execute relevant tests through the agent. |
| `$gooseqa review` | Review test quality and execution evidence. |
| `$gooseqa report` | Export a QA report. |
| `$gooseqa mode LEARN` | Change the working mode. |

These are skill arguments, not separate built-in Codex commands.

## Model policy

GooseQA includes a shared [Codex model and delegation policy](docs/codex-model-policy.md) for every project and mode. It favors bounded delegation and Medium effort or lower.

The policy is instructional: native subagent orchestration, automatic model switching, and token telemetry are not implemented yet.

## Local data & development

Project state lives in `.gooseqa/state.json`. Keep this directory out of version control and never store credentials or sensitive test data in it. The dashboard binds to loopback only and is not intended for public hosting.

<details>
<summary>Run the dashboard manually or test the toolkit</summary>

From a target project's root, run the installed skill script (example for a global Codex installation):

```sh
python ~/.agents/skills/gooseqa/scripts/qa.py start LEARN
```

If the browser does not open, use the returned dashboard URL. Add `--no-browser` for headless environments.

From the toolkit repository:

```sh
python -m unittest discover -s tests -v
node --check static/app.js
```

</details>

## Documentation

- [Skill instructions](skills/gooseqa/SKILL.md)
- [Automation guidelines](skills/gooseqa/references/automation.md)
- [State contract](skills/gooseqa/references/state-contract.md)
- [Model policy](docs/codex-model-policy.md)
- [Verification and limitations](VERIFICATION.md)

> **Early development:** GooseQA stores and displays test evidence; the agent runs the actual tests. Quality gates validate records, not the correctness of test assertions. Native client installation, Windows behavior, and browser E2E still require verification.

---

<div align="center">

**Learn by testing. Automate with confidence.**

[Report a bug](https://github.com/goosevv/gooseqa-toolkit/issues) · [Suggest an improvement](https://github.com/goosevv/gooseqa-toolkit/issues)

</div>
