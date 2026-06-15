# OSS + Bring-Your-Own-AI Roadmap

> **For Hermes / Codex:** Make the project useful as open source software without weakening document privacy. The converter must stay deterministic by default. AI features are optional, explicit, and configured by the user's own provider/API key.

**Goal:** Let any user run the converter locally for Excel/Word enterprise documents and optionally connect their own AI provider, including hosted APIs and local OpenAI-compatible endpoints.

**Architecture:** Keep `converter.py` as the deterministic extraction core. Add AI as a separate optional layer that receives explicit artifacts and returns reviewable Markdown/restructure suggestions. Do not make AI calls from the core converter or local demo unless the user has opted in through config.

**Tech Stack:** Python 3.10+, openpyxl, stdlib env parsing, optional future provider adapters, pytest, Playwright smoke.

---

## Principles

1. **Local-first:** Word/Excel documents stay on the user's machine by default.
2. **Bring your own AI:** Users configure their own OpenAI, Anthropic, Google Gemini, OpenAI-compatible, Ollama, LM Studio, or local gateway settings.
3. **No hardcoded credentials:** Examples and tests must never contain real keys.
4. **Deterministic baseline:** The converter must work without an AI provider.
5. **Reviewable outputs:** AI output should be suggestions or generated artifacts with warnings/evidence, not silent mutation.
6. **Vendor-neutral:** Provider adapters should share a small internal interface.

## Current foundation in this PR

- `.env.example` documents provider settings, with `codex` as the recommended initial hosted API mode.
- `src/jtc_excel_md/ai_config.py` loads and sanitizes provider settings without importing vendor SDKs.
- `src/jtc_excel_md/word_converter.py` adds deterministic `.docx` heading/paragraph/table extraction into the same artifact contract.
- `src/jtc_excel_md/ai_providers.py` defines the optional provider adapter interface and OpenAI-compatible request builder without making network calls from the converter.
- `tests/test_ai_config.py` verifies generic, provider-specific, Codex-first, file-based, and local no-key configuration.
- `tests/test_ai_providers.py` verifies disabled-provider behavior, secret-safe request metadata, and injected HTTP-boundary handling.
- `tests/test_word_converter.py` verifies `.docx` extraction and CLI artifact generation.
- `Dockerfile`, `compose.yaml`, and `scripts/docker_smoke.sh` provide a reproducible Docker CLI runtime for local conversion.
- `.gitignore` excludes `.env` and `.env.*` while keeping `.env.example` tracked.
- `CONTRIBUTING.md`, `SECURITY.md`, and `LICENSE` establish initial OSS hygiene.

## Task 1: Provider adapter interface

**Objective:** Add a vendor-neutral adapter interface without making network calls from the converter.

**Files:**

- Create: `src/jtc_excel_md/ai_providers.py`
- Test: `tests/test_ai_providers.py`

**Acceptance:**

- Define an `AIProvider` protocol or base class with a method such as `rewrite_specification(prompt: str) -> AIResponse`.
- Factory returns disabled provider when `AIConfig.enabled` is false.
- Factory supports `openai-compatible` by preparing request metadata but tests mock the HTTP boundary.

## Task 2: AI-assisted restructuring command

**Objective:** Add a separate command that can use the configured provider on already-generated artifacts.

**Files:**

- Create: `src/jtc_excel_md/ai_restructure.py`
- Modify: `pyproject.toml`
- Test: `tests/test_ai_restructure.py`

**Acceptance:**

- New command reads `book_specification.md` and `extracted.json` from an output directory.
- Without provider config, it exits with a clear message and does not fail the deterministic converter.
- With a fake provider, it writes `ai_restructured_specification.md` and `ai_restructure_warnings.md`.

## Task 3: UI opt-in surface

**Objective:** Show AI status in the local demo without sending data automatically.

**Files:**

- Modify: `src/jtc_excel_md/demo_server.py`
- Test: `tests/test_demo_server.py`

**Acceptance:**

- UI shows `AI支援: 未設定 / ローカル / 外部プロバイダ` based on sanitized config.
- External provider mode includes a privacy notice.
- The page never displays raw API keys.

## Task 4: Public release checklist

**Objective:** Make the repository safe to turn public.

**Files:**

- Create: `docs/public-release-checklist.md`

**Acceptance:**

- Checklist includes secret scan, generated output check, customer-document check, license check, vulnerability reporting, package metadata, and README quickstart.
- Visibility flip is a manual maintainer action, not an automated script.

## Task 5: Packaging and distribution

**Objective:** Let OSS users install the tool predictably.

**Files:**

- Modify: `pyproject.toml`
- Create if needed: GitHub Actions workflow

**Acceptance:**

- Add project URLs, license metadata, authors, and classifiers.
- Keep CI local-equivalent: compileall, pytest, smoke where possible.
- Package publishing remains manual until maintainers approve credentials.
