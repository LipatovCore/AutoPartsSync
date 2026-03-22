# Runbook

## Назначение

Этот документ описывает, как развернуть и проверить текущий Django-проект в локальной среде и через Docker.

## Установка зависимостей

### Локально

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

### Через Docker

Зависимости устанавливаются внутри образа автоматически по `requirements.txt`.

## Настройка окружения

Проект ожидает `.env` в корне репозитория.

Используемые переменные:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `ABCP_URL`
- `ABCP_USER`
- `ABCP_PASS`
- `MS_TOKEN`

Локально также встречается:

- `MS_LOGIN` - `Needs verification`, в коде не используется

## Локальный запуск

```powershell
cd src
..\.venv\Scripts\python.exe manage.py migrate
..\.venv\Scripts\python.exe manage.py runserver
```

### Создание администратора

```powershell
cd src
..\.venv\Scripts\python.exe manage.py createsuperuser
```

### Полезные URL после запуска

- `http://127.0.0.1:8000/analogs/`
- `http://127.0.0.1:8000/counterparties/clients/`
- `http://127.0.0.1:8000/admin/`
- `http://127.0.0.1:8000/accounts/login/`

## Запуск через Docker

```powershell
docker compose up --build
```

Подтвержденное поведение `docker-compose.yaml`:

- `web` собирается из локального `Dockerfile`;
- `web` выполняет миграции;
- `web` выполняет `collectstatic`;
- `web` запускает gunicorn;
- `nginx` публикует порт `80`;
- статика пробрасывается через volume `static_volume`.

## Команды миграций

### Применить миграции

```powershell
cd src
..\.venv\Scripts\python.exe manage.py migrate
```

### Создать миграции

```powershell
cd src
..\.venv\Scripts\python.exe manage.py makemigrations
```

### Показать миграции

```powershell
cd src
..\.venv\Scripts\python.exe manage.py showmigrations
```

## Команды проверки

### Django system check

```powershell
cd src
..\.venv\Scripts\python.exe manage.py check
```

### Тесты

```powershell
cd src
..\.venv\Scripts\python.exe manage.py test
```

Фактическое состояние репозитория: тестов нет, поэтому команда завершается с `NO TESTS RAN`.

## Lint / format

По текущему репозиторию команды lint/format не обнаружены. Нет подтвержденных конфигураций для `ruff`, `black`, `isort`, `mypy` или `pytest`.

## Полезные команды разработчика

```powershell
git status --short
```

```powershell
cd src
..\.venv\Scripts\python.exe manage.py shell
```

```powershell
cd src
..\.venv\Scripts\python.exe manage.py dbshell
```

Примечание: `dbshell` зависит от локального окружения и установленного клиента SQLite.

## Troubleshooting

### Страница логина открывается, но защищенные страницы не работают

Проверить:

- выполнен ли вход;
- создан ли пользователь;
- корректен ли `LOGIN_URL` и `LOGIN_REDIRECT_URL` в settings.

### Поиск аналогов возвращает пустой результат

Проверить:

- задан ли `ABCP_URL`;
- корректны ли `ABCP_USER` и `ABCP_PASS`;
- корректен ли `MS_TOKEN`;
- отвечает ли внешний API;
- не попали ли вы в сценарий, где ABCP вернул не один бренд, а несколько.

### Данные по остаткам отсутствуют

Проверить:

- совпадает ли артикул с ассортиментом в МойСклад;
- доступен ли `MS_TOKEN`;
- не сломан ли hardcoded `storeId` use case.

### `collectstatic` или статика ведут себя неожиданно

Проверить:

- `STATIC_ROOT` в `src/config/settings.py`;
- volume `static_volume` в `docker-compose.yaml`;
- `alias /app/staticfiles/;` в `docker/nginx/default.conf`.

### Подозрение на проблемы кодировки

Проверить:

- кодировку файлов в редакторе;
- кодировку терминала;
- русские строки в шаблонах и Python-файлах;
- не появились ли mojibake-символы после копирования или генерации текста.

Правило:

- не считать искажение текста в PowerShell достаточным доказательством того, что файл реально сохранен в неверной кодировке.

## Что в проекте отсутствует

По текущему коду не найдено:

- Celery / background workers;
- management commands прикладного уровня;
- CI pipeline;
- формальный healthcheck endpoint;
- централизованный logging configuration;
- отдельные scripts для bootstrap.
