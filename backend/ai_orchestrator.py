import json
import os
import re
from typing import Any, Dict, Optional

import httpx

from backend.forecasting_tool import ForecastingTool
from backend.query_tool import QueryTool


class AIOrchestrator:
    """
    AI Routing and Orchestration Engine.
    Interprets natural language queries, maps them to structured tool calls,
    executes computation via backend tools, and constructs explainability metadata.
    Supports real LLM invocation via Nvidia API (NVIDIA NIM) or OpenAI API,
    with robust local rule fallback when API keys are not provided.
    """

    def __init__(self):
        self.query_tool = QueryTool()
        self.forecasting_tool = ForecastingTool()

        self.nvidia_api_key = os.environ.get("NVIDIA_API_KEY")
        self.openai_api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get(
            "LLM_API_KEY"
        )

        self.api_key = self.nvidia_api_key or self.openai_api_key

        if self.nvidia_api_key:
            self.base_url = os.environ.get(
                "NVIDIA_BASE_URL", "https://integrate.api.nvidia.com/v1"
            )
            self.model = os.environ.get("NVIDIA_MODEL", "meta/llama-3.1-8b-instruct")
            self.provider_name = "Nvidia API (NVIDIA NIM)"
        elif self.openai_api_key:
            self.base_url = os.environ.get(
                "OPENAI_BASE_URL", "https://api.openai.com/v1"
            )
            self.model = os.environ.get("LLM_MODEL", "gpt-4o-mini")
            self.provider_name = "OpenAI API"
        else:
            self.base_url = None
            self.model = None
            self.provider_name = "Local Rule Engine"

    def process_query(self, user_question: str) -> Dict[str, Any]:
        question_lower = user_question.lower().strip()

        # Try real LLM interpretation if API key is present
        if self.api_key:
            llm_result = self._call_llm_orchestrator(user_question)
            if llm_result:
                return llm_result

        # Fallback to local rule engine
        # Route 1: Forecasting tool
        if any(
            kw in question_lower
            for kw in ["predict", "forecast", "future", "demand", "inventory", "plan"]
        ):
            return self._handle_forecasting(user_question, question_lower)

        # Route 2: Analytics Query tool
        return self._handle_analytics(user_question, question_lower)

    def _call_llm_orchestrator(self, user_question: str) -> Optional[Dict[str, Any]]:
        """
        Calls Nvidia API or OpenAI API to dynamically classify and extract structured query parameters.
        """
        prompt = f"""
You are an AI logistics analytics query router.
Analyze the user's question and select the correct tool.

Database Schema:
table `logistics` (
    client_id, order_id, order_date (YYYY-MM-DD), delivery_date, carrier,
    origin_city, destination_city, status ('delivered', 'delayed', 'canceled', 'in_transit', 'exception'),
    sku, product_category, quantity, unit_price_usd, order_value_usd, is_promo, region, warehouse
)

Available Tools:
1. `ForecastingTool`: predict demand for a SKU or category over future months.
2. `QueryTool`: execute analytical SQL aggregation on the `logistics` table.

User Question: "{user_question}"

Respond with ONLY a JSON object in the following format:
{{
  "tool": "ForecastingTool" or "QueryTool",
  "intent": "short_intent_name",
  "select_clause": "SQL select clause without SELECT, e.g. carrier, COUNT(*) as total",
  "group_by": "GROUP BY clause, e.g. carrier or 1 or null",
  "where_clause": "WHERE condition e.g. status='delayed' AND order_date >= '2025-01-01' or null",
  "order_by": "ORDER BY clause e.g. total DESC or null",
  "sku": "SKU code if forecasting, e.g. PAPER-0197 or null",
  "product_category": "Category if forecasting or null",
  "months_ahead": 4
}}
"""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        url = f"{self.base_url.rstrip('/')}/chat/completions"
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
            "max_tokens": 500,
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, headers=headers, json=payload)
                if res.status_code == 200:
                    content = res.json()["choices"][0]["message"]["content"].strip()
                    # Clean markdown formatting if present
                    content = re.sub(r"^```json\s*", "", content)
                    content = re.sub(r"\s*```$", "", content)
                    parsed = json.loads(content)

                    tool = parsed.get("tool")
                    if tool == "ForecastingTool":
                        sku = parsed.get("sku")
                        category = parsed.get("product_category")
                        months = parsed.get("months_ahead") or 4
                        forecast_res = self.forecasting_tool.predict_demand(
                            sku=sku, product_category=category, months_ahead=months
                        )
                        return {
                            "intent": parsed.get("intent", "predictive_forecasting"),
                            "user_question": user_question,
                            "tool_used": f"ForecastingTool via {self.provider_name}",
                            "answer": forecast_res["recommendation"],
                            "chart_type": "line",
                            "chart_data": forecast_res["combined_chart_data"],
                            "data_table": forecast_res["combined_chart_data"],
                            "explainability": {
                                "applied_filters": {
                                    "sku": sku or "All SKUs",
                                    "product_category": category or "All Categories",
                                    "forecast_horizon_months": months,
                                    "llm_provider": self.provider_name,
                                },
                                "metrics_and_dimensions": ["month", "quantity", "type"],
                                "query_plan": f"LLM parsed query -> ForecastingTool using Exponential Smoothing for {months} months.",
                                "methodology": forecast_res["methodology"],
                            },
                        }
                    elif tool == "QueryTool":
                        select_c = parsed.get("select_clause") or "COUNT(*) as count"
                        group_c = parsed.get("group_by")
                        where_c = parsed.get("where_clause")
                        order_c = parsed.get("order_by")

                        data = self.query_tool.execute_analytical_query(
                            select_clause=select_c,
                            group_by=group_c,
                            where_clause=where_c,
                            order_by=order_c,
                        )

                        chart_type = "bar"
                        if group_c and (
                            "week" in group_c.lower()
                            or "month" in group_c.lower()
                            or "date" in group_c.lower()
                        ):
                            chart_type = "line"
                        elif "status" in (group_c or "").lower():
                            chart_type = "pie"

                        first_row = data[0] if data else {}
                        answer = f"Query executed successfully via {self.provider_name}. Returned {len(data)} summary rows."
                        if (
                            "count" in str(first_row).lower()
                            or "total" in str(first_row).lower()
                        ):
                            answer = f"Result: {json.dumps(first_row)}."

                        return {
                            "intent": parsed.get("intent", "llm_analytical_query"),
                            "user_question": user_question,
                            "tool_used": f"QueryTool via {self.provider_name}",
                            "answer": answer,
                            "chart_type": chart_type,
                            "chart_data": data,
                            "data_table": data,
                            "explainability": {
                                "applied_filters": {
                                    "where_clause": where_c or "None",
                                    "llm_provider": self.provider_name,
                                },
                                "metrics_and_dimensions": [select_c],
                                "query_plan": f"LLM generated structured SQL clause: SELECT {select_c} FROM logistics WHERE {where_c} GROUP BY {group_c} ORDER BY {order_c}.",
                                "sql_executed": f"SELECT {select_c} FROM logistics"
                                + (f" WHERE {where_c}" if where_c else "")
                                + (f" GROUP BY {group_c}" if group_c else "")
                                + (f" ORDER BY {order_c}" if order_c else "")
                                + ";",
                            },
                        }
        except Exception as e:
            print(
                f"LLM Orchestrator call failed, falling back to local rule engine: {e}"
            )

        return None

    def _handle_forecasting(self, user_question: str, q_lower: str) -> Dict[str, Any]:
        months = 4
        month_match = re.search(r"(\d+)\s*month", q_lower)
        if month_match:
            months = int(month_match.group(1))

        sku = None
        category = None

        for cat in ["PAPER", "CRAYON", "BOOK", "PENCIL", "STICKER", "MARKER", "BRUSH"]:
            if cat.lower() in q_lower:
                category = cat
                break

        sku_match = re.search(r"\b([a-zA-Z]+-\d+)\b", user_question)
        if sku_match:
            sku = sku_match.group(1).upper()

        forecast_res = self.forecasting_tool.predict_demand(
            sku=sku,
            product_category=category,
            months_ahead=months,
            method="exponential_smoothing",
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
                    "forecast_horizon_months": months,
                    "llm_provider": self.provider_name,
                },
                "metrics_and_dimensions": [
                    "month (dimension)",
                    "quantity (metric)",
                    "type (historical vs forecast)",
                ],
                "query_plan": f"1. Aggregate historical monthly order quantity. 2. Apply Single Exponential Smoothing (alpha=0.4). 3. Project demand for {months} months ahead. 4. Calculate 20% safety stock and inventory procurement target.",
                "methodology": forecast_res["methodology"],
            },
        }

    def _handle_analytics(self, user_question: str, q_lower: str) -> Dict[str, Any]:
        # Handle "delivered late last month" / delayed count
        if (
            "delivered late" in q_lower
            or "late last month" in q_lower
            or "delayed" in q_lower
            and "last month" in q_lower
        ):
            select = "COUNT(*) as delayed_count, ROUND(SUM(order_value_usd), 2) as delayed_value"
            where_c = "status = 'delayed'"
            data = self.query_tool.execute_analytical_query(
                select, where_clause=where_c
            )

            delayed_count = data[0].get("delayed_count", 0) if data else 0
            delayed_val = data[0].get("delayed_value", 0.0) if data else 0.0
            answer = f"There were {delayed_count} orders delivered late / delayed in the evaluated period (total order value: ${delayed_val:,.2f})."

            return {
                "intent": "late_orders_summary",
                "user_question": user_question,
                "tool_used": "QueryTool.execute_analytical_query",
                "answer": answer,
                "chart_type": "bar",
                "chart_data": [
                    {
                        "name": "Delayed Orders",
                        "count": delayed_count,
                        "value": delayed_val,
                    }
                ],
                "data_table": data,
                "explainability": {
                    "applied_filters": {
                        "status": "delayed",
                        "llm_provider": self.provider_name,
                    },
                    "metrics_and_dimensions": [
                        "delayed_count (metric)",
                        "delayed_value (metric)",
                    ],
                    "query_plan": "Filter status = 'delayed' to sum late order count and order value.",
                    "sql_executed": f"SELECT {select} FROM logistics WHERE {where_c};",
                },
            }

        if "carrier" in q_lower and (
            "highest" in q_lower or "delay" in q_lower or "worst" in q_lower
        ):
            select = "carrier, COUNT(*) as total_orders, SUM(CASE WHEN status='delayed' THEN 1 ELSE 0 END) as delayed_orders, ROUND(CAST(SUM(CASE WHEN status='delayed' THEN 1 ELSE 0 END) AS FLOAT) / COUNT(*) * 100, 2) as delay_rate_pct"
            group_by = "carrier"
            order_by = "delay_rate_pct DESC"
            data = self.query_tool.execute_analytical_query(
                select, group_by=group_by, order_by=order_by
            )

            top_carrier = data[0] if data else {}
            answer = f"The carrier with the highest delay rate is {top_carrier.get('carrier', 'N/A')} with a delay rate of {top_carrier.get('delay_rate_pct', 0)}% ({top_carrier.get('delayed_orders', 0)} delayed out of {top_carrier.get('total_orders', 0)} total orders)."

            return {
                "intent": "carrier_delay_analysis",
                "user_question": user_question,
                "tool_used": "QueryTool.execute_analytical_query",
                "answer": answer,
                "chart_type": "bar",
                "chart_data": [
                    {
                        "name": r["carrier"],
                        "delay_rate": r["delay_rate_pct"],
                        "total_orders": r["total_orders"],
                    }
                    for r in data
                ],
                "data_table": data,
                "explainability": {
                    "applied_filters": {
                        "status": "All statuses evaluated",
                        "llm_provider": self.provider_name,
                    },
                    "metrics_and_dimensions": [
                        "carrier (dimension)",
                        "delay_rate_pct (metric)",
                        "total_orders (metric)",
                    ],
                    "query_plan": "GROUP BY carrier, aggregate total and delayed order counts, compute delay_rate_pct = (delayed / total) * 100, and ORDER BY delay_rate_pct DESC.",
                    "sql_executed": f"SELECT {select} FROM logistics GROUP BY {group_by} ORDER BY {order_by};",
                },
            }

        elif "by week" in q_lower or "weekly" in q_lower:
            select = "strftime('%Y-%W', order_date) as week, COUNT(*) as total_orders, SUM(CASE WHEN status='delayed' THEN 1 ELSE 0 END) as delayed_orders"
            group_by = "1"
            order_by = "1 ASC"
            data = self.query_tool.execute_analytical_query(
                select, group_by=group_by, order_by=order_by
            )

            total_delayed = sum(r["delayed_orders"] for r in data)
            answer = f"There were {total_delayed} delayed orders in total across {len(data)} weekly tracking periods."

            return {
                "intent": "weekly_delayed_orders",
                "user_question": user_question,
                "tool_used": "QueryTool.execute_analytical_query",
                "answer": answer,
                "chart_type": "line",
                "chart_data": [
                    {
                        "name": f"W{r['week']}",
                        "delayed_orders": r["delayed_orders"],
                        "total_orders": r["total_orders"],
                    }
                    for r in data
                ],
                "data_table": data,
                "explainability": {
                    "applied_filters": {
                        "time_grouping": "weekly",
                        "llm_provider": self.provider_name,
                    },
                    "metrics_and_dimensions": [
                        "week (dimension)",
                        "delayed_orders (metric)",
                        "total_orders (metric)",
                    ],
                    "query_plan": "Extract year-week format, filter/sum delayed status orders, and order chronologically.",
                    "sql_executed": f"SELECT {select} FROM logistics GROUP BY {group_by} ORDER BY {order_by};",
                },
            }

        elif "category" in q_lower or "product" in q_lower:
            select = "product_category, COUNT(*) as total_orders, SUM(order_value_usd) as total_value, SUM(CASE WHEN status='delivered' THEN 1 ELSE 0 END) as delivered"
            group_by = "product_category"
            order_by = "total_orders DESC"
            data = self.query_tool.execute_analytical_query(
                select, group_by=group_by, order_by=order_by
            )

            answer = f"Found {len(data)} product categories. Top category by volume is {data[0]['product_category']} with {data[0]['total_orders']} orders."

            return {
                "intent": "category_breakdown",
                "user_question": user_question,
                "tool_used": "QueryTool.execute_analytical_query",
                "answer": answer,
                "chart_type": "bar",
                "chart_data": [
                    {
                        "name": r["product_category"],
                        "total_orders": r["total_orders"],
                        "total_value": r["total_value"],
                    }
                    for r in data
                ],
                "data_table": data,
                "explainability": {
                    "applied_filters": {
                        "llm_provider": self.provider_name,
                    },
                    "metrics_and_dimensions": [
                        "product_category (dimension)",
                        "total_orders (metric)",
                        "total_value (metric)",
                    ],
                    "query_plan": "GROUP BY product_category, compute total order count and total order value in USD.",
                    "sql_executed": f"SELECT {select} FROM logistics GROUP BY {group_by} ORDER BY {order_by};",
                },
            }

        select = "status, COUNT(*) as count, ROUND(SUM(order_value_usd), 2) as value"
        group_by = "status"
        order_by = "count DESC"
        data = self.query_tool.execute_analytical_query(
            select, group_by=group_by, order_by=order_by
        )

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
                "applied_filters": {
                    "llm_provider": self.provider_name,
                },
                "metrics_and_dimensions": [
                    "status (dimension)",
                    "count (metric)",
                    "value (metric)",
                ],
                "query_plan": "GROUP BY status to count order distributions and calculate revenue values.",
                "sql_executed": f"SELECT {select} FROM logistics GROUP BY {group_by} ORDER BY {order_by};",
            },
        }
