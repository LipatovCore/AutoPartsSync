# Agent Guide for Codex

## 1. Project overview

- **Project:** AutoPartsSync
- **Purpose:** internal Django application for an auto parts store. The system is used to search for part analogs and stock through external services, and to manage clients with their cars.
- **Current architecture:** Django monolith with server-side rendered templates.
- **Main domains:**
  - `analogs` - search for analogs and stock via external integrations
  - `counterparties` - clients, cars, search, CRUD
  - `config` - Django settings, root URLs, app bootstrap

### Stack

- Python 3.13
- Django 6
- SQLite
- requests
- python-dotenv
- Gunicorn
- Nginx
- Docker Compose

---

## 2. Required reading

Read these files before starting work:

1. `README.md`
2. `docs/requirements.md`
3. `docs/architecture.md`
4. `docs/architecture-rules.md`
5. `CONTRIBUTING.md`
6. `.codex/working-rules.md`

Then read the exact files you are going to change:

- `src/config/settings.py`
- `src/config/urls.py`
- relevant app `views.py`
- related `models.py`
- related `forms.py`
- related templates
- related migrations if models or schema are involved

---

## 3. Working rules

- Do not change architecture without an explicit request.
- Do not add dependencies unless the task cannot be solved with current tools.
- Do not change existing contracts without direct instruction.
- Work in small, reversible steps.
- Preserve current Django monolith and SSR approach.
- Do not invent new business modules or flows.
- Do not change query-parameter-driven workspace behavior in `counterparties` without full validation.

---

## 4. Implementation rules

- For complex tasks, start with a short plan before editing.
- Change only files directly related to the task.
- Do not refactor outside the task.
- Do not move logic between layers unless the task explicitly requires it.
- Follow the current project style:
  - `counterparties`: `models + forms + function-based views + templates + admin`
  - `analogs`: be careful with existing flow in `views.py`
- Do not casually refactor these files:
  - `src/analogs/views.py`
  - `src/counterparties/views.py`
  - `src/templates/counterparties/client_list.html`
  - `src/templates/base.html`
  - existing migration chain

---

## 5. Validation rules

Run relevant checks after changes:

1. `cd src`
2. `..\.venv\Scripts\python.exe manage.py check`
3. `..\.venv\Scripts\python.exe manage.py test`

Additional validation:

- Manual check of the affected user flow is required.
- If auth was changed, verify login, logout, protected routes, and redirects.
- If models or migrations were changed, verify CRUD behavior and migration correctness.
- If templates were changed, verify `/analogs/`, `/counterparties/clients/`, and `/accounts/login/` when relevant.
- If Docker or infra files were changed, run `docker compose up --build`.

Notes:

- Dedicated lint command is not configured in this repository.
- Tests are currently minimal, so `manage.py test` does not replace manual validation.

---

## 6. Response format

In every final response include:

- **Changed files:** list of modified files
- **Done:** short summary of what was implemented
- **Risks:** what was not verified, what may still break, or what needs attention

If something is uncertain, label it explicitly as one of:

- `Unknown`
- `Assumption`
- `Needs verification`

---

## 7. High-risk areas

Treat these areas as high risk and change them only with extra caution:

- **Auth**
  - login/logout flow
  - `@login_required`
  - redirects and protected routes
- **Database**
  - models
  - migrations
  - constraints
  - cascade deletion
  - query behavior in `counterparties`
- **Infra**
  - `.env` usage
  - Docker
  - Gunicorn
  - Nginx
  - deployment-related settings
- **Security**
  - secrets and tokens
  - `DEBUG`
  - `ALLOWED_HOSTS`
  - external API credentials
  - logging of sensitive data

---

## 8. Plan execution rules

- If a task has a dedicated plan file in `docs/`, always read it before making changes.
- When a checklist-based plan exists, execute only the first unfinished step unless instructed otherwise.
- Do not jump to later steps automatically.
- After successfully finishing a step, update the checklist in the plan file.
- Do not mark a step as completed if implementation, tests, or validation are not finished.
- If the plan becomes outdated during implementation, update only the relevant part of the plan.

---

## 9. Documentation sync rules

- Keep documentation aligned with actual implementation.
- If behavior changes, update `docs/requirements.md` if relevant.
- If structure, flow, or technical design changes, update `docs/architecture.md` if relevant.
- If implementation constraints or project rules change, update related docs if needed.
- Do not document features that are not implemented, unless updating a plan file.
- Plan files may describe intended work; architecture and requirements must reflect actual system state.

---

## 10. Auth and security task rules

For authentication, invitation, password setup, permission, or token-related tasks:

- Prefer Django built-in security mechanisms where appropriate.
- Do not invent custom auth flows if Django provides a safer standard approach.
- Use time-limited and single-use tokens for invitation or password setup flows when required.
- Never store raw passwords, tokens, or secrets in plain text.
- Avoid leaking whether a user exists unless explicitly required.
- Add tests for token validity, expiration, invalid usage, and permission checks.
- Be careful with redirects, session handling, and protected routes.

---

## 11. Decision and ambiguity rules

- Do not make product or workflow decisions when multiple valid options exist.
- If implementation depends on a business choice, stop and ask a concise question.
- If security, UX, or data behavior is ambiguous, ask before implementing.
- Prefer asking over guessing when decisions affect user flow, permissions, tokens, or models.

---

## 12. Scope control rules

- Implement only the minimum required for the current task.
- Do not add speculative features or extensibility.
- Avoid refactoring unrelated parts of the codebase.
- If you notice adjacent issues, mention them instead of fixing them.

---

## 13. Testing rules

- Add or update tests when changing business logic, auth, permissions, forms, or model behavior.
- Prefer focused tests for changed functionality.
- For auth-related tasks, include both success and failure scenarios.
- If tests are not added, explicitly explain why.

---

## Project-specific cautions

- Do not hardcode tokens, passwords, URLs, or store identifiers.
- Do not call external APIs directly from new view logic if it can be isolated better.
- Do not treat terminal encoding issues as proof that file contents are broken.
- Do not document features that are not confirmed by code or docs.
- If working rules change, update related docs together with code.