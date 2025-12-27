# Crux Backend

The backend API for **Crux**, a climbing analysis platform. Built with **FastAPI**, **PostgreSQL**, **Redis**, and **MinIO** (S3).

## 🚀 Prerequisites

Ensure you have the following installed:

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

---

## 🛠️ Installation & Setup

1.  **Ensure you are in the backend directory:**

    ```bash
    cd crux/backend
    ```

2.  **Configure Environment Variables:**
    Copy the example environment file to create your local `.env`.

    ```bash
    cp .env.example .env
    ```

    > **Note:** The default settings in `.env.example` are pre-configured to work out-of-the-box with the Docker setup.

## ⚡ Core Commands

### **1. Build the Stack**

Builds the API container image. Run this after making changes to `requirements.txt` or the `Dockerfile`.

```bash
docker-compose build
```

### **2. Start the Application**

Starts all services (API, Postgres, Redis, MinIO) in the background.

```bash
docker-compose up -d
```

- **API:** [http://localhost:8000](https://www.google.com/search?q=http://localhost:8000)
- **API Docs:** [http://localhost:8000/docs](https://www.google.com/search?q=http://localhost:8000/docs)
- **MinIO Console:** [http://localhost:9001](https://www.google.com/search?q=http://localhost:9001) (User/Pass: See `.env` file)

### **3. Stop the Application**

Stops and removes all running containers.

```bash
docker-compose down

# To stop **and delete** all data volumes (database & S3 files), use:
docker-compose down -v
```

### **4. View Logs**

Follow the logs for all services or a specific one.

```bash
# All services
docker-compose logs -f

# Specific service (e.g., api, worker)
docker-compose logs -f api
```

## 🧪 Testing

Tests are run inside the Docker container to ensure they use the correct environment and dependencies.

### **Run All Tests**

```bash
docker-compose run --rm api pytest
```

### **Run Tests with Output**

If you want to see print statements or detailed output:

```bash
docker-compose run --rm api pytest -s -v
```

## 📂 Project Structure

```text
backend/
├── alembic/             # Database migrations
├── app/
│   ├── main.py          # App entrypoint & routes
│   ├── models.py        # SQLAlchemy database models
│   ├── schemas.py       # Pydantic validation schemas
│   ├── s3.py            # MinIO/S3 integration
│   ├── redis.py         # Redis connection setup
│   └── database.py      # DB connection setup
├── tests/               # Pytest suite
├── docker-compose.yml   # Infrastructure definition
├── requirements.txt     # Production dependencies
└── requirements-test.txt # Test dependencies
```
