# Public Release Checklist

Use this before changing repository visibility from private to public.

## Repository safety

- [ ] `gh repo view --json visibility` is checked and the owner confirms public release.
- [ ] No customer Word/Excel files, screenshots, generated outputs, or private demo artifacts are committed.
- [ ] `.env`, `.env.*`, API keys, tokens, and local credentials are not committed.
- [ ] `.env.example` contains placeholders only.
- [ ] `LICENSE` is present and the chosen license is approved by the maintainer.
- [ ] `README.md`, `CONTRIBUTING.md`, and `SECURITY.md` explain local-first and bring-your-own-AI behavior.

## Verification gate

Run:

```bash
python -m compileall -q src tests scripts
python -m pytest -q
python scripts/smoke_demo_ui.py
git diff --check
```

## AI/privacy gate

- [ ] Converter works with no AI credentials.
- [ ] Local provider configuration works without an API key where appropriate.
- [ ] Provider-specific keys are masked in summaries/log-like output.
- [ ] Any feature that sends document content to a remote API is explicit opt-in.
- [ ] Raw API keys are never rendered in the UI.

## GitHub settings

- [ ] Enable GitHub private vulnerability reporting.
- [ ] Confirm Actions/workflows do not expose secrets to forks.
- [ ] Confirm default branch protection or maintainers' merge policy.
- [ ] Create initial public labels: `bug`, `documentation`, `good first issue`, `help wanted`, `security`, `provider-adapter`.

## Release notes

- [ ] State this is alpha/MVP software.
- [ ] State deterministic conversion works offline.
- [ ] State AI provider support is bring-your-own-key and optional.
- [ ] State enterprise documents may contain confidential data and should be reviewed before upload to any remote provider.
