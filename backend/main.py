from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from backend.query_tool import QueryTool
from backend.forecasting_tool import ForecastingTool
from backend.ai_orchestrator import AIOrchestrator

app = FastAPI(
    title="AI-Powered Logistics Analytics API",
    description="Backend service providing descriptive KPI queries, forecasting tools, and AI query orchestration.",
    version="1.0.0"
)

# Enable CORS for frontend web interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

query_tool = QueryTool()
forecasting_tool = ForecastingTool()
ai_orchestrator = AIOrchestrator()

class AskAIRequest(BaseModel):
    question: str

class ForecastRequest(BaseModel):
    sku: Optional[str] = None
    product_category: Optional[str] = None
    months_ahead: int = 4
    method: str = "exponential_smoothing"

@app.get("/api/health")
def health_check():
    return {"status": "healthy", "service": "Logistics Analytics Backend"}

@app.get("/api/kpis")
def get_kpis(days: Optional[int] = Query(None, description="Filter KPIs for the last N days")):
    try:
        return query_tool.get_dashboard_kpis(time_range_days=days)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/charts/order-volume")
def get_order_volume():
    try:
        data = query_tool.execute_analytical_query(
            select_clause="strftime('%Y-%m', order_date) as month, COUNT(*) as total_orders, SUM(CASE WHEN status='delivered' THEN 1 ELSE 0 END) as delivered, SUM(CASE WHEN status='delayed' THEN 1 ELSE 0 END) as delayed",
            group_by="month",
            order_by="month ASC"
        )
        return {"chart_data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/charts/delivery-performance")
def get_delivery_performance():
    try:
        data = query_tool.execute_analytical_query(
            select_clause="status, COUNT(*) as count",
            group_by="status",
            order_by="count DESC"
        )
        return {"chart_data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/charts/carrier-breakdown")
def get_carrier_breakdown():
    try:
        data = query_tool.execute_analytical_query(
            select_clause="carrier, COUNT(*) as total_orders, SUM(CASE WHEN status='delayed' THEN 1 ELSE 0 END) as delayed_orders, ROUND(CAST(SUM(CASE WHEN status='delayed' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 1) as delay_rate_pct",
            group_by="carrier",
            order_by="total_orders DESC"
        )
        return {"chart_data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/forecast")
def generate_forecast(req: ForecastRequest):
    try:
        return forecasting_tool.predict_demand(
            sku=req.sku,
            product_category=req.product_category,
            months_ahead=req.months_ahead,
            method=req.method
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ask-ai")
def ask_ai(req: AskAIRequest):
    if not req.question or not req.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    try:
        return ai_orchestrator.process_query(req.question)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
