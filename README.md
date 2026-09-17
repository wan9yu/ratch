# ratch

<!-- ratch:authored -->
ratch is a ratchet for repository invariants: a small set of Tier A checks
that fail a commit the moment a mechanical, provable rule is broken, and stay
silent otherwise. Each check is configured by instantiation, proven by its own
plants, and carries a four-heading docstring stating the rule and its evidence.
The ratchet only turns one way: once a check ships, the repository it gates
cannot regress on that rule without the check itself changing.

ratch will never gate on judgment. It does not score, grade, or block on:

- naming quality
- abstraction quality
- prose quality (including commit-message quality)
- test meaningfulness

Those are decisions to not write code for: a machine cannot prove taste, so
ratch does not pretend to. Those calls belong to review by people. ratch
gates only what a machine can prove.
<!-- ratch:authored:end -->

<!-- ratch:generated:checks -->
<!-- ratch:generated:checks:end -->
