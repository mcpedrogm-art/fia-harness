# Contributing to FIA Harness

Thanks for wanting to contribute. This repository is the reference
implementation of a discipline — so contributions must respect the same rules
the kit enforces.

## Ground rules (from the kit itself)

- **No code without an approved spec.** For the kit, the spec is this README,
  `INICIO_PROYECTO.md` and `CHANGELOG_FIXES.md`. If your change affects the
  protocol, explain the design before opening the PR.
- **No invented results.** Every test you claim must have actually run. The CI
  runs the real suite on every push; do not make it pass by weakening it.
- **No secrets.** Never commit credentials, tokens or `.env` files.
- **Keep it dependency-free.** The kit is stdlib-only Python 3.8+. A PR that
  adds an external dependency needs a very strong reason and explicit approval.

## Getting started

1. Fork the repo and clone your fork.
2. Create a branch: `git checkout -b fix/descriptive-name`.
3. Run the suite before and after your change:

```bash
python -m unittest discover tests -v
```

On Windows consoles, run with `PYTHONIOENCODING=utf-8` to avoid emoji output
encoding errors: the tests print ✅/❌ markers.

## What to contribute

Useful contributions today:

- Fixing or extending the parsers in `bootstrap.py` / `task_generator.py`
  with matching tests in `tests/test_harness.py`.
- Edge cases and error messages that are ambiguous.
- Documentation typos and clearer wording (English and Spanish).

Before proposing a large feature, open an issue first and wait for a response:
maintenance is single-person and best-effort, and not every idea will be
accepted — a smaller, sharper kit is the goal.

## Pull request checklist

- [ ] Tests pass locally (49 tests, `python -m unittest discover tests -v`).
- [ ] New behavior has a test. No test, no merge.
- [ ] No unrelated changes mixed in the same PR.
- [ ] Commit messages follow the repo style (Spanish, imperative, concise).
- [ ] No secrets, no debug leftovers, no dependency added without discussion.

## Code of conduct

All interactions fall under our [Code of Conduct](CODE_OF_CONDUCT.md).
