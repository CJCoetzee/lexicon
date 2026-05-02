# Lexicon frontend

React + Vite + Tailwind frontend for Lexicon.

## Setup

```bash
npm install
npm run dev
```

Frontend runs on http://localhost:5173. Vite proxies `/api/*` to the Flask
backend on `http://localhost:5000` during development.

## Scripts

| Script           | Purpose                       |
|------------------|-------------------------------|
| `npm run dev`    | Start Vite dev server         |
| `npm run build`  | Production build to `dist/`   |
| `npm run lint`   | ESLint over all source files  |
| `npm test`       | Vitest test suite             |

## Production builds

`VITE_API_BASE_URL` controls the backend URL the build calls. Set it on
Render's frontend service to the deployed backend URL.
