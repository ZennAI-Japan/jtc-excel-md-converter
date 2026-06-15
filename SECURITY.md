# Security Policy

## Supported versions

This project is currently in MVP stage. Security fixes should target the default branch and the active release branch when one exists.

## Reporting a vulnerability

Please do not disclose security issues publicly before maintainers have had time to assess them.

For now, report suspected vulnerabilities to the maintainers through a private GitHub security advisory or a private maintainer contact channel. When the repository is made public, enable GitHub private vulnerability reporting before announcing it broadly.

## Credential handling

- Never commit `.env`, API keys, tokens, customer files, or private enterprise documents.
- `.env.example` must contain placeholders only.
- The converter must run without AI credentials by default.
- AI provider settings must be explicit and user-controlled.
- Local providers such as Ollama / LM Studio should be usable without API keys when running on the user's machine.

## Document privacy

Enterprise Word/Excel documents may contain confidential information. The default behavior should keep document contents local. Any future feature that sends content to a remote AI provider must clearly show the provider, base URL, model, and opt-in configuration path.

## Maintainer checklist before public release

- Confirm repository visibility can be public.
- Confirm no customer documents, private screenshots, tokens, or generated outputs are committed.
- Enable GitHub private vulnerability reporting.
- Add package publishing credentials only as GitHub Actions secrets, never as repo files.
- Run the full verification gate from `CONTRIBUTING.md`.
