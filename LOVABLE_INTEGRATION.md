# Connecting Your Lovable Frontend to This Backend

## Your Backend URL (after Railway deploy)
```
https://YOUR-APP.up.railway.app
```

## Step 1 — Add this to Lovable as an environment variable

In Lovable → Settings → Environment Variables:
```
VITE_API_URL=https://YOUR-APP.up.railway.app
```

## Step 2 — Paste this API client into your Lovable project

Create a file called `src/services/api.js` (or `.ts`) in Lovable:

```javascript
import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || 'https://YOUR-APP.up.railway.app'

const api = axios.create({
  baseURL: `${BASE_URL}/api/v1`,
})

// Auto-attach token to every request
api.interceptors.request.use(cfg => {
  const token = localStorage.getItem('melamine_token')
  if (token) cfg.headers.Authorization = `Bearer ${token}`
  return cfg
})

// Auto-logout on 401
api.interceptors.response.use(
  r => r,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('melamine_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// ── Auth ──────────────────────────────────────────────────────────────────────
export const login = async (email, password) => {
  const form = new FormData()
  form.append('username', email)
  form.append('password', password)
  const { data } = await api.post('/auth/login', form)
  localStorage.setItem('melamine_token', data.access_token)
  return data  // { access_token, user_id, role, full_name }
}

export const logout = () => {
  localStorage.removeItem('melamine_token')
}

export const getMe = () => api.get('/auth/me')

// ── Matching (core feature) ───────────────────────────────────────────────────
export const matchImage = async (file, onProgress) => {
  const form = new FormData()
  form.append('file', file)
  const { data } = await api.post('/match/', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: e => onProgress?.(Math.round((e.loaded * 100) / e.total)),
  })
  return data
  /*
  Returns:
  {
    upload_id: 1,
    query_color: { hex: "#A3B4C5", rgb_r: 163, rgb_g: 180, rgb_b: 197, lab_l: 72.1, ... },
    matches: [
      {
        match_result_id: 1,
        rank: 1,
        confidence_score: 0.91,   // 0.0 → 1.0
        color_delta_e: 4.2,        // lower = closer color
        score_breakdown: { vector_similarity: 0.94, color_score: 0.85 },
        product: {
          id: 3,
          code: "W980",
          name: "Alpine White",
          name_ar: "أبيض جبلي",
          finish: "matte",
          color_hex: "#F5F5F0",
          thickness_mm: 18,
          width_mm: 2800,
          length_mm: 2070,
          tags: ["white", "neutral"],
          reference_image_url: null
        }
      },
      ...up to 10 matches
    ]
  }
  */
}

export const getMatchHistory = (skip = 0, limit = 20) =>
  api.get('/match/history', { params: { skip, limit } })

// ── Feedback ──────────────────────────────────────────────────────────────────
export const submitFeedback = (matchResultId, type, notes = '') =>
  // type: "confirmed" | "rejected" | "corrected"
  api.post('/feedback/', {
    match_result_id: matchResultId,
    feedback_type: type,
    notes,
  })

// ── Products ──────────────────────────────────────────────────────────────────
export const getProducts = (params = {}) => api.get('/products/', { params })
export const getProduct = (id) => api.get(`/products/${id}`)

// ── Admin (admin role only) ───────────────────────────────────────────────────
export const getAdminStats = () => api.get('/admin/stats')
export const getUsers = () => api.get('/users/')
export const createUser = (data) => api.post('/users/', data)
export const getCompanies = () => api.get('/companies/')
export const getCatalogs = () => api.get('/catalogs/')
```

## Step 3 — Example: Match button in Lovable

```jsx
import { matchImage } from './services/api'
import { useState } from 'react'

export function MatchButton() {
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleFile = async (e) => {
    const file = e.target.files[0]
    if (!file) return
    setLoading(true)
    try {
      const data = await matchImage(file, (pct) => console.log(`${pct}%`))
      setResult(data)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div>
      <input type="file" accept="image/*" onChange={handleFile} />
      {loading && <p>Analyzing…</p>}
      {result?.matches.map(m => (
        <div key={m.match_result_id}>
          <h3>#{m.rank} — {m.product.name}</h3>
          <p>Match: {(m.confidence_score * 100).toFixed(1)}%</p>
          <p>Code: {m.product.code} | Finish: {m.product.finish}</p>
        </div>
      ))}
    </div>
  )
}
```

## Default Login Credentials

| Role | Email | Password |
|---|---|---|
| Admin | admin@melamine.com | admin1234 |
| Staff | staff@melamine.com | staff1234 |

## API Docs (Swagger)

Once deployed:
```
https://YOUR-APP.up.railway.app/api/docs
```
Use the **Authorize** button → enter email + password to test all endpoints interactively.

