from pydantic import BaseModel, EmailStr
from typing import Optional

class QuestionRequest(BaseModel):
    question: str

class KuberResponse(BaseModel):
    is_gold_query: bool
    answer: str
    extra_insights: Optional[str] = None
    simplify_suggestion: Optional[str] = None 
    nudge_text: Optional[str] = None

class PurchaseRequest(BaseModel):
    user_name: str
    user_email: EmailStr
    amount_inr: float
    quoted_price_inr_per_gram: float 
    nudge_to_invest: bool  

class PurchaseResponse(BaseModel):
    success: bool
    message: str
    transaction_id: int
    grams_purchased: float