# Universal model routing
The skill creates an advisory plan from global user preferences and an observed host inventory. It never buys API access, launches models by itself or switches the root session.

Default: AUTO routing, BALANCED profile (two concurrent subagents), Medium maximum effort and compatible fallback. ECO=0, QUALITY=4, CUSTOM=0–8, bounded by the host's observed limit. Manual uses exact user model IDs. Original Codex preset preserves the original role/model/effort assignments, excludes Astra and is strict regardless of fallback checkbox. Root model is host-controlled. Settings: `~/.gooseqa/model-settings.json` (override with GOOSEQA_CONFIG). AI Configuration in the dashboard writes the same global file. Never store API keys in it.

```sh
python qa.py model-config
python qa.py model-config-set settings.json
python qa.py model-plan host.json
```
Host contract: Codex, Claude Code, Gemini CLI and generic/local use the same inventory schema; the agent must inspect actual native tools and their model choices. Provider-specific automatic discovery/launch adapters are not implemented. Do not use Codex IDs in other hosts. Unknown capabilities mean no model-specific delegation. Example inventory (invented IDs, not real availability):
```json
{"provider":"generic","delegation":true,"model_selection":true,"max_agents":2,"current_model":"example-balanced","current_classes":["BALANCED"],"current_effort":"medium","models":[{"id":"example-balanced","classes":["BALANCED","REASONING"],"efforts":["low","medium"]},{"id":"example-fast","classes":["FAST"],"efforts":["low"]}]}
```
When unknown: `{"provider":"generic","delegation":false,"model_selection":false,"models":[]}`. Model classes describe observed capabilities, not brand or price. Empty efforts means host-controlled/unverified effort. Disclose unverifiable caps before running. Vision is blocked unless confirmed. The plan marks roles as current, delegate, blocked or cli; status is always planned_not_executed. Record actual tool results separately. The test runner remains deterministic CLI.

## Continuous workflow
In AUTO, start/next runs the eight stages sequentially in the current host invocation. Each stage requires real completion plus satisfied quality gates; re-read mode and model settings between stages. Advance using the validated CLI, resume from saved state, retry a blocker at most twice and stop on unresolved blockers or permission boundaries. LEARN and PAIR pause for actual interaction. No background execution or new permissions are implied. The dashboard does not launch the agent.
