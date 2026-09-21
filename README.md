> **[中文](README.zh.md)** · English

# ratch

[![ci](https://github.com/wan9yu/ratch/actions/workflows/ci.yml/badge.svg)](https://github.com/wan9yu/ratch/actions/workflows/ci.yml)

<!-- ratch:authored -->
A written team agreement works when people keep it. An agent does not
share that embarrassment. Prompts and policy files are not deterministic.
ratch is the extreme-programming form of the agreement: a good practice
pushed until git can re-prove it on every commit. Git author metadata no
longer names which agent made the commit.

Install with `pip install ratch`. Put a `ratch_checks.py` at the
repository root (see `examples/ratch_checks.py`). Without that file,
nothing runs. Run `python -m ratch check`. Gates that fail exit
non-zero; a gate with empty needles is VACUOUS (exit 2) until you pass
`patterns=` / `needles=`. Eyes print and never change the exit code.
`ratch check --compact` shortens the heatmap. `ratch list` labels
enabled, catalog, or meta; `ratch describe no-forbidden-literal` prints
the docstring. They do not run checks.

This repository is gated by its own root `ratch_checks.py`. `./build.sh`
and CI install, run pytest, then `ratch check --compact`.

**Provenance** — commit identity is no longer a person:

- `no-forbidden-literal` — configured tokens in content, paths, or the tip commit; empty `patterns=` is VACUOUS
- `no-first-person` — record prose without first-person voice
- `no-ai-signatures` — attribution trailers; `sources=` can add tags and files; a shallow clone FAILs

**Debris agents leave in the tree:**

- `no-conflict-markers` — unfinished merge markers
- `no-vacuous-assert` — `assert True` / `assert False` placeholders
- `no-pytest-skip` — skipped tests that read green; `paths=` for invariants vs e2e
- `no-hash-named-test` — test files named with a forgotten hex suffix
- `todo-has-issue-ref` — debt markers without an issue citation
- `bdd-test-conventions` — test names that read as a sentence; `prefix=` / `blank_blocks=`
- `no-circular-import` — a package that only imports in one order
- `no-reassurance-words` — prose that tells the reader to stop checking
- `loc-cap` — Python modules over 1000 lines
- `no-external-font-cdn` — shipped HTML/CSS/JS fetching remote webfonts; no web files is not-applicable

**The agreement must apply to the agreement:**

- `plugin-registry` — every plugin has plants, fixture, and headings (meta)
- `manifest-purity` — `ratch_checks.py` is importable and repeatable
- `no-internal-refs` — configured needles in tracked files; empty `needles=` is VACUOUS
- `doc-counts-match-ssot` — README `catalog_n` equals `discover()` (meta)
- `docs-equal-fresh-render` — the generated region matches a live render (meta)
- `tests-repo-root-ssot` — tests import one ROOT helper, not `__file__` parent walks
- `injected-clock` — bound stdlib time/datetime calls only if a Clock type exists
- `doc-cli-examples-valid` — documented ratch commands parse
- `no-autoclose-keywords-in-commits` — commit messages that would auto-close issues

**Eyes** — evidence, never a failed run:

- `catalog-size` — `enabled_n` vs `catalog_n` (wheel entry points, not a debt score)
- `commit-heatmap` — tracked files × time; `--compact` for one line

ratch will never gate on judgment. It does not score, grade, or block on:

- naming quality
- abstraction quality
- prose quality (including commit-message quality)
- test meaningfulness

Those calls belong to review by people. ratch gates only what a machine
can prove.
<!-- ratch:authored:end -->

<!-- ratch:generated:checks -->
catalog_n=24
<!-- ratch:generated:checks:end -->
