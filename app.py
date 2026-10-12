import os
import traceback
from pathlib import Path

import razorpay
from fastapi import FastAPI, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from dotenv import load_dotenv

from core_engine import (
    extract_text,
    extract_entities,
    location_score,
    connectivity_score,
    lifestyle_score,
    extract_price,
    affordability_analysis,
    investment_grade,
    confidence_score,
    score_color,
    geocode_location
)

load_dotenv()

app = FastAPI(
    title="Property Intelligence API",
    version="2.0.0"
)

client = razorpay.Client(auth=(os.getenv("RAZORPAY_KEY_ID", ""), os.getenv("RAZORPAY_KEY_SECRET", "")))

from razorpay_utils import verify_payment_signature

# ==================================================
# HEALTH CHECK
# ==================================================

@app.get("/")
def home():
    return {
        "status": "running",
        "message": "Property Intelligence API Online"
    }


@app.get("/payment", response_class=HTMLResponse)
def payment_page():
    html_path = Path(__file__).parent / "assets" / "razorpay_checkout.html"
    html_content = html_path.read_text(encoding="utf-8")
    html_content = html_content.replace("{{RAZORPAY_KEY_ID}}", os.getenv("RAZORPAY_KEY_ID", ""))
    return HTMLResponse(content=html_content)


@app.post("/api/create-order")
async def create_order(request: Request):
    try:
        payload = await request.json()
    except ValueError:
        return JSONResponse(status_code=400, content={"status": "failed", "message": "Invalid JSON payload"})

    amount = payload.get("amount")
    currency = payload.get("currency", "INR")
    receipt = payload.get("receipt", "property-intelligence")

    try:
        amount = int(amount) * 100
    except (TypeError, ValueError):
        return JSONResponse(status_code=400, content={"status": "failed", "message": "Amount must be a valid integer"})

    if amount < 100:
        return JSONResponse(status_code=400, content={"status": "failed", "message": "Amount must be at least 100 paise"})

    try:
        order_data = {
            "amount": amount,
            "currency": currency,
            "receipt": receipt,
        }
        order = client.order.create(data=order_data)
        return {
            "status": "success",
            "order_id": order["id"],
            "amount": order["amount"],
            "currency": order["currency"],
        }
    except Exception as exc:
        error_message = str(exc)
        status_code = 401 if "auth" in error_message.lower() or "key" in error_message.lower() else 500
        return JSONResponse(status_code=status_code, content={"status": "failed", "message": error_message})


@app.post("/api/verify-payment")
async def verify_payment(request: Request):
    try:
        payload = await request.json()
    except ValueError:
        return JSONResponse(status_code=400, content={"status": "failed", "message": "Invalid JSON payload"})

    order_id = payload.get("razorpay_order_id")
    payment_id = payload.get("razorpay_payment_id")
    signature = payload.get("razorpay_signature")

    if not order_id or not payment_id or not signature:
        return JSONResponse(status_code=400, content={"status": "failed", "message": "Missing payment fields"})

    is_valid = verify_payment_signature(order_id, payment_id, signature)

    if is_valid:
        return {"status": "success", "message": "Payment verified"}

    return JSONResponse(status_code=400, content={"status": "failed", "message": "Signature mismatch"})


# ==================================================
# MAIN ENDPOINT
# ==================================================

