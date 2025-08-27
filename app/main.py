from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Dict
from . import models, schemas, database
import os, requests, json, google.generativeai as genai
from datetime import datetime
import re
import logging

logger = logging.getLogger(__name__)

# --- Setup ---
models.Base.metadata.create_all(bind=database.engine)
app = FastAPI(title="SimplifyMoney KuberAI Simulation")

# -- Health Check Endpoint
@app.get("/", tags=["Health Check"])
async def read_root():
    return {"status": "ok", "message": "KuberAI is running"}

GOLD_API_KEY = os.getenv("GOLD_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Configuration of the Gemini AI ---
try:
    genai.configure(api_key=GEMINI_API_KEY)
    gemini_model = genai.GenerativeModel(model_name="gemini-1.5-flash")
except Exception:
    gemini_model = None

# --- Backup Data Helper ---
def get_backup_gold_data():
    try:
        with open('gold_data_backup.json', 'r') as f:
            data = json.load(f)
            return sorted(data, key=lambda x: datetime.fromisoformat(x['date']))
    except (FileNotFoundError, json.JSONDecodeError):
        return []

# --- Gold API helpers ---
def get_live_gold_price():
    if GOLD_API_KEY:
        try:
            url = "https://www.goldapi.io/api/XAU/INR"
            headers = {"x-access-token": GOLD_API_KEY, "Content-Type": "application/json"}
            r = requests.get(url, headers=headers, timeout=5)
            r.raise_for_status()
            data = r.json()
            if "price_gram_24k" in data:
                return {"source": "live", "current_price_inr_per_gram": round(data["price_gram_24k"], 2)}
        except Exception:
            pass

    backup_data = get_backup_gold_data()
    if backup_data:
        latest_entry = backup_data[-1]
        return {"source": "backup", "current_price_inr_per_gram": latest_entry['price']}

    return {"error": "Failed to fetch live gold price and backup is unavailable."}

def get_gold_price_history(days=30):
    if GOLD_API_KEY:
        try:
            url = f"https://www.goldapi.io/api/XAU/INR/history?period={days}d"
            headers = {"x-access-token": GOLD_API_KEY, "Content-Type": "application/json"}
            r = requests.get(url, headers=headers, timeout=5)
            r.raise_for_status()
            data = r.json()
            if isinstance(data, list) and data:
                history = [{"date": entry["date"], "price": round(entry["price"], 2)} for entry in data]
                return {"source": "live", "history": history}
        except Exception:
            pass

    backup_data = get_backup_gold_data()
    if backup_data:
        history = backup_data[-days:] if len(backup_data) >= days else backup_data
        return {"source": "backup", "history": history}

    return {"error": "Failed to fetch gold price history and backup is unavailable."}

# --- Trend analysis helper ---
def analyze_trend(history, period):
    """Returns percentage change over the given period."""
    if not history or len(history) < 2:
        return 0.0
    recent_prices = [entry['price'] for entry in history[-period:]]
    start_price = recent_prices[0]
    end_price = recent_prices[-1]
    percent_change = ((end_price - start_price) / start_price) * 100
    return percent_change

def generate_trend_text(history):
    """Generates readable trend text for 7-day and 30-day trends."""
    if not history:
        return "No sufficient data to determine trend."

    short_term = analyze_trend(history, period=7)
    long_term = analyze_trend(history, period=30 if len(history) >= 30 else len(history))

    def trend_phrase(change):
        if change > 0.1:
            return f"increased by {change:.2f}%"
        elif change < -0.1:
            return f"decreased by {abs(change):.2f}%"
        else:
            return "been relatively stable"

    return f"Gold prices have {trend_phrase(short_term)} over the last 7 days and have {trend_phrase(long_term)} over the last 30 days."

def _clean_text(s: str) -> str:
    """Normalize whitespace and collapse multiple newlines/spaces into single spaces."""
    if not s:
        return s
    return " ".join(s.split())

def _keyword_classify(question: str) -> str:
    q = question.lower()
    if any(k in q for k in ("price", "rate", "current", "today")):
        return "current_price"
    if any(k in q for k in ("history", "past", "last", "trend")):
        return "history"
    if any(k in q for k in ("predict", "forecast", "future", "will")):
        return "prediction"
    return "general_info"

def _is_gold_by_keyword(question: str) -> bool:
    return bool(re.search(r"\bgold\b|\bdigital gold\b|\bxau\b", question, flags=re.I))

# --- Conversational API ---

@app.post("/ask-kuber", response_model=schemas.KuberResponse, tags=["Conversational AI"])
async def ask_kuber_ai(request: schemas.QuestionRequest, db: Session = Depends(database.get_db)):
    user_question = request.question
    history, trend_insight = [], ""  

    try:
        # To detect gold-related question
        is_gold_query = _is_gold_by_keyword(user_question)
        if gemini_model:
            try:
                resp = gemini_model.generate_content(
                    f"Is this about gold? Answer yes or no: '{user_question}'"
                )
                is_gold_query = "yes" in resp.text.strip().lower()
            except Exception as e:
                logger.warning("Gemini detection failed: %s", e)

        extra_data = {}
        if is_gold_query:
            # To classify the intent
            classification = _keyword_classify(user_question)
            if gemini_model:
                try:
                    intent_prompt = f"""Classify "{user_question}" into: ["current_price", "history", "prediction", "general_info"]. Respond with one word."""
                    classification = gemini_model.generate_content(intent_prompt).text.strip().lower()
                except Exception as e:
                    logger.warning("Gemini intent classification failed: %s", e)

            # To fetch relevant data
            try:
                if "current_price" in classification:
                    extra_data = get_live_gold_price()
                elif "history" in classification:
                    extra_data = get_gold_price_history(days=30)
                elif "prediction" in classification:
                    extra_data = {"current": get_live_gold_price(), "history": get_gold_price_history(days=90)}
            except Exception as e:
                logger.warning("Error fetching gold data: %s", e)
                extra_data = {}

            # To ensure history exists from backup if live API failed
            history = extra_data.get("history") or get_backup_gold_data()
            if history:
                short_pct = analyze_trend(history, 7)
                long_pct = analyze_trend(history, 30 if len(history) >= 30 else len(history))
                trend_insight = f"If we look up on the trend insights then over the last 7 days, gold has changed by {short_pct:.2f}%. Over the last 30 days, it changed by {long_pct:.2f}%."

        # T generate AI response
        ai_response = None
        if gemini_model and is_gold_query:
            try:
                fusion_prompt = f"""
                You are KuberAI. User asked: "{user_question}".
                Data: {json.dumps(extra_data)}.
                Trend Analysis: {trend_insight}.
                Provide a clear answer, 3-4 short insights, and a nudge to invest.
                """
                ai_response = gemini_model.generate_content(fusion_prompt).text.strip()
            except Exception as e:
                logger.warning("Gemini fusion_prompt failed: %s", e)

        # T prepare the response
        if ai_response:
            parts = ai_response.split("\n\n", 1)
            answer = _clean_text(parts[0])
            extra_insights = _clean_text(parts[1] if len(parts) > 1 else "")
        else:
            # Fallback if AI fails
            if not is_gold_query:
                answer = "I can only help you with gold investment queries."
                extra_insights = "Please ask me a question about gold."
            else:
                answer = "Right now I'm unable to fetch live AI insights due to an API limit or server issue. The data coming is hard-coded and will resume the live response as soon as the API limit gets refreshed"
                extra_insights = (
                    "But here’s a helpful tip: Gold is a safe-haven asset. "
                    "On Simplify Money, you can instantly buy or sell 24K, 99.9% pure digital gold."
                )

        # Always appending trend_insight if available
        if trend_insight:
            extra_insights = f"{extra_insights} {trend_insight}".strip()

        simplify_suggestion = (
            "Simplify Money makes digital gold investment effortless: "
            "- Buy or sell 24K, 99.9% pure gold instantly. "
            "- Your gold is securely stored in insured vaults. "
            "- Start small with as little as ₹10."
        )
        nudge_text = "Would you like me to help you invest in digital gold on Simplify Money now?"

        return schemas.KuberResponse(
            is_gold_query=is_gold_query,
            answer=answer,
            extra_insights=extra_insights,
            simplify_suggestion=simplify_suggestion,
            nudge_text=nudge_text
        )

    except Exception as e:
        logger.exception(f"Unexpected error in ask_kuber_ai: {e}")
        # Final safety net returns fallback response with trend from backup
        history = get_backup_gold_data()
        trend_insight = ""
        if history:
            short_pct = analyze_trend(history, 7)
            long_pct = analyze_trend(history, 30 if len(history) >= 30 else len(history))
            trend_insight = f"If we look up on the trend insights then over the last 7 days, gold has changed by {short_pct:.2f}%. Over the last 30 days, it changed by {long_pct:.2f}%."

        extra_insights = (
            "But here’s a helpful tip: Gold is a safe-haven asset. "
            "On Simplify Money, you can instantly buy or sell 24K, 99.9% pure digital gold."
        )
        if trend_insight:
            extra_insights = f"{extra_insights}{trend_insight}".strip()

        return schemas.KuberResponse(
            is_gold_query=_is_gold_by_keyword(user_question),
            answer="Right now I'm unable to fetch live AI insights due to an API limit or server issue.",
            extra_insights=extra_insights,
            simplify_suggestion=(
                "Simplify Money makes digital gold investment effortless: "
                "- Buy or sell 24K, 99.9% pure gold instantly. "
                "- Your gold is securely stored in insured vaults. "
                "- Start small with as little as ₹10."
            ),
            nudge_text="Would you like me to help you invest in digital gold on Simplify Money now?"
        )

# --- Transactional API ---
@app.post("/buy-gold", response_model=schemas.PurchaseResponse, tags=["Transactional"])
async def buy_digital_gold(request: schemas.PurchaseRequest, db: Session = Depends(database.get_db)):
    if not request.nudge_to_invest:
        raise HTTPException(status_code=400, detail="Nudge flag is false. Purchase not allowed")

    price_inr_per_gram = request.quoted_price_inr_per_gram

    if request.amount_inr < 10:
        raise HTTPException(status_code=400, detail="Minimum purchase is ₹10")

    grams_purchased = round(request.amount_inr / price_inr_per_gram, 4)

    user = db.query(models.User).filter(models.User.email == request.user_email).first()
    if not user:
        user = models.User(name=request.user_name, email=request.user_email)
        db.add(user)
        db.commit()
        db.refresh(user)

    transaction = models.Transaction(
        user_id=user.id,
        amount_inr=request.amount_inr,
        grams_purchased=grams_purchased,
        gold_price_per_gram=round(price_inr_per_gram, 2)
    )
    db.add(transaction)
    db.commit()
    db.refresh(transaction)

    return schemas.PurchaseResponse(
        success=True,
        message=f"Purchase of {grams_purchased}g gold successful.",
        transaction_id=transaction.id,
        grams_purchased=grams_purchased
    )
