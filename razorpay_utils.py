import hashlib
import hmac
import os
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID", "")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET", "")


def verify_payment_signature(order_id: str, payment_id: str, razorpay_signature: str, key_secret: Optional[str] = None) -> bool:
    secret = key_secret or RAZORPAY_KEY_SECRET
    if not order_id or not payment_id or not razorpay_signature or not secret:
        return False

    generated_signature = hmac.new(
        secret.encode("utf-8"),
        f"{order_id}|{payment_id}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(generated_signature, razorpay_signature)


