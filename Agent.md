# Agent Guide for Codex

Этот файл описывает обязательный порядок работы агента в репозитории `AutoPartsSync`.

## 1. Что читать перед началом работы

Обязательный порядок:

1. [todo.md](/C:/Users/lipyf/GitHub/AutoPartsSync/todo.md)
2. [README.md](/C:/Users/lipyf/GitHub/AutoPartsSync/README.md)
3. [docs/architecture.md](/C:/Users/lipyf/GitHub/AutoPartsSync/docs/architecture.md)
4. [docs/architecture-rules.md](/C:/Users/lipyf/GitHub/AutoPartsSync/docs/architecture-rules.md)
5. [docs/requirements.md](/C:/Users/lipyf/GitHub/AutoPartsSync/docs/requirements.md)
6. [CONTRIBUTING.md](/C:/Users/lipyf/GitHub/AutoPartsSync/CONTRIBUTING.md)
7. [.codex/working-rules.md](/C:/Users/lipyf/GitHub/AutoPartsSync/.codex/working-rules.md)

После этого нужно прочитать точные файлы, которые затрагивает задача.

## 2. Статус `todo.md`

`todo.md` — основной файл плана по репозиторию.

Обязательные правила:

- перед началом любой работы агент обязан читать `todo.md`;
- если задача уже есть в `todo.md`, агент должен ориентироваться на её текущий статус;
- после выполнения задачи агент обязан обновить её статус в `todo.md`;
- если во время работы обнаружена новая важная задача, агент обязан добавить её в `todo.md`;
- нельзя считать задачу завершённой, если изменения не внесены и не проверены.

## 3. Архитектурное правило

Любые изменения должны соответствовать архитектуре из:

- [docs/architecture.md](/C:/Users/lipyf/GitHub/AutoPartsSync/docs/architecture.md)
- [docs/architecture-rules.md](/C:/Users/lipyf/GitHub/AutoPartsSync/docs/architecture-rules.md)

Если код уже нарушает архитектурные правила:

- это нужно учитывать как текущее ограничение;
- нельзя silently усиливать нарушение;
- нельзя переписывать модуль целиком без отдельной задачи.

## 4. Как работать с изменениями

- сначала проверить фактическое состояние кода;
- не документировать и не реализовывать выдуманную функциональность;
- менять только релевантные файлы;
- не рефакторить соседние участки "заодно";
- не ломать существующие URL, query-параметры и workflow без явной задачи.

Особенно осторожно работать с:

- [`src/analogs/views.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/analogs/views.py)
- [`src/counterparties/views.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/counterparties/views.py)
- [`src/templates/counterparties/client_list.html`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/templates/counterparties/client_list.html)
- [`src/templates/base.html`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/templates/base.html)
- цепочкой миграций в `employees` и `counterparties`

## 5. Как обновлять документацию

Если меняется хотя бы одно из ниже перечисленного, агент обязан синхронизировать документацию:

- команды запуска;
- env vars;
- структура модулей;
- архитектурные ограничения;
- правила разработки;
- поведение фич;
- риски и технический долг.

Минимальный набор проверки документации после изменения:

- [README.md](/C:/Users/lipyf/GitHub/AutoPartsSync/README.md)
- один или несколько файлов из `docs/`
- [todo.md](/C:/Users/lipyf/GitHub/AutoPartsSync/todo.md), если изменился статус задач
- [.codex/working-rules.md](/C:/Users/lipyf/GitHub/AutoPartsSync/.codex/working-rules.md), если изменились стабильные правила работы агента

## 6. Проверки после изменений

Обязательные команды:

```powershell
cd src
..\.venv\Scripts\python.exe manage.py check
..\.venv\Scripts\python.exe manage.py test
```

Дополнительно:

- вручную проверить затронутый пользовательский сценарий;
- если менялась auth-логика, проверить login, logout, защищённые маршруты и redirect-flow;
- если менялись модели или формы, проверить реальный CRUD;
- если менялись Docker или env-related файлы, проверить сценарий запуска.

## 7. Что нельзя делать

- выдумывать бизнес-функции, которых нет в коде;
- писать документацию по ожиданиям вместо фактов;
- менять архитектуру без явной задачи;
- добавлять новые зависимости без необходимости;
- ломать query-параметры `q`, `client`, `dialog`, `car_form` в `counterparties`;
- считать mojibake в терминале доказательством порчи файла без проверки.

## 8. Как фиксировать неопределённость

Если что-то не подтверждено кодом или проверкой, использовать пометки:

- `Unknown`
- `Assumption`
- `Needs verification`

Нельзя выдавать предположение за факт.
