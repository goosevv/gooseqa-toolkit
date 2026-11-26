# Risk-based test design
- Start with product purpose, users, trust boundaries, data lifecycle and critical journeys. Link each requirement to a source (file, line, documented behavior, or confirmed owner decision).
- P0: material security/data loss/core flow failure; P1: important workflow; P2: minor or edge regression. Explain priority and uncertainty.
- Equivalence partitions, boundary values (below/at/above), state transitions, decision tables, pairwise combinations where justified, positive and negative paths. Avoid combinatorial explosion.
- Each scenario: setup + test data, action, measurable expected outcome, cleanup, level, risk, automation suitability. Avoid circular or tautological assertions.
- Prefer deterministic fixtures, explicit clocks, independent users, test database and idempotent setup. Never use real personal data.
- Coverage matrix: risk -> case -> automation reference -> most recent execution evidence. This is risk coverage, not code coverage. Report them separately.
