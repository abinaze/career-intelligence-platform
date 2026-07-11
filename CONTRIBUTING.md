# Contributing to Career Intelligence Platform

Thank you for considering a contribution. This document covers everything you need to open a pull request that can be reviewed and merged efficiently.

Before contributing, please read the [LICENSE-SUMMARY.md](./LICENSE-SUMMARY.md). By submitting a contribution, you agree that it will be distributed under the project's [PolyForm Noncommercial License 1.0.0](./LICENSE).

## Ways to contribute

- Fix a bug reported in [Issues](https://github.com/abinaze/career-intelligence-platform/issues)
- Improve or correct documentation
- Add test coverage for an existing feature
- Propose a new feature — please open an issue first using the feature request template so the direction can be discussed before you invest time in an implementation
- Improve accessibility, performance, or code quality in an existing area

## Development workflow

1. Fork the repository.
2. Create a feature branch:
   ```bash
   git checkout -b feat/your-feature-name
   ```
3. Follow the setup steps in the [README](./README.md#getting-started) to get the stack running locally.
4. Make your changes following the code style guidelines below.
5. Commit using the [Conventional Commits](https://www.conventionalcommits.org/) format described below.
6. Push your branch and open a Pull Request against `main`.

## Commit message convention

Format: `type(scope): description`

### Allowed types

| Type | Meaning |
|---|---|
| `feat` | A new feature |
| `fix` | A bug fix |
| `refactor` | A code change that is neither a feature nor a bug fix |
| `chore` | Build process or tooling changes |
| `docs` | Documentation-only changes |
| `test` | Adding or updating tests |
| `perf` | A performance improvement |
| `style` | Formatting changes with no logic change |

### Examples

```
feat(auth): add refresh token rotation
fix(ui): correct sidebar overflow on mobile
refactor(db): extract base repository pattern
chore(docker): update PostgreSQL to version 16.2
docs(api): document the chat endpoint
test(auth): add login flow integration tests
```

## Code style

### Frontend (`apps/frontend`)

- Strict TypeScript — no `any` types.
- Functional components only.
- Business logic belongs in custom hooks or the Zustand store, not in JSX.
- Follow the existing feature-based folder structure (`features/<name>/{types,api,hooks,store,components}`).
- Run `pnpm lint` and `pnpm type-check` before opening a PR.

### Backend (`apps/backend`)

- Python 3.12 type hints everywhere.
- Ruff for linting and formatting — run `uv run ruff check . && uv run ruff format .` before committing.
- mypy in strict mode for type checking.
- Business logic belongs in service classes (`src/services/`), not in endpoint handlers.
- Database access goes through the repository pattern (`src/db/repositories/`).
- Run `uv run pytest` before opening a PR.

## Pull request requirements

- All CI checks must pass (lint, type-check, tests) for both frontend and backend.
- Test coverage must not decrease for the code you touched.
- Update relevant documentation in `docs/` if your change affects behavior described there.
- Keep PRs focused — one logical change per PR is easier to review than a large mixed PR.
- All commits must follow the commit convention above.

## Reporting issues

Open a GitHub Issue and use the appropriate template (bug report or feature request). Include:

- A clear description of the problem or proposal
- Steps to reproduce (for bugs)
- Your environment (OS, Node/Python version) if relevant

## Reporting security vulnerabilities

Do not open a public issue for security vulnerabilities. See [SECURITY.md](./SECURITY.md) for the responsible disclosure process.

## Code of conduct

This project follows the [Code of Conduct](./CODE_OF_CONDUCT.md). Participation in this project's community — issues, pull requests, discussions — implies agreement to abide by it.
