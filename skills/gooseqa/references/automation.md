# Automation engineering and review
Use the existing framework where reasonable. Web UI: Playwright TS, `getByRole`, `getByLabel`, explicit test IDs if needed, web-first assertions. API: Playwright request, pytest/httpx, or existing tooling; verify status AND body/schema AND side effects when relevant. Unit: Vitest/Jest, pytest, GDScript headless or existing runner. Desktop: test pure logic/IPC separately and use platform-aware automation for true GUI. AI: deterministic fixtures plus scored evaluation of stochastic outputs, not exact text comparisons. Games: state/physics/economy unit checks plus platform smoke and targeted visual checks.

- Separate fixtures, data and reusable helpers from cases; Page Object only where repetition justifies it.
- No arbitrary sleeps, forced actions, blanket retries, broad catch, skipped assertions or changing expected results to match bugs. Use meaningful wait conditions.
- Verify tests against intended behavior; when safe, demonstrate an intentional isolated regression causes the test to fail. Do not mutate production code for this without permission.
- Mocks test contracts, not real integrations. Label mocked and real tests separately.
- Capture actual runner output, exact test name, exit code, relevant trace/report location, environment and commit. Redact secrets.
- CI: use pinned lockfile, reproducible setup, ephemeral test environment, least privileges, timeouts, artifacts on failure. Do not claim a workflow ran unless evidence exists.

Optional sources: https://playwright.dev/docs/test-agents ; https://playwright.dev/docs/best-practices ; https://github.com/microsoft/playwright-cli ; https://github.com/petrkindlmann/qa-skills . Read and inspect before installing; not bundled dependencies.
