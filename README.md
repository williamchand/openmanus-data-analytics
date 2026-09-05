# AI-Powered Logistics Analytics & Forecasting Platform

A full-stack AI-powered logistics analytics application featuring descriptive KPI dashboards, dynamic diagnostic SQL queries, predictive time-series demand forecasting, and structured explainability auditing.

---

## 🌟 Overview & Key Features

1. **Descriptive Operational Analytics Dashboard**:
   - Live KPI cards: Total Orders, Delivered Orders, Delayed Orders, On-Time Delivery Rate (%), Average Delivery Time (days), Total Revenue ($).
   - Interactive visualizations: Monthly Order Volume & Delivery Performance trend lines, Carrier Delay Rate & Volume breakdowns.

2. **AI-Orchestrated Natural Language Interface**:
   - Query logistics data conversationally (e.g., *"Which carrier has the highest delay rate?"*, *"Show delayed orders by week for the last 3 months"*).
   - Automated tool routing: Determines whether to execute structured SQL analytics or predictive demand forecasting.
   - Dynamic Chart Rendering: Automatically selects appropriate visual charts (Bar, Line, Pie) based on response data.

3. **Predictive & Prescriptive Demand Forecasting Tool**:
   - Forecasting algorithms: Single Exponential Smoothing, Simple Moving Average, Linear Regression.
   - Predicts future monthly demand for specific SKUs or product categories.
   - Generates inventory stock targets and 20% safety stock procurement recommendations.

4. **Explainability & Computation Audit**:
   - Transparent metadata detailing applied filters, metrics & dimensions, query execution plan/SQL executed, and interactive underlying data table preview.

---

## 🛠️ Data Handling & Database Schema

The platform uses a unified dataset (`mock_logistics_data.csv` - 400 order records) synced with a relational database (supports **Supabase PostgreSQL** and **SQLite**).

### Schema (`logistics` table)
- `client_id` (TEXT / VARCHAR)
- `order_id` (TEXT / VARCHAR, PRIMARY KEY)
- `order_date` (DATE)
- `delivery_date` (DATE)
- `carrier` (VARCHAR)
- `origin_city` (VARCHAR)
- `destination_city` (VARCHAR)
- `status` (VARCHAR)
- `sku` (VARCHAR)
- `product_category` (VARCHAR)
- `quantity` (INTEGER)
- `unit_price_usd` (NUMERIC)
- `order_value_usd` (NUMERIC)
- `is_promo` (INTEGER)
- `promo_discount_pct` (NUMERIC)
- `region` (VARCHAR)
- `warehouse` (VARCHAR)

---

## 🚀 Local Quick Start Setup

### Prerequisites
- Python 3.12+
- Node.js 18+ & npm

### 1. Database Ingestion (SQLite Local)
Run the migration script to generate and populate `logistics.db`:
```bash
python scripts/migrate_to_sqlite.py
```

### 2. Backend API Setup
Install dependencies and run the FastAPI server:
```bash
pip install -r requirements.txt
PYTHONPATH=. uvicorn backend.main:app --host 0.0.0.0 --port 8000
```
Backend API interactive docs will be available at: `http://localhost:8000/docs`

### 3. Frontend Dashboard Setup
In a new terminal window:
```bash
cd frontend
npm install
npm run dev -- --port 3000
```
Access the application dashboard at: `http://localhost:3000`

---

## ☁️ Tutorial: Deployment to Supabase PostgreSQL & Vercel

Follow these step-by-step instructions to deploy the production dataset to **Supabase PostgreSQL** and host the frontend on **Vercel**.

### Step 1: Supabase PostgreSQL Setup & Data Migration

1. **Create Supabase Project**:
   - Log in to [Supabase](https://supabase.com) and create a new project.
2. **Obtain Connection String**:
   - Go to **Project Settings** -> **Database**.
   - Copy the **URI Connection String** under *Connection string* (Transaction/Session Pooler or Direct connection).
   - Format: `postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres`
3. **Execute Migration Script**:
   - Set the `DATABASE_URL` environment variable and run the migration script:
   ```bash
   export DATABASE_URL="postgresql://postgres:[YOUR-PASSWORD]@db.[YOUR-PROJECT-REF].supabase.co:5432/postgres"
   python scripts/migrate_to_postgres.py
   ```
   - The script automatically creates the `logistics` table, builds indexes, and inserts all 400 records.

---

### Step 2: Backend API Deployment (Render / AWS / Railway / Vercel Serverless)

1. Deploy the Python FastAPI backend to your cloud host (e.g. Render, Railway, or AWS EC2).
2. Configure the Cloud Environment Variable:
   - `DATABASE_URL`: Your Supabase connection string.
3. Verify backend health endpoint once deployed: `https://your-backend-api.onrender.com/api/health`

---

### Step 3: Vercel Frontend Deployment

1. **Push Code to GitHub**:
   - Commit and push your code to your GitHub repository.
2. **Deploy on Vercel**:
   - Log in to [Vercel](https://vercel.com) and click **Add New** -> **Project**.
   - Select your GitHub repository.
   - Set **Root Directory** to `frontend`.
   - Build Settings:
     - Framework Preset: **Vite**
     - Build Command: `npm run build`
     - Output Directory: `dist`
3. **Configure Environment Variables in Vercel**:
   - Under **Environment Variables**, add:
     - `VITE_API_BASE_URL`: `https://your-backend-api.onrender.com` (Your deployed backend API URL)
4. **Deploy**:
   - Click **Deploy**. Vercel will build and assign a publicly accessible HTTPS URL (e.g., `https://logistics-analytics.vercel.app`).

---

## 🏗️ System Architecture & AI Orchestration Flow

### Flow Architecture
```
User Question
    │
    ▼
AI Orchestrator (backend/ai_orchestrator.py)
    │
    ├────────────► Query Tool (backend/query_tool.py) ──► PostgreSQL / SQLite
    │
    └────────────► Forecasting Tool (backend/forecasting_tool.py) ──► Time Series Model
    │
    ▼
Structured Result + Explainability Audit + Dynamic Chart
```

### Security & SQL Safety
- Direct execution of arbitrary raw user SQL is strictly prevented.
- Queries are validated against forbidden DDL/DML keywords (`DROP`, `DELETE`, `INSERT`, `UPDATE`, `ALTER`).
- All data queries use parameterized or verified read-only SQL clauses.

---

## 🧪 Testing & Verification

Run the full Python backend test suite:
```bash
python -m pytest tests/test_api.py tests/test_tools.py
```

---

## 📌 Assumptions, Simplifications & Limitations

1. **Dataset Scope**: Operates on 400 fixed logistics order records covering 2025-2026.
2. **Read-Only Operation**: All database operations treat records as read-only.
3. **Forecasting Model**: Employs Single Exponential Smoothing (alpha=0.4) and 3-month Moving Average for stable, interpretable time-series demand estimation.

---

## 🔮 Future Improvements

1. **Advanced ML Forecasting**: Integrate Prophet or ARIMA models for seasonal decomposition.
2. **LLM Function Calling**: Upgrade AI orchestrator to use OpenAI / Anthropic tool use APIs for multi-step reasoning.
3. **Real-time Streaming**: Implement WebSockets for live order status updates and alert notifications.
