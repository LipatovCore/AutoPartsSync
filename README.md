# AutoPartsSync

Внутренний Django-монолит для магазина автозапчастей. По текущему коду проект решает три задачи:

- поиск аналогов детали по артикулу через ABCP и показ остатков из МойСклад;
- ведение базы клиентов и их автомобилей;
- закрытый доступ сотрудников через кастомную модель пользователя `employees.Employee`.

Документ описывает только то, что подтверждается кодом в `src/`.

## Что реализовано

### `analogs`

- маршрут: `/analogs/`
- вход: только для авторизованных пользователей
- сценарий:
  - пользователь вводит артикул в GET-параметр `search`;
  - приложение запрашивает бренды в ABCP;
  - если ABCP вернул ровно один бренд, приложение запрашивает аналоги;
  - для найденных артикулов приложение запрашивает данные по ассортименту и остаткам в МойСклад;
  - в интерфейсе отображаются `article`, `brand`, `stock`.

Ограничения текущей реализации:

- поиск не работает как пошаговый выбор бренда: результат есть только когда ABCP вернул ровно один бренд;
- локальных моделей и кэша для результатов нет;
- ошибки интеграций не логируются штатно, а печатаются через `print()`;
- `storeId` МойСклад захардкожен в [`src/analogs/views.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/analogs/views.py).

### `counterparties`

- маршруты начинаются с `/counterparties/clients/`
- вход: только для авторизованных пользователей
- сущности:
  - `Client`: имя, телефон, комментарий, дата создания;
  - `Car`: клиент, марка, модель, госномер, VIN, комментарий, дата создания.
- поддерживаемые операции:
  - список клиентов;
  - единый поиск по имени клиента, телефону, марке, модели, госномеру и VIN;
  - выбор активного клиента через query string;
  - создание, редактирование и удаление клиента;
  - создание, редактирование и удаление автомобиля клиента.

UI зависит от query-параметров:

- `q` — строка поиска;
- `client` — выбранный клиент;
- `dialog` — открытие диалога создания/редактирования;
- `car_form` — режим создания/редактирования автомобиля.

Менять эти параметры без проверки всех переходов нельзя.

### `employees`

- кастомная модель пользователя: [`src/employees/models.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/employees/models.py)
- логин: `/accounts/login/`
- административный интерфейс управления сотрудниками: `/employees/`
- публичная ссылка установки пароля: `/employees/invitations/<token>/set-password/`

Что реально есть в коде:

- вход по email и паролю;
- статусы сотрудника: `created`, `active`, `deactivated`;
- выпуск одноразового приглашения на установку пароля;
- перевыпуск приглашения;
- сброс доступа активного сотрудника;
- деактивация сотрудника;
- завершение серверных сессий при активации, сбросе доступа и деактивации;
- rate limit для логина, установки пароля и перевыпуска приглашения;
- аудит ключевых событий доступа;
- группы `admin` и `user`, синхронизируемые через `post_migrate`.

## Архитектура

Подробно:

- [docs/architecture.md](/C:/Users/lipyf/GitHub/AutoPartsSync/docs/architecture.md)
- [docs/architecture-rules.md](/C:/Users/lipyf/GitHub/AutoPartsSync/docs/architecture-rules.md)

Коротко:

- `config` — настройки, root URL, WSGI/ASGI;
- `employees` — единственное приложение с выраженным service/repository слоем;
- `counterparties` — `models + forms + function-based views + templates + admin`;
- `analogs` — один view-модуль с HTTP-логикой и вызовами внешних API;
- `templates` — серверный рендеринг HTML;
- `staticfiles` — собранная статика, не источник бизнес-логики.

Фактические архитектурные нарушения, которые нужно учитывать:

