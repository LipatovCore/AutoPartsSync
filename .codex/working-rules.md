# Codex Working Rules

## Inspect before editing

Before any code change, inspect:

1. `README.md`
2. `docs/architecture.md`
3. `docs/development-rules.md`
4. `docs/decisions-and-debt.md`
5. the exact app files you will touch

Minimum inspection:

- `src/config/settings.py`
- `src/config/urls.py`
- app-specific `views.py`
- related `models.py`, `forms.py`, templates, `admin.py`
- related migrations if models or domain meaning are involved

## Read these docs first

- `docs/project-overview.md`
- `docs/architecture.md`
- `docs/codebase-map.md`
- `docs/ai-context.md`

## Hard boundaries

- Do not invent unsupported business modules.
- Do not turn the project into API-first architecture by accident.
- Do not move domain logic into `src/config/`.
- Do not break the query-param-driven workspace flow in `counterparties`.
- Do not treat terminal mojibake as proof that file contents are broken.

## Files not to refactor casually

- `src/analogs/views.py`
- `src/counterparties/views.py`
- `src/templates/counterparties/client_list.html`
- `src/templates/base.html`
- existing migration chain

## Values that are part of the current UI contract

Do not change without full workflow verification:

- `q`
- `client`
- `dialog`
- `car_form`

## What must be tested after changes

Always run:

- `python manage.py check`
- `python manage.py test`

Also manually test the affected UI flow, especially if you changed:

- templates
- redirects
- auth
- external integration behavior
- ORM queries in `counterparties`
- model forms

## How to record uncertainty

Use one of these labels:

- `Unknown`
- `Assumption`
- `Needs verification`
- `Historical evidence`

Do not promote a guess into a fact.

## When docs must be updated

Update docs whenever you change:

- project scope
- env vars
- commands
- architecture boundaries
- app/module structure
- migration expectations
- known risks or debt
- practical rules future agents must follow

Minimum docs review after a code change:

- `README.md`
- one or more files in `docs/`
- `docs/ai-context.md` if agent workflow changed
- `.codex/working-rules.md` if stable operating rules changed
