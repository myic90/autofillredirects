# Redirect Resolver - browser-based starter

This project gives you a browser-based tool for resolving redirected URLs from an Excel file.

## Recommended hosting model
- Frontend: Vercel Hobby plan
- Backend: Render free web service

This keeps the UI simple for your team:
1. Open the site in the browser
2. Upload the spreadsheet
3. Choose the source and output columns
4. Download the completed file

## Included features
- Upload `.xlsx`, `.xls`, or `.xlsm`
- Choose worksheet
- Choose source column by column letter or header name
- Choose output column by column letter or header name
- Choose start row
- Choose timeout
- Automatically download the completed file

## Folder structure
- `frontend/` — static browser UI for Vercel
- `backend/` — FastAPI service for Render
- `backend/render.yaml` — optional Render blueprint
- `frontend/vercel.json` — rewrite config

## 1. Deploy the backend to Render

### A. Create a GitHub repo
Push this project to GitHub.

### B. Create a Render web service
In Render:
- New > Web Service
- Connect your GitHub repo
- Root directory: `backend`
- Environment: Python
- Build command:
  `pip install -r requirements.txt && mkdir -p static && cp ../frontend/index.html static/index.html`
- Start command:
  `uvicorn main:app --host 0.0.0.0 --port $PORT`

Or use the included `render.yaml`.

### C. Note your backend URL
It will look like:
`https://your-service-name.onrender.com`

## 2. Deploy the frontend to Vercel

### A. Import the same repo into Vercel
Choose the `frontend` directory as the root.

### B. Update `frontend/vercel.json`
Replace:
`https://YOUR-RENDER-SERVICE.onrender.com`
with your actual Render backend URL.

### C. Deploy
Vercel will host the browser UI, and all `/api/...` requests will be proxied to Render.

## 3. Team usage
Share the Vercel URL with your team.

## Notes and limitations
- Render free services can sleep after inactivity, so the first request may be slower.
- Some websites block automated requests, so a few rows may return `ERROR: ...` even when a link works in a normal browser.
- This starter is best for public URLs.
- For heavier team usage, move the backend to a paid Render plan.

## Local development
Backend:
`cd backend`
`pip install -r requirements.txt`
`mkdir -p static`
`cp ../frontend/index.html static/index.html`
`uvicorn main:app --reload`
