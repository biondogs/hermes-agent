# Twin Tools — M0-4

Three test tools for the estate twin so later steward work can be proven with no real model, bot or secret.

- **mock-model** — OpenAI-compatible chat completions at `http://mock-model:8080/v1`, scripted fixtures per test.
- **fake-telegram** — Bot API subset at `http://fake-telegram:8081`, plus test-only control endpoints.
- **eval-gate** — scoped relay to `glm53` via LiteLLM, off by default, on only for `make eval`.
- **portability scan** — `make scan` baseline listing hard-wired hostnames/paths.

See card t_23b54a15 and ESTATE-REWORK-DESIGN-2026-11-26.md §5.1, §7 M0.
