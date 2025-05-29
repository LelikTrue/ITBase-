
*(Self-correction: Based on our recent discussion, `app/` should contain `api/`, `db/`, `models/`, etc., and `schema.sql` is more of a reference for initial setup than a primary component if Alembic is used.)*

## 🔄 Миграции базы данных (Alembic)

Проект использует Alembic для управления схемой базы данных. Вот основные команды:

1.  **Применение всех ожидающих миграций:**

    ```bash
    docker compose exec backend alembic upgrade head
    ```

2.  **Создание новой миграции** (после внесения изменений в модели SQLAlchemy):

    ```bash
    docker compose exec backend alembic revision --autogenerate -m "Описание ваших изменений"
    ```

3.  **Откат последней миграции:**

    ```bash
    docker compose exec backend alembic downgrade -1
    ```

## 🛠 Доступные API-конечные точки

*   `GET /` - Перенаправляет на панель управления.
*   `GET /dashboard` - Основной веб-интерфейс для обзора ИТ-активов.
*   `GET /api/v1/assets` - Получение списка всех активов (конечная точка JSON API).
*   `POST /api/v1/assets` - Добавление нового актива.
*   `GET /assets/add` - Веб-форма для добавления нового актива.
*   `GET /docs` - Интерактивная документация API (Swagger UI).
*   `GET /redoc` - Альтернативная документация API (ReDoc).

*(Self-correction: Added more endpoints based on our discussion, like POST /api/v1/assets and GET /assets/add, for clarity.)*

## 🔒 Аутентификация (если применимо)

*Этот раздел будет заполнен после реализации аутентификации. Пока это заглушка.*

В настоящее время проект сосредоточен на основной функциональности управления активами. Механизмы аутентификации будут интегрированы в будущих фазах разработки.

Если вы разрабатываете и хотите протестировать конечные точки API, которые в будущем могут быть защищены, вот пример того, как это может выглядеть:

```bash
curl -X 'GET' \
  'http://localhost/api/protected-route' \
  -H 'Authorization: Bearer your-jwt-token'