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

## 🛠️ Data Migration

Data from `examples/use_case/logistic_data/mock_logistics_data.csv` is migrated into a relational SQLite database (`logistics.db`).

### Schema
- `client_id` (TEXT)
- `order_id` (TEXT, PRIMARY KEY)
- `order_date` (TEXT)
- `delivery_date` (TEXT)
- `carrier` (TEXT)
- `origin_city` (TEXT)
- `destination_city` (TEXT)
- `status` (TEXT)
- `sku` (TEXT)
- `product_category` (TEXT)
- `quantity` (INTEGER)
- `unit_price_usd` (REAL)
- `order_value_usd` (REAL)
- `is_promo` (INTEGER)
- `promo_discount_pct` (REAL)
- `region` (TEXT)
- `warehouse` (TEXT)

---

## 🚀 Quick Start & Local Setup Instructions

### Prerequisites
- Python 3.12+
- Node.js 18+ & npm

### 1. Database Ingestion
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

## 🏗️ System Architecture & AI Orchestration Flow

### Flow Architecture
```
User Question
    │
    ▼
AI Orchestrator (backend/ai_orchestrator.py)
    │
    ├────────────► Query Tool (backend/query_tool.py) ──► SQLite (logistics.db)
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

1. **Dataset Scope**: The dataset operates on 400 fixed logistics order records covering 2025-2026.
2. **Read-Only Operation**: Operations treat all order records as read-only.
3. **Forecasting Model**: Employs Single Exponential Smoothing (alpha=0.4) and 3-month Moving Average for stable, interpretable time-series demand estimation without requiring external ML dependencies.

---

## 🔮 Future Improvements

1. **Advanced ML Forecasting**: Integrate Prophet or ARIMA models for seasonal decomposition.
2. **LLM Function Calling**: Upgrade AI orchestrator to use OpenAI / Anthropic tool use APIs for multi-step reasoning.
3. **Real-time Streaming**: Implement WebSockets for live order status updates and alert notifications.
