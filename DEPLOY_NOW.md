# Deploy to Railway — Step by Step

## What you have
- ✅ Neon PostgreSQL
- ✅ Qdrant Cloud
- ⏳ Cloudflare R2 (activating — not needed for first deploy)

---

## Step 1 — Push this folder to GitHub

1. Go to github.com → New repository → name it `melamine-backend` → Create
2. Then run these commands in your terminal inside this folder:

```bash
git init
git add .
git commit -m "initial backend"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/melamine-backend.git
git push -u origin main
```

---

## Step 2 — Deploy on Railway

1. Go to **railway.app** → New Project
2. Click **"Deploy from GitHub repo"**
3. Select `melamine-backend`
4. Railway auto-detects Python and starts building

**That's it.** Railway will:
- Install dependencies
- Run `alembic upgrade head` (creates all DB tables)
- Run `python -m app.db.seed` (creates users + 30 products)
- Start the API server

---

## Step 3 — Get your public URL

In Railway dashboard:
- Click your service → **Settings** → **Networking** → **Generate Domain**
- You'll get: `https://melamine-backend-xxxx.up.railway.app`

Test it:
```
https://melamine-backend-xxxx.up.railway.app/health
→ {"status":"ok","version":"1.0.0"}

https://melamine-backend-xxxx.up.railway.app/api/docs
→ Full Swagger UI
```

---

## Step 4 — Connect to Lovable

In your Lovable project, set the API base URL to:
```
https://melamine-backend-xxxx.up.railway.app
```

See `LOVABLE_INTEGRATION.md` for the full API client code to paste into Lovable.

---

## Step 5 — Add R2 later (optional)

Once you have R2 Access Key ID + Secret, add these in Railway → Variables:
```
R2_ACCESS_KEY_ID=your_key_id
R2_SECRET_ACCESS_KEY=your_secret
USE_LOCAL_STORAGE=false
```

Railway will redeploy automatically and images will go to R2.

---

## Default Credentials

| Role  | Email                  | Password   |
|-------|------------------------|------------|
| Admin | admin@melamine.com     | admin1234  |
| Staff | staff@melamine.com     | staff1234  |