- в `analogs` бизнес-логика, работа с `.env`, HTTP-запросы и подготовка результата смешаны в [`src/analogs/views.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/analogs/views.py);
- в `counterparties` view-функции напрямую содержат ORM-запросы и логику workspace;
- шаблоны содержат крупные блоки inline CSS/JS, особенно [`src/templates/counterparties/client_list.html`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/templates/counterparties/client_list.html);
- часть текстов в шаблонах и некоторых `.py` выглядит как mojibake в терминале, но это не доказывает порчу логики. Сначала проверять фактическое поведение.

## Структура репозитория

```text
.
|-- .codex/
|-- docker/
|   `-- nginx/default.conf
|-- docs/
|-- src/
|   |-- analogs/
|   |-- config/
|   |-- counterparties/
|   |-- employees/
|   |-- staticfiles/
|   |-- templates/
|   `-- manage.py
|-- .env.example
|-- Agent.md
|-- CONTRIBUTING.md
|-- Dockerfile
|-- docker-compose.yaml
|-- requirements.txt
`-- todo.md
```

## Запуск локально

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt

cd src
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py createsuperuser
..\.venv\Scripts\python.exe manage.py runserver
```

После запуска:

- логин: `/accounts/login/`
- поиск аналогов: `/analogs/`
- клиенты: `/counterparties/clients/`
- управление сотрудниками: `/employees/`
- Django admin: `/admin/`

## Переменные окружения

Шаблон: [`.env.example`](/C:/Users/lipyf/GitHub/AutoPartsSync/.env.example)

Используемые переменные:

- `DJANGO_ENV`
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `ABCP_URL`
- `ABCP_USER`
- `ABCP_PASS`
- `MS_TOKEN`

Правила из текущего `settings.py`:

- `DJANGO_ENV=local` включает локальный режим;
- вне `local` `DEBUG` всегда выключается;
- вне `local` обязательны `DJANGO_SECRET_KEY` и `DJANGO_ALLOWED_HOSTS`;
- в `production` включаются `SECURE_SSL_REDIRECT`, `SESSION_COOKIE_SECURE`, `CSRF_COOKIE_SECURE`, `SECURE_PROXY_SSL_HEADER`;
- локальный fallback `unsafe-local-development-key` допустим только в `local`.

## Docker

Контур из репозитория:

- контейнер `web` запускает миграции, `collectstatic` и Gunicorn;
- контейнер `nginx` проксирует трафик на `web` и раздаёт `/static/`.

Команда:

```powershell
docker compose up --build
```

Важно: `docker-compose.yaml` ожидает файл `.env` в корне репозитория.

## Тесты и проверки

```powershell
cd src
..\.venv\Scripts\python.exe manage.py check
..\.venv\Scripts\python.exe manage.py test
```

Текущее состояние покрытия:

- `employees` покрыт заметно лучше остальных модулей;
- `config` содержит тесты хелперов настроек;
- `analogs` и `counterparties` почти без автотестов.

Поэтому после изменений нужен ручной прогон затронутого UI-сценария.

## Как безопасно вносить изменения

1. Прочитать [todo.md](/C:/Users/lipyf/GitHub/AutoPartsSync/todo.md), затем [docs/architecture.md](/C:/Users/lipyf/GitHub/AutoPartsSync/docs/architecture.md) и [docs/architecture-rules.md](/C:/Users/lipyf/GitHub/AutoPartsSync/docs/architecture-rules.md).
2. Найти фактическую точку изменения в коде.
3. Не переносить существующую логику между приложениями без отдельной задачи.
4. Не менять query-параметры workspace в `counterparties` без полной проверки.
5. После изменений обновить документацию, если изменились правила, структура или поведение.

## Полезные документы

- [docs/requirements.md](/C:/Users/lipyf/GitHub/AutoPartsSync/docs/requirements.md)
- [docs/architecture.md](/C:/Users/lipyf/GitHub/AutoPartsSync/docs/architecture.md)
- [docs/architecture-rules.md](/C:/Users/lipyf/GitHub/AutoPartsSync/docs/architecture-rules.md)
- [docs/employee-auth-plan.md](/C:/Users/lipyf/GitHub/AutoPartsSync/docs/employee-auth-plan.md)
- [Agent.md](/C:/Users/lipyf/GitHub/AutoPartsSync/Agent.md)
- [CONTRIBUTING.md](/C:/Users/lipyf/GitHub/AutoPartsSync/CONTRIBUTING.md)
