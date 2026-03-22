# AutoPartsSync

AutoPartsSync - внутреннее Django-приложение для магазина автозапчастей. По текущему состоянию репозитория проект решает две задачи:

- поиск аналогов по артикулу с обращением к ABCP и МойСклад;
- ведение клиентов и связанных с ними автомобилей.

Документ описывает только подтвержденное кодом состояние.

## Что подтверждено кодом

- страница поиска доступна по `/analogs/`;
- поиск использует внешние HTTP-запросы к ABCP и МойСклад;
- данные клиентов и автомобилей хранятся в моделях `Client` и `Car`;
- CRUD по клиентам и автомобилям реализован в приложении `counterparties`;
- защищенные страницы используют стандартный Django auth и `@login_required`;
- проект запускается как Django monolith с `gunicorn` и `nginx`.

## Что не подтверждено кодом

- заказы;
- закупки;
- активная работа с поставщиками как отдельной сущностью;
- подбор деталей по совместимости с автомобилем;
- фоновые синхронизации;
- REST API.

## Реализованные возможности

### Поиск аналогов

- пользователь вводит артикул на странице `/analogs/`;
- код в `src/analogs/views.py` запрашивает бренд и артикулы через ABCP;
- затем тот же модуль запрашивает остатки через МойСклад;
- результат отображается в `src/templates/search.html`.

### Клиенты и автомобили

- `src/counterparties/models.py` содержит `Client` и `Car`;
- `src/counterparties/forms.py` содержит `ClientForm` и `CarForm`;
- `src/counterparties/views.py` реализует поиск, создание, обновление и удаление;
- основной интерфейс находится в `src/templates/counterparties/client_list.html`;
- поиск работает по имени, телефону, марке, модели, госномеру и VIN.

## Технологический стек

- Python
- Django 6.0.2
- SQLite
- requests
- python-dotenv
- gunicorn
- nginx
- Docker / Docker Compose

## Структура проекта

```text
.
|-- Dockerfile
|-- docker-compose.yaml
|-- requirements.txt
|-- src/
|   |-- manage.py
|   |-- config/
|   |-- analogs/
|   |-- counterparties/
|   |-- templates/
|   `-- staticfiles/
|-- docker/
|   `-- nginx/default.conf
|-- docs/
`-- .codex/
```

Подробная карта файлов: [docs/codebase-map.md](docs/codebase-map.md)

## Быстрый старт

### Локальная установка

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

### Переменные окружения

Проект ожидает `.env` в корне репозитория.

По коду используются:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `ABCP_URL`
- `ABCP_USER`
- `ABCP_PASS`
- `MS_TOKEN`

Локально также встречается `MS_LOGIN`, но в коде он не используется. Это `Needs verification`.

### Запуск локально

```powershell
cd src
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py createsuperuser
..\.venv\Scripts\python.exe manage.py runserver
```

Основные URL:

- `/analogs/`
- `/counterparties/clients/`
- `/admin/`
- `/accounts/login/`

### Запуск через Docker

```powershell
docker compose up --build
```

По `docker-compose.yaml` контейнер `web`:

- выполняет миграции;
- выполняет `collectstatic`;
- запускает `gunicorn config.wsgi:application`.

`nginx` публикует `80` и обслуживает `/static/` через volume.

## Проверки

### Django check

```powershell
cd src
..\.venv\Scripts\python.exe manage.py check
```

### Тесты

```powershell
cd src
..\.venv\Scripts\python.exe manage.py test
```

Текущее состояние: инфраструктура тестов есть, но автотестов в репозитории нет.

### Lint / format / type-check

Подтвержденных конфигураций для `ruff`, `black`, `isort`, `mypy`, `pytest` и `pre-commit` в репозитории нет.

## Конфигурация

- Django settings: `src/config/settings.py`
- root URLs: `src/config/urls.py`
- installed apps:
  - стандартные Django apps
  - `analogs`
  - `counterparties`
- база данных по коду: SQLite
- auth settings:
  - `LOGIN_URL = "/accounts/login/"`
  - `LOGIN_REDIRECT_URL = "/analogs/"`
  - `LOGOUT_REDIRECT_URL = "/accounts/login/"`

## Документация

- [docs/project-overview.md](docs/project-overview.md) - предметная область и границы
- [docs/architecture.md](docs/architecture.md) - фактическая архитектура и потоки
- [docs/codebase-map.md](docs/codebase-map.md) - карта каталогов и файлов
- [docs/development-rules.md](docs/development-rules.md) - обязательные правила изменения кода
- [docs/runbook.md](docs/runbook.md) - запуск и troubleshooting
- [docs/decisions-and-debt.md](docs/decisions-and-debt.md) - решения и технический долг
- [docs/ai-context.md](docs/ai-context.md) - контекст для coding agents
- [.codex/working-rules.md](.codex/working-rules.md) - короткие правила для Codex

## Ограничения и вопросы на проверку

- `src/analogs/views.py` совмещает HTTP layer и интеграционную логику.
- Автотесты отсутствуют.
- `storeId` для остатков захардкожен в коде.
- В `src/templates/counterparties/client_detail.html` есть признаки legacy-шаблона, потому что `client_detail` делает redirect в workspace.
- `TIME_ZONE='UTC'` и `LANGUAGE_CODE='en-us'` требуют подтверждения.
- Русскоязычные строки в PowerShell могут отображаться некорректно. Источником истины считать содержимое файлов, а не отображение консоли.
