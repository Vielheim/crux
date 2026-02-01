# Crux

**Crux** is a comprehensive climbing analysis platform. It uses Computer Vision (Pose Estimation) to analyze climbing ascents, score performance, and track progress.

## 🏗 Architecture

The platform consists of the following containerized services:

- **Frontend**: React (Vite + TypeScript + Tailwind)
- **Backend**: Python (FastAPI + SQLAlchemy + AsyncPG)
- **Worker**: Python (ARQ + Redis) for background video processing
- **Database**: PostgreSQL
- **Storage**: MinIO (S3-compatible object storage)
- **Infrastructure**: Nginx (Reverse Proxy)

## 🚀 Quick Start

The entire stack is containerized. You only need Docker to run the application.

### 1. Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running.

### 2. Setup Environment

Copy the example environment file to create your local configuration:

```bash
cp .env.example .env
```

### 3. Start the Stack

Run the following command to build and start all services:

```bash
docker-compose up --build -d

```

Once running, the services are accessible at:

| Service      | URL                                                      | Description                          |
| ------------ | -------------------------------------------------------- | ------------------------------------ |
| **Web App**  | [http://localhost:5173](http://localhost:5173)           | Frontend Dev Server (Hot Reload)     |
| **API**      | [http://localhost:8000](http://localhost:8000)           | Backend API                          |
| **API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Swagger UI                           |
| **MinIO**    | [http://localhost:9001](http://localhost:9001)           | S3 Console (User/Pass in `.env`)     |
| **Proxy**    | [http://localhost](http://localhost)                     | Nginx (Simulates Production Routing) |

### 4. Stop the Stack

To stop containers:

```bash
docker-compose down

```

To stop and **destroy** database/storage volumes (reset data):

```bash
docker-compose down -v

```

---

## 📂 Project Structure

- `backend/` - FastAPI application, database models, and CV logic.
- `frontend/` - React application.
- `nginx/` - Reverse proxy configuration.
