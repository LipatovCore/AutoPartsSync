# AI Context

## Project summary

AutoPartsSync is a Django monolith for an auto parts store internal workflow.

Confirmed by code:

- article-number search in `src/analogs/`
- external HTTP calls to ABCP and MoySklad
- client and car CRUD in `src/counterparties/`
- server-rendered UI in `src/templates/`
- Django auth-protected pages

Not confirmed by code:

- orders
- procurement
- active supplier management
- vehicle-based compatibility search
- background sync jobs
- REST API

Treat anything outside the confirmed list as `Unknown` until you inspect new evidence.

## Domain vocabulary

- `Client`: customer card in `counterparties`
- `Car`: vehicle linked to a `Client`
- `article`: part/article number used in `analogs`
- `brand`: part brand returned by ABCP
- `stock`: current inventory value returned from MoySklad
- `counterparties`: app name; current active scope is client + car

Historical evidence only:

- `src/counterparties/migrations/0001_initial.py` had `Client.type` with `customer` / `supplier`
- `src/counterparties/migrations/0002_remove_client_type.py` removed that field

Do not turn historical evidence into current functionality.

## Architectural boundaries

- `src/config/` is infrastructure only
- `src/counterparties/` owns clients and cars
- `src/analogs/` owns article search and external integration flow
- current DB access is direct Django ORM from views in `counterparties`
- current external API access is direct `requests.get(...)` in `src/analogs/views.py`
- templates are part of the real application surface
- there is no DRF layer, serializer layer, background worker stack, or dedicated query layer

## Common change locations

### Article search changes

Read first:

- `src/analogs/views.py`
- `src/analogs/urls.py`
- `src/templates/search.html`

### Client or car changes

Read first:

- `src/counterparties/models.py`
- `src/counterparties/forms.py`
- `src/counterparties/views.py`
- `src/counterparties/urls.py`
- `src/templates/counterparties/client_list.html`
- `src/counterparties/admin.py`
- `src/counterparties/migrations/0001_initial.py`
- `src/counterparties/migrations/0002_remove_client_type.py`

### Auth or entry-flow changes

Read first:

- `src/config/settings.py`
- `src/config/urls.py`
- `src/templates/registration/login.html`
- `src/templates/base.html`

## Dangerous files

- `src/analogs/views.py`
  - mixes HTTP handling, integration logic, and response shaping
- `src/counterparties/views.py`
  - mixes ORM logic, workspace state resolution, and redirects
- `src/templates/counterparties/client_list.html`
  - large template with inline CSS/JS and stateful UI behavior
- `src/templates/base.html`
  - shared layout and navigation
- `src/config/settings.py`
  - single settings module; small changes affect the whole project

Do not refactor these files casually.

## Required reading before edits

Always read:

1. `README.md`
2. `docs/architecture.md`
3. `docs/development-rules.md`
4. `docs/decisions-and-debt.md`

Then read the exact code files you are about to edit.

## Pre-edit checklist

- Confirm which Django app owns the change.
- Confirm whether the behavior is implemented in code or only implied by docs/history.
- Check related templates, URLs, forms, admin registrations, and migrations.
- Check whether the target file is actually used by the current URL/view flow.
- Check whether new env vars or config values are required.
- Check whether the `counterparties` workspace depends on:
  - `q`
  - `client`
  - `dialog`
  - `car_form`

## Post-edit checklist

- Run `python manage.py check`
- Run `python manage.py test`
- Manually test the affected page or workflow
- Update docs if you changed:
  - app structure
  - env vars
  - commands
  - architecture expectations
  - operational risks
  - rules future agents must follow

## Do-not-do list

- Do not invent unsupported business processes.
- Do not describe supplier/order/procurement functionality as current unless code proves it.
- Do not introduce a partial DRF/API architecture.
- Do not move domain logic into `src/config/`.
- Do not silently change hardcoded integration assumptions such as the current stock store filter.
- Do not treat `src/staticfiles/` as a normal feature-development area.
- Do not assume mojibake in PowerShell means the file itself is broken.
- Do not delete `client_detail.html` only because it looks unused; verify the routing flow first.

## Ambiguity handling rules

Use these labels explicitly:

- `Unknown`
- `Assumption`
- `Needs verification`
- `Historical evidence`

If docs and code conflict:

- trust code first
- update docs
- mention the conflict in your summary
