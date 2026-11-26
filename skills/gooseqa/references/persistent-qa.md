# Persistent QA (runtime 0.4)

Run the bundled qa.py from the target root. All mutations use `apply ACTION -` or a UTF-8 JSON file. Every payload includes `project_id`.

| Action | Additional fields |
| --- | --- |
| checkpoint | status: pending/working/blocked/paused; detail: short description of completed substeps and next action |
| memory | key: architecture/stack/commands/environment/conventions/known_risks/lessons; text; source: verified file or command |
| impact-map | path: exact relative Git path; case_ids: nonempty array of existing case IDs |
| review-result | verdict: ACCEPT/REVISE; method: independent/self-review; reviewer; findings; fingerprint from current list |
| new-cycle | none; only allowed after all 8 stages |

`list` exposes the checkpoint, memory, review fingerprint, saved review and archived cycle evidence. Do not store secrets. Checkpoints are descriptive, not a transactional guarantee for external changes; reconcile actual files before resuming. On advancing a stage a fresh pending checkpoint is saved atomically with the stage. Existing state files remain readable.

`impact PROJECT_ID` proposes FULL or INCREMENTAL, paths, reason and case IDs. A baseline is recorded only when all stages complete and Git is clean (excluding ignored files and .gooseqa records). Without a reviewed baseline, ancestry, or mapping for every changed path, use FULL. Mapping is a claim from the agent, not a dependency analyzer. Revalidate shared code, configs, dependencies, renames, generated assets and indirect effects; use full suite whenever uncertain. Always test P0, newly added/changed cases and prior failures. A new cycle archives old runs; old PASS cannot unlock the new execution gate. Existing risks and cases must be revalidated.

Review requires actual evidence and a current fingerprint. A separate native reviewer must not be the test author. If unavailable, disclose self-review; the runtime does not independently prove agent identity or truth of evidence. Review checks include meaningful assertions, regression sensitivity, isolation, coverage, failures, mock boundaries, negative tests and reproducibility. Record REVISE and remediate, then re-run and record fresh review (at most two corrections per invocation). Gate 6 requires ACCEPT and no open P0 bugs. Evidence modifications invalidate the verdict. Legacy completed states remain readable.

The dashboard displays these records, not live agent execution. No token limits or budget controls are added.
