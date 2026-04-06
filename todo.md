# TODO

`todo.md` — основной рабочий список проекта. Перед началом работы его нужно читать, после выполнения задач — обновлять.

## In Progress

- [ ] Устранить архитектурный долг `analogs`: вынести интеграции ABCP/МойСклад и убрать `print()` из обработки ошибок.
- [ ] Снизить связность [`src/counterparties/views.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/counterparties/views.py): постепенно выносить повторяемую workspace-логику в отдельный слой без смены URL и query-параметров.

## Backlog

- [ ] Убрать хардкод `storeId` из [`src/analogs/views.py`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/analogs/views.py) в конфигурацию.
- [ ] Добавить автотесты для `counterparties`: поиск, выбор клиента, CRUD клиента, CRUD автомобиля.
- [ ] Добавить автотесты для `analogs` с моками ABCP и МойСклад.
- [ ] Вынести крупные inline CSS/JS из [`src/templates/base.html`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/templates/base.html) и [`src/templates/counterparties/client_list.html`](/C:/Users/lipyf/GitHub/AutoPartsSync/src/templates/counterparties/client_list.html) в управляемую статику.
- [ ] Проверить и при необходимости нормализовать кодировку пользовательских строк в шаблонах и Python-файлах, не меняя подтверждённое поведение.
- [ ] При необходимости разделить `src/employees/tests.py` на тематические тестовые модули без изменения покрытия.

## Done

- [x] Провести аудит структуры проекта, архитектуры, конфигурации, тестов и workflow разработки.
- [x] Обновить `README.md` по фактическому состоянию кода.
- [x] Обновить `docs/architecture.md` с описанием модулей, слоёв, зависимостей и нарушений архитектуры.
- [x] Обновить `docs/architecture-rules.md` с правилами разработки и антипаттернами.
- [x] Обновить `docs/requirements.md` по реализованным фичам и ограничениям.
- [x] Обновить `docs/employee-auth-plan.md` как статус реализации employee-auth.
- [x] Обновить `Agent.md`, `CONTRIBUTING.md` и `.codex/working-rules.md` под единый процесс работы.
- [x] Создать и зафиксировать `todo.md` как основной файл плана.
