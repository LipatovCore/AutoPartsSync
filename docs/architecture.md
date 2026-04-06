# Архитектура AutoPartsSync

Документ фиксирует фактическое устройство проекта по состоянию текущего кода. Здесь нет целевой архитектуры "на будущее", если она не подтверждена файлами в `src/`.

## 1. Общая схема

```text
HTTP request
  -> config.urls
  -> app urls
  -> view
     -> forms / services / repositories / ORM / external HTTP API
  -> template
  -> HTML response
```

Реально используются три разных стиля внутри одного монолита:

1. `employees`
   Есть слои `views -> services -> repository -> models`.
2. `counterparties`
   Используется `views -> forms + ORM -> templates`.
3. `analogs`
   Почти вся логика находится прямо в `views.py`, включая запросы во внешние API.

## 2. Модули и их роли

### `src/config`

Назначение:

- загрузка окружения;
- настройки Django;
- root URL;
- WSGI/ASGI entrypoints.

Ключевые файлы:

- [`src/config/settings.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/config/settings.py)
- [`src/config/urls.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/config/urls.py)
- [`src/config/wsgi.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/config/wsgi.py)
- [`src/config/asgi.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/config/asgi.py)

Что важно:

- `.env` читается из корня репозитория через `python-dotenv`;
- база данных по умолчанию: SQLite;
- модель пользователя заменена на `employees.Employee`;
- все приложения подключаются здесь.

### `src/employees`

Назначение:

- кастомная user-модель;
- логин сотрудников;
- приглашения на установку пароля;
- деактивация и сброс доступа;
- аудит событий доступа;
- bootstrap групп и permission.

Структура:

- [`src/employees/models.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/employees/models.py)
- [`src/employees/views.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/employees/views.py)
- [`src/employees/forms.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/employees/forms.py)
- [`src/employees/auth_backends.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/employees/auth_backends.py)
- [`src/employees/permissions.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/employees/permissions.py)
- [`src/employees/repositories/invitation_repository.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/employees/repositories/invitation_repository.py)
- [`src/employees/services/invitation_service.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/employees/services/invitation_service.py)
- [`src/employees/services/password_setup_service.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/employees/services/password_setup_service.py)
- [`src/employees/services/access_service.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/employees/services/access_service.py)
- [`src/employees/services/audit_service.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/employees/services/audit_service.py)
- [`src/employees/services/security_service.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/employees/services/security_service.py)
- [`src/employees/services/session_service.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/employees/services/session_service.py)

Это самый структурированный модуль проекта.

### `src/counterparties`

Назначение:

- клиенты;
- автомобили клиентов;
- поиск и CRUD в одном workspace.

Структура:

- [`src/counterparties/models.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/counterparties/models.py)
- [`src/counterparties/forms.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/counterparties/forms.py)
- [`src/counterparties/views.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/counterparties/views.py)
- [`src/counterparties/urls.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/counterparties/urls.py)
- [`src/counterparties/admin.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/counterparties/admin.py)

Фактический паттерн:

- формы валидируют пользовательский ввод;
- view-функции сами строят queryset, сами выбирают активного клиента, сами управляют редиректами и `messages`;
- отдельного service/repository слоя нет.

### `src/analogs`

Назначение:

- поиск брендов и аналогов в ABCP;
- запрос ассортимента и остатков из МойСклад;
- вывод итоговой таблицы.

Структура:

- [`src/analogs/views.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/analogs/views.py)
- [`src/analogs/urls.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/analogs/urls.py)
- [`src/analogs/models.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/analogs/models.py)

Фактически:

- моделей нет;
- почти весь модуль состоит из одного набора функций в `views.py`;
- интеграция и orchestration не отделены от HTTP-слоя.

### `src/templates`

Назначение:

- server-side rendered UI.

Что важно:

- общий layout в [`src/templates/base.html`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/templates/base.html);
- страницы логина и установки пароля имеют собственные standalone шаблоны;
- `counterparties/client_list.html` содержит не только HTML, но и большой объём inline CSS/JS.

### `src/staticfiles`

Это собранная статика, в основном артефакты Django admin. Не место для правок бизнес-логики.

## 3. Слои и реальные зависимости

### `config`

Может зависеть от:

- Django settings API;
- переменных окружения;
- приложений проекта.

Не должен содержать:

- предметную логику;
- вызовы внешних бизнес-интеграций.

### `views`

Реальная роль:

- принять HTTP-запрос;
- извлечь query string / POST;
- создать и проверить формы;
- вызвать сервис или ORM;
- записать `messages`;
- вернуть `render` или `redirect`.

Фактические зависимости:

- `employees.views` зависит от forms, services, repository, permission helpers;
- `counterparties.views` зависит от forms, ORM, query params, templates;
- `analogs.views` зависит от `requests`, `os.getenv`, внешних API и templates.

### `services`

Сейчас существуют только в `employees`.

Роль:

- бизнес-сценарии доступа сотрудников;
- транзакции;
- генерация токенов;
- запись аудита;
- rate limiting;
- завершение сессий.

Зависимости:

- repository;
- models;
- Django settings;
- cache;
- sessions.

### `repositories`

