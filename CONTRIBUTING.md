# CONTRIBUTING

Документ для разработчиков и AI-агентов, которые вносят изменения в репозиторий.

## 1. Цель изменений

Изменения должны:

- опираться на реальный код;
- сохранять рабочее поведение системы;
- не расширять продуктовую область без отдельной задачи;
- не маскировать архитектурный долг под "небольшой рефакторинг".

## 2. Что читать перед работой

Минимальный обязательный набор:

1. [todo.md](/C:/Users/lipyf/GitHub/AutoPartsSync/todo.md)
2. [README.md](/C:/Users/lipyf/GitHub/AutoPartsSync/README.md)
3. [docs/architecture.md](/C:/Users/lipyf/GitHub/AutoPartsSync/docs/architecture.md)
4. [docs/architecture-rules.md](/C:/Users/lipyf/GitHub/AutoPartsSync/docs/architecture-rules.md)
5. [docs/requirements.md](/C:/Users/lipyf/GitHub/AutoPartsSync/docs/requirements.md)
6. [.codex/working-rules.md](/C:/Users/lipyf/GitHub/AutoPartsSync/.codex/working-rules.md)

Затем нужно открыть конкретные файлы, которые будут меняться.

## 3. Подготовка локального окружения

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
cd src
..\.venv\Scripts\python.exe manage.py migrate
```

Если нужен суперпользователь:

```powershell
..\.venv\Scripts\python.exe manage.py createsuperuser
```

## 4. Текущие архитектурные правила

### `employees`

- развивать через `views -> services -> repository -> models`;
- новую бизнес-логику employee-auth писать в `services`;
- ORM-обвязку, которая повторяется, держать в repository.

### `counterparties`

- текущий паттерн: `models + forms + function-based views + templates + admin`;
- не ломать query string contract: `q`, `client`, `dialog`, `car_form`;
- не добавлять крупный рефакторинг без отдельной задачи.

### `analogs`

- учитывать, что модуль уже перегружен логикой в `views.py`;
- не усиливать смешение слоёв без необходимости;
- не хардкодить новые идентификаторы, токены и URL.

## 5. Стандарты кода

- Python-идентификаторы на английском;
- пользовательские тексты могут быть на русском;
- формы использовать для валидации HTML-ввода;
- ограничения данных держать в моделях и миграциях;
- бизнес-сценарии выносить в сервисы там, где такой слой уже существует;
- не использовать `print()` для штатной обработки ошибок интеграций;
- не создавать абстрактные `utils.py` как свалку логики.

## 6. Что проверять после изменений

Обязательные команды:

```powershell
cd src
..\.venv\Scripts\python.exe manage.py check
..\.venv\Scripts\python.exe manage.py test
```

Обязательная ручная проверка:

- затронутый UI-сценарий;
- auth flow, если менялись login / invitation / password setup / permissions;
- CRUD, если менялись модели, формы или view;
- Docker run, если менялись infra-файлы.

Важно:

- тесты проекта неравномерны;
- `employees` покрыт лучше остальных модулей;
- отсутствие падений в `manage.py test` не доказывает корректность `analogs` и `counterparties`.

## 7. Обновление документации

Документацию нужно обновлять вместе с кодом, если меняется:

- поведение фич;
- env vars;
- структура модулей;
- архитектурные ограничения;
- команды запуска;
- технические риски.

Минимальный набор:

- [README.md](/C:/Users/lipyf/GitHub/AutoPartsSync/README.md)
- релевантный файл в `docs/`
- [todo.md](/C:/Users/lipyf/GitHub/AutoPartsSync/todo.md), если изменился статус задач

## 8. Отдельные риски проекта

- в [`src/analogs/views.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/analogs/views.py) смешаны интеграции, env access и HTTP-слой;
- в [`src/analogs/views.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/analogs/views.py) захардкожен `storeId` МойСклад;
- в [`src/counterparties/views.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/counterparties/views.py) view содержит ORM и состояние workspace;
- [`src/templates/counterparties/client_list.html`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/templates/counterparties/client_list.html) и [`src/templates/base.html`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/templates/base.html) уже содержат большой inline CSS/JS;
- в терминале часть русского текста отображается с mojibake, но это не означает автоматически, что файл или логика сломаны.

## 9. Правило `todo.md`

`todo.md` — единый рабочий список репозитория.

Нужно:

- читать его перед началом работы;
- обновлять статус выполненных задач;
- добавлять новые найденные задачи;
- не оставлять важные выводы только в памяти диалога.
