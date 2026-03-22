# Архитектура

## Текущее состояние

Проект реализован как небольшой Django monolith с server-rendered интерфейсом.

Подтверждено кодом:

- один Django project `config`;
- два локальных Django app: `analogs` и `counterparties`;
- function-based views;
- Django ORM без отдельного слоя репозиториев;
- Django templates как основной UI;
- стандартный `django.contrib.auth`;
- отсутствие DRF, фоновых задач, signals и management commands прикладного уровня.

Это описание текущего состояния, а не желаемой целевой архитектуры.

## Границы приложений

### `src/config/`

Инфраструктурный модуль проекта.

Файлы:

- `settings.py`
- `urls.py`
- `wsgi.py`
- `asgi.py`

Ответственность:

- настройки Django;
- root routing;
- WSGI/ASGI entry points.

### `src/counterparties/`

Доменный модуль клиентов и автомобилей.

Файлы:

- `models.py` - `Client`, `Car`
- `forms.py` - `ClientForm`, `CarForm`
- `views.py` - workspace, поиск, CRUD
- `urls.py`
- `admin.py`
- `migrations/`

Ответственность:

- хранение клиентских карточек;
- хранение автомобилей клиента;
- поиск по клиентам и автомобилям;
- CRUD через формы и шаблоны.

### `src/analogs/`

Интеграционный модуль поиска по артикулу.

Файлы:

- `views.py`
- `urls.py`
- `models.py` - фактически пустой
- `admin.py` - фактически пустой
- `tests.py` - фактически пустой

Ответственность:

- принять артикул из запроса;
- вызвать ABCP;
- вызвать МойСклад;
- подготовить результат для шаблона `src/templates/search.html`.

## Где живет логика

### Бизнес-логика и orchestration

Сейчас существенная часть логики живет в view-функциях:

- `src/analogs/views.py`
- `src/counterparties/views.py`

Это особенно важно для онбординга:

- в `src/analogs/views.py` рядом находятся HTTP handler, внешние запросы и преобразование ответа;
- в `src/counterparties/views.py` рядом находятся ORM-запросы, вычисление состояния workspace и redirect logic.

### Валидация

Валидация пользовательского ввода в `counterparties` живет в:

- `src/counterparties/forms.py`

В `analogs` отдельного слоя форм или сериализаторов нет.

### Представление

Основной интерфейс находится в шаблонах:

- `src/templates/base.html`
- `src/templates/search.html`
- `src/templates/counterparties/client_list.html`
- `src/templates/registration/login.html`

Часть CSS и JavaScript встроена прямо в шаблоны.

## Работа с БД

По `src/config/settings.py` используется SQLite.

Текущий подход к данным:

- прямой доступ к ORM из view-функций;
- `counterparties/views.py` использует `Q`, `Count`, `Prefetch`, `prefetch_related`;
- отдельного query layer нет;
- в `analogs` собственных моделей нет.

Практический вывод:

- новые ORM-запросы должны размещаться внутри app, которому принадлежат данные;
- нельзя переносить доступ к доменным моделям в `config`;
- дублировать одну и ту же ORM-конструкцию по нескольким views нельзя.

## Request and data flow

### Поиск аналогов

Поток запроса:

1. Пользователь открывает `/analogs/`.
2. `search()` в `src/analogs/views.py` читает query parameter `search`.
3. Выполняется запрос к ABCP `/search/brands/`.
4. Если найден ровно один бренд, выполняется запрос к ABCP `/search/articles/`.
5. Результат обогащается через `ms_assort()`.
6. Затем `search_ms()` запрашивает остатки в МойСклад.
7. Шаблон `src/templates/search.html` отображает таблицу.

Подтвержденные ограничения:

- запросы синхронные;
- используется `requests.get(...)`;
- в запросе остатков есть hardcoded `storeId`;
- ошибочные запросы логируются через `print(...)`.

### Контрагенты

Поток запроса:

1. Пользователь открывает `/counterparties/clients/`.
2. `client_list()` в `src/counterparties/views.py` строит queryset клиентов.
3. View использует `annotate(Count("cars"))` и `prefetch_related(...)`.
4. Состояние интерфейса определяется query parameters:
   - `q`
   - `client`
   - `dialog`
   - `car_form`
5. Шаблон `src/templates/counterparties/client_list.html` отображает список клиентов, карточку и блок автомобилей.

Практический вывод:

- query parameters выше являются частью реального контракта интерфейса;
- любые изменения этих параметров требуют проверки всего workspace flow.

## Auth и permissions

По коду:

- подключен `django.contrib.auth`;
- root routing включает `django.contrib.auth.urls`;
- защищенные страницы используют `@login_required`;
- отдельной ролевой модели и custom permissions не видно.

## Admin

В `src/counterparties/admin.py` зарегистрированы:

- `Client`
- `Car`

В `analogs/admin.py` прикладной admin-логики нет.

## Интеграции

Подтвержденные внешние интеграции:

- ABCP
- МойСклад

Код интеграций расположен в:

- `src/analogs/views.py`

По текущему состоянию:

- credentials берутся из env vars;
- retry-механизма нет;
- централизованного logging нет;
- кэширования нет.

## Что отсутствует

По репозиторию не найдены:

- DRF;
- Celery;
- RQ;
- cron-like jobs;
- signals;
- management commands прикладного уровня;
- CI configuration.

## Сильные стороны

- небольшой и понятный Django stack;
- быстрое погружение в код;
- простая карта приложения;
- базовая оптимизация ORM уже используется в `counterparties`;
- локальный и Docker-запуск очевидны.

## Слабые стороны

- логика сосредоточена во view-функциях;
- автотесты отсутствуют;
- интеграции синхронны и слабо наблюдаемы;
- в шаблонах большие inline CSS/JS блоки;
- есть исторические следы старой структуры, например `client_detail.html`.

## Архитектурные правила для новых изменений

- Не добавлять новые доменные сущности без подтверждения в задаче и документации.
- Изменения клиентов и автомобилей держать внутри `src/counterparties/`.
- Изменения поиска и внешних API держать внутри `src/analogs/`.
- Не вводить DRF, отдельный JSON API или фоновые задачи точечно.
- Новые env vars документировать в том же change set.
- Если логика разрастается, выносить ее целиком в отдельный модуль внутри того же app.

## How to add new functionality without breaking architecture

1. Определить owning app:
   - `counterparties` для клиентов и автомобилей;
   - `analogs` для поиска и интеграций;
   - `config` только для инфраструктуры.
2. Проверить связанные файлы:
   - `urls.py`
   - `views.py`
   - `forms.py`
   - шаблоны
   - `admin.py`
3. Если меняется модель:
   - обновить модель;
   - создать миграцию;
   - проверить формы, admin и affected templates.
4. Если меняется поиск аналогов:
   - не менять молча структуру результата для `src/templates/search.html`;
   - проверить работу при пустом ответе и ошибке внешнего API.
5. Если меняется workspace клиентов:
   - сохранить совместимость `q`, `client`, `dialog`, `car_form`;
   - проверить поиск, создание, редактирование и удаление.
6. Перед завершением:
   - выполнить `python manage.py check`;
   - выполнить `python manage.py test`;
   - вручную проверить затронутую страницу.
7. Обновить:
   - `README.md`;
   - релевантные документы в `docs/`;
   - `docs/ai-context.md` и `.codex/working-rules.md`, если меняются устойчивые правила работы.
