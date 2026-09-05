import re
from typing import Dict, Any, List, Optional
from backend.query_tool import QueryTool
from backend.forecasting_tool import ForecastingTool

class AIOrchestrator:
    """
    AI Routing and Orchestration Engine.
    Interprets natural language queries, maps them to structured tool calls,
    executes computation via backend tools, and constructs explainability metadata.
    """
    def __init__(self):
        self.query_tool = QueryTool()
        self.forecasting_tool = ForecastingTool()

    def process_query(self, user_question: str) -> Dict[str, Any]:
        question_lower = user_question.lower().strip()

        # Route 1: Forecasting tool
        if any(kw in question_lower for kw in ["predict", "forecast", "future", "demand", "inventory", "plan"]):
            return self._handle_forecasting(user_question, question_lower)

        # Route 2: Analytics Query tool
        return self._handle_analytics(user_question, question_lower)

    def _handle_forecasting(self, user_question: str, q_lower: str) -> Dict[str, Any]:
        # Extract months
        months = 4
        month_match = re.search(r"(\d+)\s*month", q_lower)
        if month_match:
            months = int(month_match.group(1))

        # Extract SKU or Category
        sku = None
        category = None

        # Check common categories
        for cat in ["PAPER", "CRAYON", "BOOK", "PENCIL", "STICKER", "MARKER", "BRUSH"]:
            if cat.lower() in q_lower:
                category = cat
                break

        # Check SKU match like PAPER-0197 or SKU X
        sku_match = re.search(r"\b([a-zA-Z]+-\d+)\b", user_question)
        if sku_match:
            sku = sku_match.group(1).upper()

        forecast_res = self.forecasting_tool.predict_demand(
            sku=sku,
            product_category=category,
            months_ahead=months,
            method="exponential_smoothing"
        )

        return {
            "intent": "predictive_forecasting",
            "user_question": user_question,
            "tool_used": "ForecastingTool.predict_demand",
            "answer": forecast_res["recommendation"],
            "chart_type": "line",
            "chart_data": forecast_res["combined_chart_data"],
            "data_table": forecast_res["combined_chart_data"],
            "explainability": {
                "applied_filters": {
                    "sku": sku or "All SKUs",
                    "product_category": category or "All Categories",
                    "forecast_horizon_months": months
                },
                "metrics_and_dimensions": ["month (dimension)", "quantity (metric)", "type (historical vs forecast)"],
                "query_plan": f"1. Aggregate historical monthly order quantity from SQLite DB. 2. Apply Single Exponential Smoothing (alpha=0.4) over history. 3. Project demand for {months} months ahead. 4. Calculate 20% safety stock and inventory procurement target.",
                "methodology": forecast_res["methodology"]
            }
        }

    def _handle_analytics(self, user_question: str, q_lower: str) -> Dict[str, Any]:
        # Determine query pattern
        if "carrier" in q_lower and ("highest" in q_lower or "delay" in q_lower or "worst" in q_lower):
            select = "carrier, COUNT(*) as total_orders, SUM(CASE WHEN status='delayed' THEN 1 ELSE 0 END) as delayed_orders, ROUND(CAST(SUM(CASE WHEN status='delayed' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 2) as delay_rate_pct"
            group_by = "carrier"
            order_by = "delay_rate_pct DESC"
            data = self.query_tool.execute_analytical_query(select, group_by=group_by, order_by=order_by)

            top_carrier = data[0] if data else {}
            answer = f"The carrier with the highest delay rate is {top_carrier.get('carrier', 'N/A')} with a delay rate of {top_carrier.get('delay_rate_pct', 0)}% ({top_carrier.get('delayed_orders', 0)} delayed out of {top_carrier.get('total_orders', 0)} total orders)."

            return {
                "intent": "carrier_delay_analysis",
                "user_question": user_question,
                "tool_used": "QueryTool.execute_analytical_query",
                "answer": answer,
                "chart_type": "bar",
                "chart_data": [{"name": r["carrier"], "delay_rate": r["delay_rate_pct"], "total_orders": r["total_orders"]} for r in data],
                "data_table": data,
                "explainability": {
                    "applied_filters": {"status": "All statuses evaluated"},
                    "metrics_and_dimensions": ["carrier (dimension)", "delay_rate_pct (metric)", "total_orders (metric)"],
                    "query_plan": "GROUP BY carrier, aggregate total and delayed order counts, compute delay_rate_pct = (delayed / total) * 100, and ORDER BY delay_rate_pct DESC.",
                    "sql_executed": f"SELECT {select} FROM logistics GROUP BY {group_by} ORDER BY {order_by};"
                }
            }

        elif "by week" in q_lower or "weekly" in q_lower:
            select = "strftime('%Y-%W', order_date) as week, COUNT(*) as total_orders, SUM(CASE WHEN status='delayed' THEN 1 ELSE 0 END) as delayed_orders"
            group_by = "week"
            order_by = "week ASC"
            data = self.query_tool.execute_analytical_query(select, group_by=group_by, order_by=order_by)

            total_delayed = sum(r['delayed_orders'] for r in data)
            answer = f"There were {total_delayed} delayed orders in total across {len(data)} weekly tracking periods."

            return {
                "intent": "weekly_delayed_orders",
                "user_question": user_question,
                "tool_used": "QueryTool.execute_analytical_query",
                "answer": answer,
                "chart_type": "line",
                "chart_data": [{"name": f"W{r['week']}", "delayed_orders": r["delayed_orders"], "total_orders": r["total_orders"]} for r in data],
                "data_table": data,
                "explainability": {
                    "applied_filters": {"time_grouping": "weekly"},
                    "metrics_and_dimensions": ["week (dimension)", "delayed_orders (metric)", "total_orders (metric)"],
                    "query_plan": "Extract year-week format via strftime('%Y-%W'), filter/sum delayed status orders, and order chronologically.",
                    "sql_executed": f"SELECT {select} FROM logistics GROUP BY {group_by} ORDER BY {order_by};"
                }
            }

        elif "category" in q_lower or "product" in q_lower:
            select = "product_category, COUNT(*) as total_orders, SUM(order_value_usd) as total_value, SUM(CASE WHEN status='delivered' THEN 1 ELSE 0 END) as delivered"
            group_by = "product_category"
            order_by = "total_orders DESC"
            data = self.query_tool.execute_analytical_query(select, group_by=group_by, order_by=order_by)

            answer = f"Found {len(data)} product categories. Top category by volume is {data[0]['product_category']} with {data[0]['total_orders']} orders."

            return {
                "intent": "category_breakdown",
                "user_question": user_question,
                "tool_used": "QueryTool.execute_analytical_query",
                "answer": answer,
                "chart_type": "bar",
                "chart_data": [{"name": r["product_category"], "total_orders": r["total_orders"], "total_value": r["total_value"]} for r in data],
                "data_table": data,
                "explainability": {
                    "applied_filters": {},
                    "metrics_and_dimensions": ["product_category (dimension)", "total_orders (metric)", "total_value (metric)"],
                    "query_plan": "GROUP BY product_category, compute total order count and total order value in USD.",
                    "sql_executed": f"SELECT {select} FROM logistics GROUP BY {group_by} ORDER BY {order_by};"
                }
            }

        # General/Default breakdown (e.g. status breakdown or order summary)
        select = "status, COUNT(*) as count, ROUND(SUM(order_value_usd), 2) as value"
        group_by = "status"
        order_by = "count DESC"
        data = self.query_tool.execute_analytical_query(select, group_by=group_by, order_by=order_by)

        status_summary = ", ".join([f"{r['status']}: {r['count']}" for r in data])
        answer = f"Logistics order status breakdown: {status_summary}."

        return {
            "intent": "status_breakdown",
            "user_question": user_question,
            "tool_used": "QueryTool.execute_analytical_query",
            "answer": answer,
            "chart_type": "pie",
            "chart_data": [{"name": r["status"], "value": r["count"]} for r in data],
            "data_table": data,
            "explainability": {
                "applied_filters": {},
                "metrics_and_dimensions": ["status (dimension)", "count (metric)", "value (metric)"],
                "query_plan": "GROUP BY status to count order distributions and calculate revenue values.",
                "sql_executed": f"SELECT {select} FROM logistics GROUP BY {group_by} ORDER BY {order_by};"
            }
        }
