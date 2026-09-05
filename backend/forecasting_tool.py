from datetime import datetime
from typing import Any, Dict, Optional

from backend.db import IS_POSTGRES, execute_query, get_placeholder


class ForecastingTool:
    """
    Forecasting tool for predicting future logistics demand based on historical data.
    Supports Moving Average, Linear Regression, and Exponential Smoothing methods.
    Supports both SQLite and PostgreSQL (Supabase).
    """

    def __init__(self):
        pass

    def predict_demand(
        self,
        sku: Optional[str] = None,
        product_category: Optional[str] = None,
        months_ahead: int = 4,
        method: str = "exponential_smoothing",
    ) -> Dict[str, Any]:
        where_clauses = []
        params = []
        placeholder = get_placeholder()

        if sku:
            where_clauses.append(f"LOWER(sku) = LOWER({placeholder})")
            params.append(sku)
        if product_category:
            where_clauses.append(f"LOWER(product_category) = LOWER({placeholder})")
            params.append(product_category)

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        if IS_POSTGRES:
            month_expr = "to_char(order_date::date, 'YYYY-MM')"
        else:
            month_expr = "strftime('%Y-%m', order_date)"

        sql = f"""
        SELECT
            {month_expr} as month,
            SUM(quantity) as total_quantity,
            COUNT(*) as total_orders,
            SUM(order_value_usd) as total_revenue
        FROM logistics
        {where_sql}
        GROUP BY month
        ORDER BY month ASC;
        """

        rows = execute_query(sql, tuple(params))

        if not rows:
            return {
                "error": f"No historical data found for target filter (SKU: {sku}, Category: {product_category}).",
                "historical_data": [],
                "forecast_data": [],
                "recommendation": "Maintain baseline safety stock based on default operational policy.",
                "methodology": "No historical data available.",
            }

        historical_months = [r["month"] for r in rows]
        historical_quantities = [float(r["total_quantity"]) for r in rows]

        historical_series = [
            {"month": m, "quantity": q, "type": "historical"}
            for m, q in zip(historical_months, historical_quantities)
        ]

        last_month_str = historical_months[-1]
        last_dt = datetime.strptime(last_month_str + "-01", "%Y-%m-%d")

        future_months = []
        curr_dt = last_dt
        for _ in range(months_ahead):
            year = curr_dt.year + (curr_dt.month // 12)
            month = (curr_dt.month % 12) + 1
            curr_dt = datetime(year, month, 1)
            future_months.append(curr_dt.strftime("%Y-%m"))

        forecast_quantities = []
        methodology_desc = ""

        n = len(historical_quantities)
        if method == "moving_average" or n < 3:
            window = min(3, n)
            avg_val = sum(historical_quantities[-window:]) / window
            forecast_quantities = [round(avg_val, 1)] * months_ahead
            methodology_desc = f"Simple Moving Average ({window}-month window) calculated from recent historical trend."

        elif method == "linear_regression":
            x = list(range(n))
            y = historical_quantities
            x_mean = sum(x) / n
            y_mean = sum(y) / n

            num = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
            den = sum((x[i] - x_mean) ** 2 for i in range(n))
            b = num / den if den != 0 else 0
            a = y_mean - b * x_mean

            for step in range(1, months_ahead + 1):
                pred = a + b * (n - 1 + step)
                forecast_quantities.append(round(max(0, pred), 1))
            methodology_desc = f"Linear Regression (Ordinary Least Squares) capturing linear growth/decline trend (slope: {b:.2f})."

        else:
            alpha = 0.4
            s = historical_quantities[0]
            for val in historical_quantities[1:]:
                s = alpha * val + (1 - alpha) * s

            forecast_quantities = [round(s, 1)] * months_ahead
            methodology_desc = f"Single Exponential Smoothing (alpha={alpha}) dampening high-frequency variance and giving higher weight to recent demand."

        forecast_series = [
            {"month": m, "quantity": q, "type": "forecast"}
            for m, q in zip(future_months, forecast_quantities)
        ]

        total_predicted = sum(forecast_quantities)
        avg_monthly_pred = total_predicted / months_ahead if months_ahead > 0 else 0
        safety_stock = round(avg_monthly_pred * 0.20, 1)
        recommended_inventory = round(total_predicted + safety_stock, 1)

        target_name = (
            sku if sku else (product_category if product_category else "all products")
        )

        recommendation = (
            f"For {target_name}, predicted demand over the next {months_ahead} months is {total_predicted:.1f} units "
            f"(avg {avg_monthly_pred:.1f} units/month). Recommended inventory stock target is {recommended_inventory:.1f} units "
            f"(including a 20% safety stock buffer of {safety_stock:.1f} units)."
        )

        return {
            "target": target_name,
            "sku": sku,
            "product_category": product_category,
            "months_ahead": months_ahead,
            "method": method,
            "methodology": methodology_desc,
            "historical_data": historical_series,
            "forecast_data": forecast_series,
            "combined_chart_data": historical_series + forecast_series,
            "summary_metrics": {
                "total_predicted_demand": total_predicted,
                "avg_monthly_demand": avg_monthly_pred,
                "safety_stock_buffer": safety_stock,
                "recommended_procurement_units": recommended_inventory,
            },
            "recommendation": recommendation,
        }
