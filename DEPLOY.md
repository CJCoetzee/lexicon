# Deploying Lexicon to Render

This walks you through deploying both the Flask backend and the React
frontend to Render's free tier using the included `render.yaml` blueprint.

Estimated time: 10–15 minutes. Estimated cost: $0 (free tier).

---

## 1. Push the latest code to GitHub

The blueprint reads from your repo, so make sure everything you want
deployed is on `main`:

```
git checkout main
git pull
git push origin main
```

Confirm the file `render.yaml` exists at the repo root.

## 2. Create a Blueprint on Render

1. Go to https://dashboard.render.com and sign in with GitHub.
2. Click **New** → **Blueprint**.
3. Select the `lexicon` repository. Render reads `render.yaml` and shows
   you the two services it will create: `lexicon-backend` and
   `lexicon-frontend`.
4. Click **Apply Blueprint**.

Render will begin building both services. The backend takes the longest
because it installs Chroma and friends — expect 4–6 minutes.

## 3. Set backend environment variables

While the backend is building, click into the `lexicon-backend` service:

1. **Environment** tab → **Add Environment Variable**:
   - `GEMINI_API_KEY` — paste your key (the same one in `backend/.env`)
   - `CORS_ORIGINS` — leave blank for now; we'll set it once the frontend has a URL

2. Click **Save Changes**. The service will redeploy.

## 4. Confirm the backend is up

When the backend status shows **Live**, copy its URL — it'll look like
`https://lexicon-backend-XXXX.onrender.com`. Test it:

```
curl https://lexicon-backend-XXXX.onrender.com/healthz
```

You should get `{"status":"ok"}`.

> **Free tier note:** Render's free web services sleep after 15 minutes of
> inactivity. The first request after a sleep takes 30–60s to wake. For the
> demo, hit `/healthz` once before recording to warm it up.

## 5. Set frontend environment variables

Click into the `lexicon-frontend` service:

1. **Environment** tab → **Add Environment Variable**:
   - `VITE_API_BASE_URL` = the backend URL you just copied
2. Click **Save Changes**.

The frontend rebuilds (about 2 minutes). When it goes **Live**, copy its
URL — `https://lexicon-frontend-XXXX.onrender.com`.

## 6. Update the backend's CORS_ORIGINS

Go back to `lexicon-backend` → Environment, set:

- `CORS_ORIGINS` = the frontend URL from step 5

Save. Backend redeploys.

## 7. Smoke test

Open the frontend URL in a browser. You should see the Lexicon UI. Upload a
small TXT file and ask a question. Verify:

- Document appears in the left list
- Chat answer appears in the right panel with `[n]` citations
- Citation list under the answer is populated
- Clicking `[1]` opens the citation list and highlights the source

If all four are green, deployment is complete.

## 8. Lock the URLs into the repo

Update `README.md` so graders can find your live deployment:

```markdown
- **Frontend:** https://lexicon-frontend-XXXX.onrender.com
- **Backend API:** https://lexicon-backend-XXXX.onrender.com
```

Commit and push.

---

## Troubleshooting

**Backend build fails on Chroma / sqlite.** Render's stock image has the
right sqlite version, so this should "just work". If it doesn't, add
`pysqlite3-binary` to `requirements.txt` and a small shim at the top of
`app.py`:

```python
import sys
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules['pysqlite3']
```

**`401`/`403` from Gemini after deploy.** Re-check `GEMINI_API_KEY` in the
backend's Environment tab — Render hides values after save, so re-paste it
if unsure.

**`CORS error` in the browser console.** `CORS_ORIGINS` must exactly match
your frontend URL, including `https://` and no trailing slash.

**Chroma data disappeared.** Expected on the free tier — Render free
services run on ephemeral storage. The index resets on restart and after
the free-tier sleep wakes the service back up. Re-upload your documents
when this happens. If you need persistence, upgrade `lexicon-backend` to a
paid tier ($7/mo) and add a `disk:` block to `render.yaml` mounting at
`/var/data` with `CHROMA_PERSIST_DIR=/var/data/chroma`.
