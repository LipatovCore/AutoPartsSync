# Карта кодовой базы

## Репозиторий верхнего уровня

```text
AutoPartsSync/
|-- .env                     # локальные переменные окружения, не источник истины для VCS
|-- .gitignore
|-- CONTRIBUTING.md
|-- Dockerfile
|-- README.md
|-- docker-compose.yaml
|-- docker/
|   `-- nginx/default.conf
|-- docs/
|-- src/
`-- .codex/
```

## Ключевые директории

### `src/`

Корень Django-проекта.

Содержит:

- `manage.py`
- `config/`
- `analogs/`
- `counterparties/`
- `templates/`
- `staticfiles/`

### `src/config/`

Инфраструктурная конфигурация Django:

- `settings.py` - единый settings module;
- `urls.py` - корневые маршруты;
- `wsgi.py` - WSGI entry point;
- `asgi.py` - ASGI entry point.

### `src/analogs/`

Приложение поиска аналогов.

Важные файлы:

- `views.py` - основной код поиска и интеграций;
- `urls.py` - маршрутизация `/analogs/`;
- `models.py` - пустой;
- `admin.py` - пустой;
- `tests.py` - пустой;
- `migrations/` - без прикладных миграций.

### `src/counterparties/`

Приложение клиентов и автомобилей.

Важные файлы:

- `models.py`
- `forms.py`
- `views.py`
- `urls.py`
- `admin.py`
- `tests.py`
- `migrations/0001_initial.py`
- `migrations/0002_remove_client_type.py`

### `src/templates/`

Глобальные и app-level шаблоны:

- `base.html`
- `search.html`
- `registration/login.html`
- `counterparties/client_list.html`
- `counterparties/client_detail.html`

### `src/staticfiles/`

Содержит собранные admin static files. Это не место для прикладной бизнес-логики. Изменять только осознанно.

### `docker/`

Инфраструктурная конфигурация nginx:

- `docker/nginx/default.conf`

## Entry points

### Запуск разработки

- `src/manage.py`

### Корневые URL

- `src/config/urls.py`

Подключены маршруты:

- `/admin/`
- `/accounts/`
- `/analogs/`
- `/counterparties/`

### Runtime entry points

- `config.wsgi:application` для gunicorn
- nginx proxy через `docker/nginx/default.conf`

## Где искать что

### Если нужно изменить настройки

Смотрите:

- `src/config/settings.py`
- `.env`
- `docker-compose.yaml`
- `Dockerfile`

### Если нужно изменить поиск аналогов

Смотрите:

- `src/analogs/views.py`
- `src/analogs/urls.py`
- `src/templates/search.html`

### Если нужно изменить клиентов или автомобили

Смотрите:

- `src/counterparties/models.py`
- `src/counterparties/forms.py`
- `src/counterparties/views.py`
- `src/counterparties/urls.py`
- `src/templates/counterparties/client_list.html`
- `src/counterparties/admin.py`

### Если нужно изменить авторизацию

Смотрите:

- `src/config/urls.py`
- `src/templates/registration/login.html`
- `src/config/settings.py`

## Настройки и конфигурация

### Python dependencies

- `requirements.txt`

### Docker

- `Dockerfile`
- `docker-compose.yaml`

### nginx

- `docker/nginx/default.conf`

### Environment variables

По коду используются:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `ABCP_URL`
- `ABCP_USER`
- `ABCP_PASS`
- `MS_TOKEN`

Дополнительно локально присутствует:

- `MS_LOGIN` - `Needs verification`, по коду не используется

## Миграции, тесты, статика, шаблоны, скрипты

### Миграции

- `src/counterparties/migrations/`
- `src/analogs/migrations/`

### Тесты

- `src/counterparties/tests.py`
- `src/analogs/tests.py`

Сейчас фактически пусты.

### Шаблоны

- `src/templates/`
- `src/templates/counterparties/`
- `src/templates/registration/`

### Статика

- `src/staticfiles/`

### Скрипты

Отдельных `scripts/` и management commands в репозитории не найдено.

## Навигация для нового разработчика

Рекомендуемый порядок чтения:

1. `README.md`
2. `docs/project-overview.md`
3. `docs/architecture.md`
4. `docs/development-rules.md`
5. `src/config/settings.py`
6. `src/config/urls.py`
7. профильный app:
   - `src/analogs/views.py`
   - или `src/counterparties/models.py`, `forms.py`, `views.py`

## Особые замечания

- `src/templates/counterparties/client_detail.html` существует, но текущий `client_detail` view делает redirect в workspace и не рендерит этот шаблон напрямую.
- `src/analogs/models.py` и `src/analogs/admin.py` пока не содержат прикладной логики.
- Крупные блоки CSS и JavaScript встроены прямо в шаблоны, поэтому изменения UI часто требуют просмотра HTML, CSS и JS в одном файле.
- При чтении русскоязычных файлов через PowerShell возможны артефакты кодировки; проверять нужно содержимое файла, а не только вывод консоли.
