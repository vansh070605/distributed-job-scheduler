# Contributing Guidelines

Thank you for contributing to the Distributed Job Scheduler! Please review our coding standards and repository setup rules.

## Local Setup

Refer to the [Setup Guide](setup.md) to set up your local development environment.

## Code Integrity

### Python Style Guide
- Formatting: Enforced using `black` and `isort`.
- Linting: Monitored using `flake8`.
- Running formatting commands locally:
```bash
black app/
isort app/
flake8 app/
```

### TypeScript / React Style Guide
- Formatting: Managed using `prettier`.
- Compiles: Run `npm run build` locally to verify that TypeScript checks pass without errors.
