import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    BASE_DIR=BASE_DIR
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-change-me")

    _db_url = os.environ.get(
        "DATABASE_URL", f"sqlite:///{os.path.join(BASE_DIR, 'instance', 'beat_ai.db')}"
    )
    # Vercel's serverless filesystem is read-only/ephemeral outside /tmp, so SQLite
    # cannot be used there - only for local `python app.py` development. On Vercel,
    # DATABASE_URL must point at an external Postgres (Neon/Supabase free tier both work).
    # SQLAlchemy needs "postgresql://" not the bare "postgres://" some providers hand out.
    if _db_url.startswith("postgres://"):
        _db_url = _db_url.replace("postgres://", "postgresql://", 1)
    SQLALCHEMY_DATABASE_URI = _db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    ON_VERCEL = bool(os.environ.get("VERCEL"))
    if ON_VERCEL and SQLALCHEMY_DATABASE_URI.startswith("sqlite"):
        raise RuntimeError(
            "Running on Vercel requires DATABASE_URL to be set to an external "
            "Postgres connection string (e.g. from Neon or Supabase) - SQLite "
            "does not persist on Vercel's serverless filesystem."
        )

    FLASK_ENV = os.environ.get("FLASK_ENV", "development")
    IS_PRODUCTION = FLASK_ENV == "production"

    # PAYMENT_MODE: "test" or "live". Guarded so test mode can never run in production.
    PAYMENT_MODE = os.environ.get("PAYMENT_MODE", "test").lower()
    if IS_PRODUCTION and PAYMENT_MODE == "test":
        raise RuntimeError(
            "PAYMENT_MODE=test is not allowed when FLASK_ENV=production. "
            "Set PAYMENT_MODE=live and provide real Razorpay credentials."
        )

    ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "awanishkumarmishra2005@gmail.com")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD")  # required to seed admin, see app.py

    RAZORPAY_KEY_ID = os.environ.get("RAZORPAY_KEY_ID", "")
    RAZORPAY_KEY_SECRET = os.environ.get("RAZORPAY_KEY_SECRET", "")
    RAZORPAY_WEBHOOK_SECRET = os.environ.get("RAZORPAY_WEBHOOK_SECRET", "")

    if PAYMENT_MODE == "live" and not (RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET):
        raise RuntimeError(
            "PAYMENT_MODE=live requires RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET to be set."
        )

    # Prices are defined ONLY here (paise). Frontend can never override these.
    # Beginner has no entry - it is never chargeable, enforced in payment.py.
    PRICES_PAISE = {
        "intermediate": int(os.environ.get("INTERMEDIATE_PRICE_PAISE", 2000)),
        "advanced": int(os.environ.get("ADVANCED_PRICE_PAISE", 3000)),
    }

    QUESTIONS_PER_TIER = {"beginner": 5, "intermediate": 10, "advanced": 10}
    QUESTION_POOL_SIZE = {"beginner": 15, "intermediate": 30, "advanced": 30}

    CERT_DIR = os.path.join(BASE_DIR, "certs")