@app.post("/analyze-property")
async def analyze(
    file: UploadFile = File(...),
    monthly_income: float = Form(0),
    existing_emi: float = Form(0),
    down_payment: float = Form(0)
):

    try:

        # ==================================================
        # READ FILE
        # ==================================================

        file_bytes = await file.read()

        text = extract_text(
            file_bytes,
            file.filename
        )

        print(
            f"Processing file: "
            f"{file.filename}"
        )        

        if not text or len(text.strip()) < 20:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "failed",
                    "message": "Insufficient or unreadable text extracted"
                }
            )

        # ==================================================
        # ENTITY EXTRACTION
        # ==================================================

        entities = extract_entities(text)

        location = entities.get("location", "Unknown")

        location = entities.get("location", "Unknown")

        print("\n====================")
        print("LOCATION FOUND:", location)

        geo_location = geocode_location(location)

        print("GEO LOCATION:", geo_location)
        print("====================\n")

        # ==================================================
        # GEO LOCATION
        # ==================================================

        geo_location = geocode_location(location)

        # ==================================================
        # SCORING
        # ==================================================

        loc_score = location_score(location)
        conn_score = connectivity_score(text)
        life_score = lifestyle_score(text)

        property_price = extract_price(text)

        print("\n======================")
        print("PROPERTY PRICE:", property_price)
        print("MONTHLY INCOME:", monthly_income)
        print("DOWN PAYMENT:", down_payment)
        print("======================\n")

        # ==================================================
        # INVESTMENT SCORE
        # ==================================================

        inv_score = round(
            (
                loc_score * 0.35
                + conn_score * 0.25
                + life_score * 0.25
                + 15
            ),
            2
        )

        inv_score = min(inv_score, 100)
        risk_score = round(100 - inv_score, 2)

        # ==================================================
        # VERDICT
        # ==================================================

        if inv_score >= 80:
            verdict = "STRONG BUY"
        elif inv_score >= 65:
            verdict = "BUY"
        elif inv_score >= 50:
            verdict = "HOLD"
        else:
            verdict = "AVOID"

        # ==================================================
        # AFFORDABILITY
        # ==================================================

# ==================================================
# AFFORDABILITY
# ==================================================

        affordability = None
        wealth_ratio = None

        try:

            if (
                property_price
                and monthly_income
                and monthly_income > 0
            ):

                affordability = affordability_analysis(
                    property_price=property_price,
                    monthly_income=monthly_income,
                    existing_emi=existing_emi,
                    down_payment=down_payment
                )

                affordability["property_price"] = property_price

                affordability["down_payment"] = down_payment

                affordability["loan_to_value"] = round(
                    (
                        property_price - down_payment
                    ) / property_price * 100,
                    2
                )

                annual_income = monthly_income * 12

                wealth_ratio = round(
                    property_price / annual_income,
                    2
                )

        except Exception as e:

            print("Affordability Error:", e)

            affordability = None
            wealth_ratio = None

        # ==================================================
        # SUMMARY
        # ==================================================

        summary = f"""
PROPERTY INTELLIGENCE REPORT

Location:
{location}

Builder:
{entities.get("builder", "Unknown")}

Property Size:
{entities.get("size_sqft", "Unknown")} sq.ft

Property Price:
₹{property_price:,.0f}
""" if property_price else f"""
PROPERTY INTELLIGENCE REPORT

Location:
{location}

Builder:
{entities.get("builder", "Unknown")}

Property Size:
{entities.get("size_sqft", "Unknown")} sq.ft
"""

        summary += f"""

Investment Score:
{inv_score}/100

Risk Score:
{risk_score}/100

Recommendation:
{verdict}
"""

        if affordability:

            summary += f"""

Estimated EMI:
₹{affordability.get("estimated_emi", 0):,.0f}

Debt Ratio:
{affordability.get("debt_ratio", 0)}%

Affordability:
{affordability.get("affordability_rating", "N/A")}
"""

        # ==================================================
        # RESPONSE
        # ==================================================

        response = {
            "status": "success",

            "summary": summary,

            "location": location,

            "builder": entities.get("builder"),

            "property_size": entities.get("size_sqft"),

            "property_price": property_price,

            "entities": entities,

            "scores": {
                "investment": inv_score,
                "risk": risk_score,
                "location": loc_score,
                "connectivity": conn_score,
                "lifestyle": life_score
            },

            "geo_location": geo_location,
            "affordability": affordability,
            "wealth_ratio": wealth_ratio,
            "verdict": verdict,

            "grade": investment_grade(inv_score),

            "confidence": confidence_score(entities),

            "score_color": score_color(inv_score),

            "document_preview": text[:3000]
        }

        return response

    except Exception as e:

        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": str(e),
                "trace": traceback.format_exc()
            }
        )

