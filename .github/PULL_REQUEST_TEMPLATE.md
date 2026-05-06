## Summary

<!-- One or two sentences: what does this PR change and why? -->

## Type of change

- [ ] Bug fix
- [ ] New feature
- [ ] New feed integration
- [ ] Refactor / internal cleanup
- [ ] Documentation
- [ ] CI / tooling

## Checklist

- [ ] `uv run ruff format` and `uv run ruff check` pass locally
- [ ] `uv run mypy src/feed_comparison` passes locally
- [ ] `uv run pytest` passes locally
- [ ] Tests added or updated (HTTP-based feeds use `responses` — no real network in CI)
- [ ] `CHANGELOG.md` updated under `[Unreleased]`
- [ ] Documentation (`README.md`, `CONTRIBUTING.md`, `.env.example`) updated where relevant
- [ ] Commits are signed off (`git commit -s`) — DCO

## Notes for the reviewer

<!-- Anything the reviewer should focus on, decisions you'd like a second opinion on, follow-ups for later PRs. -->
