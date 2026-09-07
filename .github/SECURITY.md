# Security policy — FIA Harness repository

> **Not to be confused with `SECURITY.md` at the repository root.** The root
> `SECURITY.md` is a **project template the kit ships**: each project that
> uses FIA Harness copies it and fills in its own security decisions. This
> file (`.github/SECURITY.md`) is the policy for **this repository itself** —
> how to report a vulnerability in the kit.

## Supported versions

| Version | Supported |
|---|---|
| Latest release (v2.x) | ✅ |
| Older releases | ❌ |

This is a best-effort, single-maintainer project. Fixes land on the latest
release; backports are not guaranteed.

## Reporting a vulnerability

Please do **not** open a public issue for security problems. Report them
privately:

1. Go to **Security → Report a vulnerability** in this repository (GitHub
   private vulnerability reporting), or
2. Open a private issue to the maintainer (`mcpedrogm-art`).

Include, if possible:

- Affected file and line / minimal reproduction
- Expected vs actual behavior
- Whether it affects the generated CI workflows of downstream projects

## What this kit is — and the honest limits

FIA Harness is Markdown plus two stdlib-only Python scripts that generate
state, tasks and a CI workflow for **your** project. The enforcement a project
gets (gitleaks, dependency audits, `progress.json` validation) runs inside
**that project's own** CI, on **your** infrastructure. Security of the kit
itself therefore means: the scripts must not corrupt state, leak data, or
produce workflows that are trivially bypassable by design. Anything else lives
in the project that uses the kit — start from the template `SECURITY.md`.
