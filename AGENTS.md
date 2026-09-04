<!-- telos-sdd:start -->
## Telos workflow

For every Telos project request, invoke the `telos` skill before reading or editing specification or application files. Never edit paths under `telos/` directly; use the Telos CLI and preserve native human approval prompts.

Do not rely on the generated Codex guard or rules until setup is reviewed and trusted. Open `/hooks`, review and trust the repository `.codex` layer, and verify the exact `telos agent-guard --host codex` hook before proceeding. Until that review and trust is complete, treat `.codex/hooks.json` and `.codex/rules/telos.rules` as inactive.
<!-- telos-sdd:end -->
