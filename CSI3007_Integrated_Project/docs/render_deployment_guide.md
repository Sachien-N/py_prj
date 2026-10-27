# Free Online Hosting & Deployment Guide (Render, Streamlit Cloud & Railway)

This guide provides step-by-step instructions for hosting the **CSI3007 Integrated Project** online for free.

---

## Deployment Options Overview

| Deployment Method | Platform | Cost | Recommended For |
|---|---|---|---|
| **Option 1: Render Blueprints (Multi-Service)** | [Render.com](https://render.com) | **Free** | Official submission showing 3 truly independent hosted web services + APIs. |
| **Option 2: Render Single Web Service** | [Render.com](https://render.com) | **Free** | Easiest 1-click deployment running all 3 apps + landing gateway on 1 free Render instance. |
| **Option 3: Streamlit Community Cloud + Render** | [Streamlit Cloud](https://streamlit.io/cloud) & Render | **Free** | Free Streamlit hosting for frontends, free Render instance for FastAPI backends. |

---

## Option 1: Automated Deployment on Render using `render.yaml`

Render offers a **Free Tier** for Web Services. With the included `render.yaml` Blueprint file, you can automatically deploy all backends and frontends in minutes.

### Step 1: Push Repository to GitHub
1. Create a new GitHub repository (e.g., `CSI3007-Integrated-Project`).
2. Push your project code:
   ```bash
   git init
   git add .
   git commit -m "Initial commit for CSI3007 Integrated Project"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/CSI3007-Integrated-Project.git
   git push -u origin main
   ```

### Step 2: Deploy Blueprint on Render
1. Sign up / Log in to [Render.com](https://render.com).
2. Click **New +** in the top right corner and select **Blueprint**.
3. Connect your GitHub repository.
4. Render will automatically detect `render.yaml` and display all 7 web services:
   - `csi3007-gateway` (Landing Page Gateway)
   - `csi3007-person-a-api` (FastAPI - Person A)
   - `csi3007-person-a-ui` (Streamlit - Person A)
   - `csi3007-person-b-api` (FastAPI - Person B)
   - `csi3007-person-b-ui` (Streamlit - Person B)
   - `csi3007-person-c-api` (FastAPI - Person C)
   - `csi3007-person-c-ui` (Streamlit - Person C)
5. Select **Free Plan** for each service and click **Apply**.
6. Render will build and deploy each service. Once complete, you will receive public HTTPS URLs for each application!

---

## Option 2: Deploying as a Single Free Web Service on Render

If you prefer to stay strictly within Render's single free web service limit, you can run all services or the integrated gateway in 1 Web Service instance!

1. On Render, click **New +** -> **Web Service**.
2. Connect your GitHub repository.
3. Configure the settings:
   - **Name**: `csi3007-integrated-project`
   - **Environment**: `Python`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python run_cloud.py --service all`
   - **Plan**: `Free`
4. Click **Create Web Service**. Your landing page and services will be live at `https://csi3007-integrated-project.onrender.com`!

---

## Option 3: Hosting Streamlit Frontends on Streamlit Community Cloud (100% Free)

Streamlit Community Cloud provides unlimited free hosting for Streamlit applications directly connected to GitHub!

### Step 1: Deploy FastAPI Backends on Render
Deploy `csi3007-person-a-api`, `csi3007-person-b-api`, and `csi3007-person-c-api` as Web Services on Render (or Railway).

### Step 2: Deploy Streamlit Dashboards on Streamlit Cloud
1. Go to [share.streamlit.io](https://share.streamlit.io) and log in with GitHub.
2. Click **New App**.
3. Select your repository, branch (`main`), and path to the Streamlit app:
   - **Person A**: `person_a_sachien_n_23MID0255/app.py`
   - **Person B**: `person_b_shravan_n_a_23MID0445/app.py`
   - **Person C**: `person_c_hariharan_s_23MID0182/app.py`
4. Expand **Advanced Settings** -> **Secrets / Environment Variables** and enter:
   ```toml
   API_BASE_URL = "https://your-person-a-api.onrender.com"
   ```
5. Click **Deploy!** Your Streamlit app will be live on `https://your-app.streamlit.app`.

---

## Cross-Application API Integration in Production

When hosted online, update the API URLs in each application's environment variables or `.env` so that Person A, Person B, and Person C can communicate across their live HTTPS endpoints:

### Person A Environment Variables (`.env`)
```env
API_BASE_URL=https://csi3007-person-a-api.onrender.com
PERSON_B_API_URL=https://csi3007-person-b-api.onrender.com
PERSON_C_API_URL=https://csi3007-person-c-api.onrender.com
PERSON_B_SYNC_API_KEY=dev-person-b-to-a-key
PERSON_C_SYNC_API_KEY=dev-person-c-to-a-key
CORS_ORIGINS=*
```

### Person B Environment Variables (`.env`)
```env
API_BASE_URL=https://csi3007-person-b-api.onrender.com
PERSON_A_API_URL=https://csi3007-person-a-api.onrender.com
PERSON_A_SYNC_API_KEY=dev-person-b-to-a-key
CORS_ORIGINS=*
```

### Person C Environment Variables (`.env`)
```env
API_BASE_URL=https://csi3007-person-c-api.onrender.com
PERSON_A_API_URL=https://csi3007-person-a-api.onrender.com
PERSON_A_SYNC_API_KEY=dev-person-c-to-a-key
CORS_ORIGINS=*
```

---

## Database Persistence Notice

Each application uses SQLite databases (`data/person_a.db`, `data/person_b.db`, `data/person_c.db`).
- On free hosting tiers (like Render or Streamlit Cloud), local SQLite files reset whenever the server restarts after inactivity.
- For permanent data retention in production, you can attach a free **Render Persistent Disk** or connect to a free cloud PostgreSQL database (such as Supabase, Neon, or ElephantSQL) by setting `DATABASE_URL` in environment variables:
  ```env
  DATABASE_URL=postgresql://user:password@host:5432/dbname
  ```

---

## Troubleshooting Cloud Deployments

1. **Service Timeout / Cold Start**:
   Render's free tier spins down services after 15 minutes of inactivity. The first request after spin-down may take 30-50 seconds to respond ("cold start").
2. **CORS Errors**:
   Ensure `CORS_ORIGINS=*` is set in the environment variables of all FastAPI backends.
3. **Port Binding**:
   Render dynamically assigns the `$PORT` environment variable. The project automatically uses `$PORT` when deployed.
