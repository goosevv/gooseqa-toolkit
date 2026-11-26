# Global Codex model policy

This policy belongs to GooseQA Toolkit, not to the target project. Apply it to every Codex invocation, in LEARN, PAIR and AUTO, including resumed sessions. The canonical machine-readable configuration is [codex-model-policy.json](codex-model-policy.json).

| Role | Model | Effort |
|---|---|---|
| Orchestrator | GPT-6.2 Sol | Medium |
| Explorer | GPT-6 Luna | Medium |
| Test Designer | GPT-6.2 Sol | Medium |
| Test Engineer | GPT-6.2 Sol | Medium |
| Visual Analyst | GPT-6.1 Terra | Low |
| Reviewer | GPT-6.2 Sol | Medium |
| Documentation | GPT-6 Luna | Low |
| Test Runner | No AI — deterministic CLI | — |

- Do not use Astra or reasoning effort above Medium.
- BALANCED by default: up to two concurrent subagents; ECO: none; QUALITY: up to four. Profiles affect delegation, not the approved role-to-model mapping.
- Delegate only when a role is needed. Provide relevant files, a narrow task, and a compact output contract; don't duplicate repository exploration.
- In ECO the orchestrator performs tasks itself; report that no dedicated role model was invoked.
- Run tests, parse reports and aggregate statistics with deterministic local tools wherever possible.
- The host must actually expose the requested model and effort. If a model/effort or native delegation is unavailable, disclose the limitation and ask before using a different configuration. Never claim a model ran solely because its name appears in this policy.
- The root model is selected by the host/client; a skill cannot by itself guarantee changing a running session. Check the selected model where possible and tell the user how to select Sol Medium if necessary.
- Claude Code has no model mapping yet; do not apply these OpenAI model IDs to it. A separate Claude policy will be designed later.

Status: approved model mapping and delegation design; native Codex subagent enforcement and client compatibility still require implementation and verification. No token savings have been measured.
