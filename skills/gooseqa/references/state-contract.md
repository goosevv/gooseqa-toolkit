# Local state contract (v1)
Run the bundled CLI from the target project. `GOOSEQA_DATA` may override the default `.gooseqa` directory; use the same setting for CLI and dashboard. `list` shows projects, IDs and computed gates; `apply ACTION FILE` reads UTF-8 JSON (use `-` for stdin); `report ID` emits Markdown; `serve --port 8766` starts a loopback-only HTTP dashboard. Commands never execute test code automatically. Actual tests are run via the agent's normal shell after scope approval.

All mutations except project require `project_id`. Create records and use returned IDs, not invented IDs. Examples of payloads (replace IDs):

| Action | Additional keys |
| --- | --- |
| project | `name`, `repo` (path or URL), `mode`: LEARN/PAIR/AUTO |
| mode | `mode` |
| note | `stage`: 0–7, `text` |
| risk | `title`, `priority`: P0/P1/P2, `reason` |
| case | `title`, `kind`: UI/API/Unit/Integration/Visual/Desktop/Game/AI, `priority`, `risk_id` optional, `steps`, `expected`, `automation_ref` optional |
| automate | `case_id`, `automation_ref` |
| run | `case_id`, `result`: PASS/FAIL/BLOCKED/SKIPPED, `evidence` (required for PASS/FAIL), `command`, `source`: manual/agent/ci |
| bug | `title`, `severity`: P0/P1/P2, `case_id` optional, `details` |
| bug-status | `id`, `status`: OPEN/CLOSED |
| task | `title`, `details` |
| task-status | `id`, `done`: JSON boolean |
| advance | no additional keys |

Example:
```json
{"name":"BugRepConstruct","repo":"C:/Projects/BugRepConstruct","mode":"LEARN"}
```
Gate 0: discovery note; 1: risks; 2: cases with expected result and P0 risk links; 3: automation plan note; 4: code links for P0 cases and at least one linked test; 5: every P0 case latest PASS with evidence; 6: review note and no open P0 defects; 7: CI/report note. These are record checks, not independent verification. Progress counts completed stages; later evidence can invalidate previously satisfied gates. Never advance based solely on a checkbox. A project with no P0 case cannot meet execution gate; document this limitation rather than fabricate priority.
