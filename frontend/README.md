# Crux Frontend

The web client for **Crux**. Built with **React**, **TypeScript**, **Vite**, and **Tailwind CSS**.

## 🛠️ Developer Workflow

You can run the frontend either **inside Docker** (default, requires zero setup) or **Locally** (faster, requires Node.js).

### Option A: Running via Docker (Recommended)

This is the default behavior when running `docker-compose up` from the project root.

- **URL:** [http://localhost:5173](http://localhost:5173)
- **Hot Reload:** Enabled via volume mounts.

### Option B: Running Locally

If you prefer running outside Docker for performance:

1.  **Install Dependencies:**

    ```bash
    npm install
    ```

2.  **Start Dev Server:**

    ```bash
    npm run dev
    ```

3.  **Access:** [http://localhost:5173](http://localhost:5173)

### Linting & Code Quality

We use ESLint for code quality.

```bash
# Run Linter
npm run lint
```

## 🏗 Tech Stack

- **Vite**: Build tool and dev server.
- **React 19**: UI Library.
- **TypeScript**: Type safety.
- **Tailwind CSS 4**: Styling.
- **TanStack Query**: Data fetching and caching.

## 📂 Key Directories

```text
frontend/
├── src/
│   ├── components/      # Reusable UI components
│   ├── pages/           # Page-level components
│   ├── App.tsx          # Main application component
│   └── main.tsx         # Entry point
├── public/              # Static assets
└── package.json         # Dependencies and scripts

```
