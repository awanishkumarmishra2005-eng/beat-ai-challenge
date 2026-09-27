"""
All payment logic lives here. This module is the single source of truth for:
  - what an order costs (never trust the frontend)
  - whether a payment is SUCCESS
  - creating the one Attempt a SUCCESS payment entitles

Nothing outside this module may set Payment.status = "SUCCESS".
"""
import hmac
import hashlib
import secrets
import string
from datetime import datetime

from flask import current_app

from extensions import db
from models import Payment, Attempt, Question, Participant
import random


class PaymentError(Exception):
    pass


def _gen_order_id():
    alphabet = string.ascii_uppercase + string.digits
    return "order_" + "".join(secrets.choice(alphabet) for _ in range(16))


def start_free_beginner_attempt():
    """
    Beginner is genuinely free - no payment, no registration required.
    We still route it through a Payment+Attempt row (amount 0, method "free",
    status SUCCESS) so every other piece of the app - the lock check, the
    admin dashboard, the one-attempt-per-entitlement model - stays a single
    code path instead of a special case. This function is the ONLY place
    "beginner" attempts are created; it can never be reused to grant a
    paid tier.
    """
    guest = Participant(name="Guest", is_guest=True)
    db.session.add(guest)
    db.session.flush()

    free_payment = Payment(
        order_id=_gen_order_id(),
        participant_id=guest.id,
        challenge_type="beginner",
        amount_paise=0,
        method="free",
        status="SUCCESS",
        verified_at=datetime.utcnow(),
    )
    db.session.add(free_payment)
    db.session.flush()

    attempt = Attempt(
        payment_id=free_payment.id,
        participant_id=guest.id,
        challenge_type="beginner",
        status="unlocked",
    )
    db.session.add(attempt)
    db.session.commit()
    return attempt


def get_price_paise(challenge_type):
    if challenge_type == "beginner":
        raise PaymentError("Beginner is free and can never be charged")
    prices = current_app.config["PRICES_PAISE"]
    if challenge_type not in prices:
        raise PaymentError("Invalid challenge type")
    return prices[challenge_type]


def create_order(participant, challenge_type):
    """
    Creates a PENDING payment row. In live mode also creates a real Razorpay order.
    Amount is always taken from server config, never from the client.
    """
    amount = get_price_paise(challenge_type)
    mode = current_app.config["PAYMENT_MODE"]

    if mode == "live":
        import razorpay
        client = razorpay.Client(
            auth=(current_app.config["RAZORPAY_KEY_ID"], current_app.config["RAZORPAY_KEY_SECRET"])
        )
        rp_order = client.order.create(
            {"amount": amount, "currency": "INR", "payment_capture": 1}
        )
        order_id = rp_order["id"]
        method = "razorpay"
    else:
        order_id = _gen_order_id()
        method = "test"

    payment = Payment(
        order_id=order_id,
        participant_id=participant.id,
        challenge_type=challenge_type,
        amount_paise=amount,
        method=method,
        status="PENDING",
    )
    db.session.add(payment)
    db.session.commit()
    return payment


def verify_signature(order_id, razorpay_payment_id, razorpay_signature):
    """Verify Razorpay's HMAC-SHA256 signature server-side. Never skip this in live mode."""
    secret = current_app.config["RAZORPAY_KEY_SECRET"]
    payload = f"{order_id}|{razorpay_payment_id}".encode()
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, razorpay_signature)


def verify_webhook_signature(raw_body: bytes, signature: str):
    secret = current_app.config["RAZORPAY_WEBHOOK_SECRET"]
    expected = hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def mark_success_and_unlock(payment: Payment, gateway_payment_id: str):
    """
    The ONLY function allowed to flip a payment to SUCCESS and create its Attempt.
    Idempotent: calling twice for the same payment never creates a second attempt.
    """
    if payment.status == "SUCCESS" and payment.attempt:
        return payment.attempt  # already processed - one payment, one attempt, guaranteed

    if payment.status in ("FAILED", "CANCELLED", "REFUNDED"):
        raise PaymentError(f"Cannot mark a {payment.status} payment as SUCCESS")

    payment.status = "SUCCESS"
    payment.payment_id = gateway_payment_id
    payment.verified_at = datetime.utcnow()
    db.session.add(payment)
    db.session.flush()

    # Defensive: attempt may already exist from a race; never create a second one.
    existing = Attempt.query.filter_by(payment_id=payment.id).first()
    if existing:
        db.session.commit()
        return existing

    attempt = Attempt(
        payment_id=payment.id,
        participant_id=payment.participant_id,
        challenge_type=payment.challenge_type,
        status="unlocked",
    )
    db.session.add(attempt)
    db.session.commit()
    return attempt


def mark_failed(payment: Payment, reason="FAILED"):
    if payment.status == "SUCCESS":
        return  # never downgrade a verified success
    payment.status = reason
    db.session.add(payment)
    db.session.commit()


def draw_questions(challenge_type):
    """Randomly select this tier's question count from its own separate pool.
    Beginner/Intermediate/Advanced pools never overlap (category is the pool)."""
    n = current_app.config["QUESTIONS_PER_TIER"][challenge_type]
    pool = Question.query.filter_by(category=challenge_type).all()
    if len(pool) < n:
        raise PaymentError(f"Not enough {challenge_type} questions seeded ({len(pool)}/{n})")
    chosen = random.sample(pool, n)
    random.shuffle(chosen)
    return [q.id for q in chosen]
