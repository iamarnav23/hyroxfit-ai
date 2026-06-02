# HYROXFit AI Frontend

Stage 6 frontend for HYROXFit AI with Supabase Auth.

## Run

```bash
npm install
npm run dev
```

Open:

```text
http://127.0.0.1:3000
```

Create `.env.local` from `.env.local.example` before testing auth:

```text
NEXT_PUBLIC_SUPABASE_URL=
NEXT_PUBLIC_SUPABASE_ANON_KEY=
NEXT_PUBLIC_API_BASE_URL=http://127.0.0.1:8000
```

The form sends data to `/api/generate-plan`, which forwards the request and
Supabase access token to the FastAPI backend at:

```text
http://127.0.0.1:8000/generate-plan
```
