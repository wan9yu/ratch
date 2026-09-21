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
repository root (see `examples/ratch_checks.py`). Run
`python -m ratch check`. Gates that fail exit non-zero. Eyes print and
never change the exit code. `ratch list` and `ratch describe no-forbidden-literal` show the
catalog; they do not run checks.

This repository is gated by its own root `ratch_checks.py`. `./build.sh`
and CI install, run pytest, then `ratch check`.

**Provenance** — commit identity is no longer a person:

- `no-forbidden-literal` — author-tool tokens in content, paths, or the tip commit
- `no-first-person` — record prose without first-person voice
- `no-ai-signatures` — attribution trailers that survive rebase

**Debris agents leave in the tree:**

- `no-conflict-markers` — unfinished merge markers
- `no-vacuous-assert` — `assert True` / `assert False` placeholders
- `no-pytest-skip` — skipped tests that read green
- `no-hash-named-test` — test files named with a forgotten hex suffix
- `todo-has-issue-ref` — debt markers without an issue citation
- `bdd-test-conventions` — test names that read as a sentence; two blank lines split the body into three blocks
- `no-circular-import` — a package that only imports in one order
- `no-reassurance-words` — prose that tells the reader to stop checking
- `loc-cap` — Python modules over 1000 lines
- `no-external-font-cdn` — shipped HTML/CSS/JS fetching remote webfonts

**The agreement must apply to the agreement:**

- `plugin-registry` — every plugin has plants, fixture, and headings
- `manifest-purity` — `ratch_checks.py` is importable and repeatable
- `no-internal-refs` — no pointers into a gitignored notes tree
- `doc-counts-match-ssot` — README `catalog_n` equals `discover()`
- `docs-equal-fresh-render` — the generated region matches a live render
- `tests-repo-root-ssot` — tests import one ROOT helper, not Path(__file__) walks
- `injected-clock` — stdlib time/datetime calls only if a Clock type exists
- `doc-cli-examples-valid` — documented ratch commands parse
- `no-autoclose-keywords-in-commits` — commit messages that would auto-close issues

**Eyes** — evidence, never a failed run:

- `catalog-size` — how many plugins are installed
- `commit-heatmap` — directory-grouped file × time touches and numstat growth

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
