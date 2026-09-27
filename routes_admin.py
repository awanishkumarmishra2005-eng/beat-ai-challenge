from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user

from extensions import db
from models import Admin, Payment, Participant, Attempt, Certificate, PaymentSettings, Feedback

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        admin = Admin.query.filter_by(email=email).first()
        if admin and admin.check_password(password):
            login_user(admin)
            return redirect(url_for("admin.dashboard"))
        flash("Invalid credentials.")

    return render_template("admin/login.html")


@bp.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("admin.login"))


@bp.route("/")
@login_required
def dashboard():
    total_revenue = _sum_revenue()
    today_revenue = _sum_revenue(since=_today_start())
    successful = Payment.query.filter_by(status="SUCCESS").count()
    intermediate_paid = Payment.query.filter_by(status="SUCCESS", challenge_type="intermediate").count()
    advanced_paid = Payment.query.filter_by(status="SUCCESS", challenge_type="advanced").count()
    pending = Payment.query.filter_by(status="PENDING").count()
    failed = Payment.query.filter(Payment.status.in_(["FAILED", "CANCELLED"])).count()
    recent_payments = Payment.query.order_by(Payment.created_at.desc()).limit(10).all()

    return render_template(
        "admin/dashboard.html",
        total_revenue=total_revenue,
        today_revenue=today_revenue,
        successful=successful,
        intermediate_paid=intermediate_paid,
        advanced_paid=advanced_paid,
        pending=pending,
        failed=failed,
        recent_payments=recent_payments,
    )


@bp.route("/payments")
@login_required
def payments():
    status = request.args.get("status", "")
    challenge_type = request.args.get("challenge_type", "")
    q = Payment.query
    if status:
        q = q.filter_by(status=status)
    if challenge_type:
        q = q.filter_by(challenge_type=challenge_type)
    search = request.args.get("q", "").strip()
    if search:
        q = q.join(Participant).filter(
            db.or_(
                Participant.name.ilike(f"%{search}%"),
                Participant.email.ilike(f"%{search}%"),
                Payment.order_id.ilike(f"%{search}%"),
                Payment.payment_id.ilike(f"%{search}%"),
            )
        )
    payments_list = q.order_by(Payment.created_at.desc()).limit(500).all()

    summary = {
        "total_revenue": _sum_revenue(),
        "today_revenue": _sum_revenue(since=_today_start()),
        "successful": Payment.query.filter_by(status="SUCCESS").count(),
        "intermediate": Payment.query.filter_by(status="SUCCESS", challenge_type="intermediate").count(),
        "advanced": Payment.query.filter_by(status="SUCCESS", challenge_type="advanced").count(),
        "pending": Payment.query.filter_by(status="PENDING").count(),
        "failed": Payment.query.filter(Payment.status.in_(["FAILED", "CANCELLED"])).count(),
    }

    return render_template("admin/payments.html", payments=payments_list, summary=summary,
                            status=status, challenge_type=challenge_type, search=search)


@bp.route("/participants")
@login_required
def participants():
    rows = (
        db.session.query(Participant, Payment, Attempt, Certificate)
        .join(Payment, Payment.participant_id == Participant.id)
        .outerjoin(Attempt, Attempt.payment_id == Payment.id)
        .outerjoin(Certificate, Certificate.attempt_id == Attempt.id)
        .order_by(Payment.created_at.desc())
        .limit(500)
        .all()
    )
    return render_template("admin/participants.html", rows=rows)


@bp.route("/revenue")
@login_required
def revenue():
    now = datetime.utcnow()
    week_start = now - timedelta(days=7)
    month_start = now - timedelta(days=30)

    data = {
        "total": _sum_revenue(),
        "today": _sum_revenue(since=_today_start()),
        "week": _sum_revenue(since=week_start),
        "month": _sum_revenue(since=month_start),
        "intermediate": _sum_revenue(challenge_type="intermediate"),
        "advanced": _sum_revenue(challenge_type="advanced"),
        "successful": Payment.query.filter_by(status="SUCCESS").count(),
        "failed": Payment.query.filter(Payment.status.in_(["FAILED", "CANCELLED"])).count(),
        "pending": Payment.query.filter_by(status="PENDING").count(),
    }
    return render_template("admin/revenue.html", data=data)


@bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    s = PaymentSettings.get()
    if request.method == "POST":
        s.upi_id = request.form.get("upi_id", "").strip()
        s.display_name = request.form.get("display_name", "").strip()
        db.session.commit()
        flash("Settings saved.")
    return render_template("admin/settings.html", settings=s)


@bp.route("/feedback")
@login_required
def feedback():
    rows = Feedback.query.order_by(Feedback.created_at.desc()).limit(200).all()
    by_level = {}
    by_reaction = {}
    for f in rows:
        by_level[f.challenge_type] = by_level.get(f.challenge_type, 0) + 1
        by_reaction[f.reaction] = by_reaction.get(f.reaction, 0) + 1
    return render_template("admin/feedback.html", rows=rows, by_level=by_level, by_reaction=by_reaction)


def _today_start():
    n = datetime.utcnow()
    return datetime(n.year, n.month, n.day)


def _sum_revenue(since=None, challenge_type=None):
    q = Payment.query.filter_by(status="SUCCESS")
    if since:
        q = q.filter(Payment.verified_at >= since)
    if challenge_type:
        q = q.filter_by(challenge_type=challenge_type)
    total_paise = sum(p.amount_paise for p in q.all())
    return round(total_paise / 100, 2)