Сейчас есть только [`src/employees/repositories/invitation_repository.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/employees/repositories/invitation_repository.py).

Роль:

- собрать ORM-операции, которые переиспользуются в сервисах доступа.

### `forms`

Роль:

- валидация HTML-форм;
- минимальная настройка виджетов;
- без бизнес-сценариев.

### `models`

Роль:

- структура данных;
- связи;
- ограничения;
- `Meta`;
- простые invariants.

## 4. Модель данных

### `counterparties`

`Client`

- `name`
- `phone`
- `note`
- `created_at`

`Car`

- `client -> Client`
- `brand`
- `model`
- `license_plate`
- `vin`
- `note`
- `created_at`

Поведение:

- удаление клиента каскадно удаляет связанные автомобили;
- явных уникальных ограничений на VIN, номер или телефон нет.

### `employees`

`Employee`

- email как `USERNAME_FIELD`
- статусы `created`, `active`, `deactivated`
- `email_verified`
- стандартные поля `AbstractUser`, кроме `username`

`EmployeeInvitation`

- хранит только `token_hash`, а не сырой токен;
- имеет `expires_at`, `used_at`, `revoked_at`;
- на уровне БД разрешено только одно незавершённое приглашение на сотрудника.

`EmployeeAccessAuditEvent`

- тип события;
- целевой сотрудник;
- инициатор;
- приглашение;
- IP;
- JSON metadata;
- время создания.

## 5. Точки входа

HTTP:

- `/accounts/login/` -> `EmployeeLoginView`
- `/accounts/` -> стандартные Django auth URLs
- `/employees/` -> employee management
- `/analogs/` -> поиск аналогов
- `/counterparties/` -> workspace клиентов
- `/admin/` -> Django admin

Фоновых задач, отдельных CLI-команд приложения или worker-процессов в репозитории нет.

## 6. Конфигурация и инфраструктура

### Настройки

Главные настройки:

- [`src/config/settings.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/config/settings.py)

Подтверждённые env vars:

- `DJANGO_ENV`
- `DJANGO_SECRET_KEY`
- `DJANGO_DEBUG`
- `DJANGO_ALLOWED_HOSTS`
- `ABCP_URL`
- `ABCP_USER`
- `ABCP_PASS`
- `MS_TOKEN`

### Docker

- [`Dockerfile`](/C:/Users/lipyf/GitHub/AutoPartsSync/Dockerfile)
- [`docker-compose.yaml`](/C:/Users/lipyf/GitHub/AutoPartsSync/docker-compose.yaml)
- [`docker/nginx/default.conf`](/C:/Users/lipyf/GitHub/AutoPartsSync/docker/nginx/default.conf)

Контур:

- Gunicorn внутри `web`;
- Nginx спереди;
- `collectstatic` выполняется при старте `web`;
- отдельный volume под `staticfiles`.

## 7. Где должна находиться логика

### Уже нормально размещено

- employee-auth сценарии: в `employees/services/*`;
- ORM-операции invite/access: в `employees/repositories/invitation_repository.py`;
- правила модели доступа: в `employees/models.py` и `employees/permissions.py`.

### Сейчас размещено неидеально, но так устроен код

- `analogs`: интеграции и orchestration прямо во view;
- `counterparties`: ORM и workspace-логика прямо во view;
- большие UI-правила в шаблонах.

### Куда класть новую логику

- изменения employee-auth продолжать в текущем service/repository паттерне `employees`;
- новые поля и ограничения клиентов/авто добавлять в `counterparties.models` и `counterparties.forms`;
- если в `counterparties` появится повторяемый бизнес-сценарий, сначала выделять сервис, не ломая текущие URL и query-параметры;
- если дорабатывается `analogs`, желательно выносить внешние вызовы из view в отдельный integration/service слой поэтапно, без скрытого переписывания фичи.

## 8. Где логика не должна находиться

- в `config`;
- в `staticfiles`;
- в миграциях;
- в шаблонах, если это бизнес-правило, а не чисто визуальное поведение;
- в `print()`-вызовах для обработки ошибок интеграций.

## 9. Зафиксированные архитектурные нарушения

Это не задачи на немедленное переписывание. Это факты, которые надо учитывать при разработке.

1. [`src/analogs/views.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/analogs/views.py)
   Смешаны HTTP-обработка, env access, внешние API и преобразование результата.
2. [`src/analogs/views.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/analogs/views.py)
   Захардкожен `storeId` МойСклад.
3. [`src/analogs/views.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/analogs/views.py)
   Ошибки интеграций обрабатываются через `print()`, а не `logging`.
4. [`src/counterparties/views.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/counterparties/views.py)
   View-файл совмещает HTTP, ORM, выбор состояния workspace и часть прикладной логики.
5. [`src/templates/counterparties/client_list.html`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/templates/counterparties/client_list.html)
   Шаблон содержит крупные блоки inline CSS/JS и становится точкой концентрации UI-логики.
6. [`src/templates/base.html`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/templates/base.html)
   Общий layout содержит большой встроенный CSS вместо отдельной статики.

## 10. Что не реализовано

По коду отсутствуют:

- публичная регистрация;
- восстановление пароля сотрудником без администратора;
- email-отправка приглашений из системы;
- API для фронтенда;
- история поиска аналогов;
- массовый импорт/экспорт клиентов;
- отдельный service/repository слой для `counterparties` и `analogs`.
