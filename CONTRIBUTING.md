# Contributing to Career Intelligence Platform

## Development Workflow

Fork the repository.

Create a feature branch:

```bash
git checkout -b feat/your-feature-name
```

Make your changes following the conventions below.

Commit using conventional commits format.

Push your branch and open a Pull Request.

## Commit Message Convention

Format is type(scope): description

### Allowed Types

- feat means a new feature
- fix means a bug fix
- refactor means a code change that is not a feature or bug fix
- chore means build process or tooling changes
- docs means documentation only changes
- test means adding or updating tests
- perf means a performance improvement
- style means formatting changes with no logic change

### Examples

```
feat(auth): add refresh token rotation
fix(ui): correct sidebar overflow on mobile
refactor(db): extract base repository pattern
chore(docker): update PostgreSQL to version 16.2
docs(api): document assessment endpoints
test(auth): add login flow integration tests
```

## Frontend Code Style

Use strict TypeScript with no any types.

Use functional components only.

Extract logic into custom hooks.

Follow the feature-based folder structure.

## Backend Code Style

Use Python 3.12 type hints everywhere.

Use Ruff for linting and formatting.

Use mypy in strict mode.

Use the repository pattern for all database access.

Keep business logic inside service classes.

## Pull Request Requirements

All CI checks must pass before merging.

Test coverage must not decrease.

Documentation must be updated if behavior changes.

All commits must follow the commit convention.

## Reporting Issues

Open a GitHub Issue and use the appropriate issue template.
