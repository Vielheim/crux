# Crux Backend

The backend API for **Crux**. Built with **FastAPI**, **PostgreSQL**, **Redis**, and **MinIO**.

## 🛠️ Developer Workflow

The backend is designed to run inside Docker to ensure consistency with the production environment (especially for system-level dependencies like OpenCV).

### 1. Running the Server

The backend starts automatically with the main `docker-compose up` command in the root directory.

- **Hot Reload:** The `api` service maps the local `backend/` folder to the container. Changes to `*.py` files will auto-reload the server.

### 2. Database Migrations (Alembic)

We use **Alembic** for schema migrations. All commands should be run _inside_ the docker container.

**Create a new migration (after modifying `models.py`):**

```bash
# -m "message" describes the change
docker-compose exec api alembic revision --autogenerate -m "Added climber profile"
```

**Apply migrations:**

```bash
# This runs automatically on container startup, but can be run manually:
docker-compose exec api alembic upgrade head

```

### 3. Running Tests

Tests run in an isolated environment inside Docker.

```bash
# Run all tests
docker-compose exec apipytest

# Run tests with output (print statements)
docker-compose exec api pytest -s
```

### 4. Managing Dependencies

If you add a package to `requirements.txt`:

1. Add the package to `requirements.txt`.
2. Rebuild the container to install the new dependency:

```bash
docker-compose up -d --build api
```

## 📐 Project Structure

```text
backend/
├── alembic/             # Database migration versions
├── app/
│   ├── main.py          # API Routes & Entrypoint
│   ├── models.py        # SQLAlchemy Database Models
│   ├── schemas.py       # Pydantic Schemas (Validation)
│   ├── worker.py        # Background Task Logic (CV Analysis)
│   └── database.py      # DB Connection Setup
├── tests/               # Pytest Suite
└── docker-compose.yml   # (Reference to root compose)

```
