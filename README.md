# AutoPartsSync

AutoPartsSync - внутреннее Django-приложение для магазина автозапчастей. Проект помогает искать аналоги деталей и остатки через внешние сервисы, а также вести базу клиентов и их автомобилей.

## Основные функции

- поиск аналогов по артикулу;
- получение остатков через интеграцию с МойСклад;
- хранение клиентов и связанных с ними автомобилей;
- поиск клиентов по имени, телефону, VIN, госномеру, марке и модели;
- авторизация сотрудников через кастомную Django user-модель с email как идентификатором входа.

## Стек технологий

- Python 3.13
- Django 6
- SQLite
- requests
- python-dotenv
- Gunicorn
- Nginx
- Docker Compose

## Запуск локально

1. Создайте и активируйте виртуальное окружение.
2. Установите зависимости.
3. Заполните `.env` в корне проекта.
4. Выполните миграции.
5. При необходимости создайте суперпользователя.
6. Запустите сервер разработки.

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

Минимальные переменные окружения:

- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `ABCP_URL`
- `ABCP_USER`
- `ABCP_PASS`
- `MS_TOKEN`

## Команды для разработки

### Install

```powershell
pip install -r requirements.txt
```

### Run

```powershell
cd src
..\.venv\Scripts\python.exe manage.py runserver
```

### Test

```powershell
cd src
..\.venv\Scripts\python.exe manage.py test
```

Дополнительно можно проверить конфигурацию:

```powershell
cd src
..\.venv\Scripts\python.exe manage.py check
```

## Структура проекта

```text
.
|-- docker/                 # конфигурация nginx
|-- docs/                   # проектная документация
|-- src/
|   |-- config/             # настройки Django и маршруты
|   |-- analogs/            # поиск аналогов и остатков
|   |-- counterparties/     # клиенты и автомобили
|   |-- employees/          # сотрудники и приглашения на активацию
|   |-- templates/          # HTML-шаблоны
|   `-- manage.py
|-- Dockerfile
|-- docker-compose.yaml
`-- requirements.txt
```

## Docker

```powershell
docker compose up --build
```
