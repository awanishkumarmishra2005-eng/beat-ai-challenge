import json
import secrets
import string
from datetime import datetime

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from extensions import db


def gen_id(prefix, n=10):
    alphabet = string.ascii_uppercase + string.digits
    return f"{prefix}-{''.join(secrets.choice(alphabet) for _ in range(n))}"


class Admin(UserMixin, db.Model):
    __tablename__ = "admins"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)


class Participant(db.Model):
    __tablename__ = "participants"
    id = db.Column(db.Integer, primary_key=True)
    registration_id = db.Column(db.String(32), unique=True, default=lambda: gen_id("REG"))
    name = db.Column(db.String(150), nullable=False, default="Guest")
    email = db.Column(db.String(255), nullable=True, index=True)
    phone = db.Column(db.String(20), nullable=True)
    institution = db.Column(db.String(255))
    leaderboard_optin = db.Column(db.Boolean, default=False)
    is_guest = db.Column(db.Boolean, default=False)  # True for Beginner (no registration required)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    payments = db.relationship("Payment", backref="participant", lazy=True)
    attempts = db.relationship("Attempt", backref="participant", lazy=True)


class Question(db.Model):
    __tablename__ = "questions"
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(20), nullable=False, index=True)  # intermediate | advanced
    text = db.Column(db.Text, nullable=False)
    options_json = db.Column(db.Text, nullable=False)  # JSON list of 4 strings
    correct_index = db.Column(db.Integer, nullable=False)  # 0-3
    ai_correct = db.Column(db.Boolean, default=True)  # whether the AI benchmark gets this right

    @property
    def options(self):
        return json.loads(self.options_json)


class Payment(db.Model):
    __tablename__ = "payments"
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    payment_id = db.Column(db.String(64), unique=True, nullable=True, index=True)  # set on success
    participant_id = db.Column(db.Integer, db.ForeignKey("participants.id"), nullable=False)
    challenge_type = db.Column(db.String(20), nullable=False)  # intermediate | advanced
    amount_paise = db.Column(db.Integer, nullable=False)
    method = db.Column(db.String(30), default="razorpay")  # razorpay | test
    status = db.Column(db.String(20), default="PENDING", index=True)
    # PENDING | SUCCESS | FAILED | CANCELLED | REFUNDED
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    verified_at = db.Column(db.DateTime, nullable=True)

    attempt = db.relationship("Attempt", backref="payment", uselist=False)

    @property
    def amount_rupees(self):
        return self.amount_paise / 100


class Attempt(db.Model):
    """
    Created the instant a payment is verified SUCCESS (one payment -> one attempt).
    status: unlocked -> in_progress -> completed
    """
    __tablename__ = "attempts"
    id = db.Column(db.Integer, primary_key=True)
    attempt_code = db.Column(db.String(32), unique=True, default=lambda: gen_id("ATT"))
    payment_id = db.Column(db.Integer, db.ForeignKey("payments.id"), unique=True, nullable=False)
    participant_id = db.Column(db.Integer, db.ForeignKey("participants.id"), nullable=False)
    challenge_type = db.Column(db.String(20), nullable=False)

    question_ids_json = db.Column(db.Text, nullable=True)  # set when attempt starts
    current_index = db.Column(db.Integer, default=0)
    answers_json = db.Column(db.Text, default="[]")  # list of chosen option indices

    status = db.Column(db.String(20), default="unlocked", index=True)
    # unlocked | in_progress | completed

    human_score_pct = db.Column(db.Float, nullable=True)
    ai_score_pct = db.Column(db.Float, nullable=True)
    result_category = db.Column(db.String(20), nullable=True)  # champion | survivor | draw

    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)

    @property
    def duration_seconds(self):
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    certificate = db.relationship("Certificate", backref="attempt", uselist=False)

    @property
    def question_ids(self):
        return json.loads(self.question_ids_json) if self.question_ids_json else []

    @question_ids.setter
    def question_ids(self, value):
        self.question_ids_json = json.dumps(value)

    @property
    def answers(self):
        return json.loads(self.answers_json)

    @answers.setter
    def answers(self, value):
        self.answers_json = json.dumps(value)


class Certificate(db.Model):
    __tablename__ = "certificates"
    id = db.Column(db.Integer, primary_key=True)
    certificate_code = db.Column(db.String(32), unique=True, default=lambda: gen_id("CERT"))
    attempt_id = db.Column(db.Integer, db.ForeignKey("attempts.id"), unique=True, nullable=False)
    participant_name = db.Column(db.String(150), nullable=False)
    institution = db.Column(db.String(255), nullable=True)
    challenge_type = db.Column(db.String(20), nullable=False)
    certificate_type = db.Column(db.String(10), nullable=False, default="normal")  # normal | premium
    human_score_pct = db.Column(db.Float, nullable=False)
    ai_score_pct = db.Column(db.Float, nullable=False)
    result_category = db.Column(db.String(20), nullable=False)
    issued_at = db.Column(db.DateTime, default=datetime.utcnow)
    file_path = db.Column(db.String(500), nullable=True)


class PaymentSettings(db.Model):
    __tablename__ = "payment_settings"
    id = db.Column(db.Integer, primary_key=True)
    upi_id = db.Column(db.String(120), default="")
    display_name = db.Column(db.String(150), default="")
    qr_image_path = db.Column(db.String(500), default="")

    @staticmethod
    def get():
        s = PaymentSettings.query.first()
        if not s:
            s = PaymentSettings()
            db.session.add(s)
            db.session.commit()
        return s


class Feedback(db.Model):
    __tablename__ = "feedback"
    id = db.Column(db.Integer, primary_key=True)
    attempt_id = db.Column(db.Integer, db.ForeignKey("attempts.id"), nullable=True)
    challenge_type = db.Column(db.String(20), nullable=False)
    result_category = db.Column(db.String(20), nullable=True)
    reaction = db.Column(db.String(30), nullable=False)  # e.g. "amazing" | "fun" | "want_more" | "good" | "tough"
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
