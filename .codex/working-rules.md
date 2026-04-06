# Codex Working Rules

## 1. Обязательное чтение перед началом работы

Всегда читать в таком порядке:

1. [todo.md](/C:/Users/lipyf/GitHub/AutoPartsSync/todo.md)
2. [README.md](/C:/Users/lipyf/GitHub/AutoPartsSync/README.md)
3. [docs/architecture.md](/C:/Users/lipyf/GitHub/AutoPartsSync/docs/architecture.md)
4. [docs/architecture-rules.md](/C:/Users/lipyf/GitHub/AutoPartsSync/docs/architecture-rules.md)
5. [docs/requirements.md](/C:/Users/lipyf/GitHub/AutoPartsSync/docs/requirements.md)
6. [Agent.md](/C:/Users/lipyf/GitHub/AutoPartsSync/Agent.md)

После этого читать точные файлы задачи:

- `src/config/settings.py`
- `src/config/urls.py`
- нужные `views.py`, `models.py`, `forms.py`, `templates`
- связанные миграции, если меняется смысл данных

## 2. Жёсткие границы

- не выдумывать неподтверждённую функциональность;
- не превращать проект в API-first или frontend-first архитектуру;
- не переносить доменную логику в `src/config/`;
- не ломать query-параметры `q`, `client`, `dialog`, `car_form` в `counterparties`;
- не считать mojibake в терминале доказательством повреждения файла.

## 3. Текущие архитектурные факты

- `employees` использует service/repository подход;
- `counterparties` работает через `models + forms + function-based views + templates`;
- `analogs` держит интеграции и orchestration в `views.py`.

Новый код должен подчиняться этим фактам и не усиливать существующий архитектурный долг без отдельной задачи.

## 4. Файлы повышенного риска

- `src/analogs/views.py`
- `src/counterparties/views.py`
- `src/templates/counterparties/client_list.html`
- `src/templates/base.html`
- существующая цепочка миграций

Эти файлы нельзя рефакторить casually.

## 5. Что обязательно делать после изменений

Всегда запускать:

```powershell
cd src
..\.venv\Scripts\python.exe manage.py check
..\.venv\Scripts\python.exe manage.py test
```

И всегда:

- вручную проверять затронутый UI-сценарий;
- отдельно проверять auth flow, если менялся доступ сотрудников;
- обновлять документацию, если менялись правила, структура или поведение.

## 6. Как работать с `todo.md`

`todo.md` обязателен для агента.

- читать перед началом работы;
- обновлять статус выполненных задач;
- добавлять найденные новые задачи;
- не считать работу завершённой, если `todo.md` остался неактуальным относительно результатов.

## 7. Как фиксировать неопределённость

Использовать только явные метки:

- `Unknown`
- `Assumption`
- `Needs verification`

Нельзя превращать предположение в факт.

## 8. Когда обязательно обновлять docs

Если меняется хотя бы одно из ниже:

- env vars;
- команды запуска;
- структура модулей;
- архитектурные ограничения;
- поведение фич;
- риски;
- постоянные правила работы агента.

Минимум обновлений:

- `README.md`
- один или несколько файлов в `docs/`
- `todo.md`
- `.codex/working-rules.md`, если изменились стабильные правила работы
