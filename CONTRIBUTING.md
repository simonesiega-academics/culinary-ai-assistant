<h1 align="center">Contributing to Culinary AI Assistant</h1>

<p align="center">
  Guidelines for contributing to <strong>Culinary AI Assistant</strong>.
</p>

<p align="center">
  <img src="https://img.shields.io/github/stars/simonesiega-academics/culinary-ai-assistant?style=social" />
  <img src="https://img.shields.io/github/forks/simonesiega-academics/culinary-ai-assistant" />
  <img src="https://img.shields.io/github/last-commit/simonesiega-academics/culinary-ai-assistant" />
  <img src="https://img.shields.io/github/issues-pr/simonesiega-academics/culinary-ai-assistant" />
  <img src="https://img.shields.io/github/issues/simonesiega-academics/culinary-ai-assistant" />
  <img src="https://img.shields.io/github/license/simonesiega-academics/culinary-ai-assistant" />
</p>

## Quick start 🚀

If you are new to the project, read [`README.md`](README.md) first, then pick one issue and keep the PR scope small.

| Step | Action                               |
| ---- | ------------------------------------ |
| 1    | Fork the repository                  |
| 2    | Create a branch from `main`          |
| 3    | Implement one focused change         |
| 4    | Run checks locally                   |
| 5    | Open a PR with context and rationale |

Branch naming:

| Type        | Pattern                     | Example                    |
| ----------- | --------------------------- | -------------------------- |
| Feature     | `feat/<short-description>`  | `feat/pdf-recipe-parser`   |
| Bug fix     | `fix/<short-description>`   | `fix/ingredient-order-sql` |
| Docs        | `docs/<short-description>`  | `docs/update-ci-section`   |
| Maintenance | `chore/<short-description>` | `chore/dependency-update`  |

---

## Issues: bug reports and feature requests

Before opening a new issue, check existing [Issues](../../issues) to avoid duplicates.

Please include:

| Field                                            | Why it matters                                |
| ------------------------------------------------ | --------------------------------------------- |
| Expected behavior                                | Defines the intended result                   |
| Actual behavior                                  | Shows current failure or limitation           |
| Reproduction steps                               | Makes debugging reliable                      |
| Environment (OS, Python, Docker, Ollama version) | Helps isolate platform-specific issues        |
| Logs / error output                              | Speeds root-cause analysis                    |
| Sample input/output (if relevant)                | Clarifies parsing and SQL generation outcomes |

Tip: for architecture-level changes, open an issue first so we can align on design early.

---

## Local validation

Choose one of the following workflows.

### Python + Node workflow

```bash
npm ci
npm run format:check

python -m pip install -r requirements.txt
ruff check src
python -m compileall src
pytest
```

### Docker workflow

```bash
docker compose up --build
```

Reference docs:

- [Docker guide](docs/setup/docker.md)

---

## Pull request checklist

Before requesting review, verify:

- [ ] Title and description explain what changed and why
- [ ] Local checks/tests were run when applicable
- [ ] Docs were updated if behavior or usage changed
- [ ] No secrets or personal data were committed
- [ ] PR is focused (no unrelated cleanup)

---

## Security policy

If you discover a vulnerability, **do not** open a public issue.

Report privately to the maintainer with:

- Description
- Impact
- Reproduction steps
- Suggested mitigation (optional but appreciated)

---

## Community guidelines 🤝

Be respectful and constructive in issues, PRs, and reviews.

Clear, actionable feedback is always welcome.

---

## Contact 📬

For direct contact:

- Email: simonesiega1@gmail.com
- GitHub: https://github.com/simonesiega

Thanks again for contributing to Culinary AI Assistant.
