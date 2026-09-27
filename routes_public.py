from datetime import datetime, timedelta

from flask import Blueprint, render_template, request, redirect, url_for, jsonify, flash, session, abort, current_app, send_file

from extensions import db
from models import Participant, Payment, Attempt, Question, Certificate, PaymentSettings, Feedback
import payment as pay
import certificate as cert_mod

bp = Blueprint("public", __name__)


# ---------- Landing / category choice ----------

@bp.route("/")
def landing():
    return render_template("landing.html")


@bp.route("/play/beginner")
def play_beginner():
    """The ONLY entry point for Beginner. Free, no registration, no payment -
    goes straight through the same locked-challenge machinery as the paid
    tiers (via a $0 SUCCESS payment), so there is exactly one code path for
    'is this attempt allowed to see questions', not a special case for free."""
    attempt = pay.start_free_beginner_attempt()
    return redirect(url_for("public.challenge_gate", attempt_code=attempt.attempt_code))


# ---------- Registration (Intermediate / Advanced only - Beginner needs none) ----------

@bp.route("/register/<challenge_type>", methods=["GET", "POST"])
def register(challenge_type):
    if challenge_type not in ("intermediate", "advanced"):
        abort(404)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        institution = request.form.get("institution", "").strip()
        leaderboard_optin = request.form.get("leaderboard_optin") == "on"

        if not name or not email or not phone:
            flash("Name, email and phone are required.")
            return render_template("register.html", challenge_type=challenge_type)

        participant = Participant(
            name=name, email=email, phone=phone, institution=institution,
            leaderboard_optin=leaderboard_optin,
        )
        db.session.add(participant)
        db.session.commit()

        order = pay.create_order(participant, challenge_type)
        return redirect(url_for("public.pay_page", order_id=order.order_id))

    return render_template("register.html", challenge_type=challenge_type)


# ---------- Payment ----------

@bp.route("/pay/<order_id>")
def pay_page(order_id):
    payment = Payment.query.filter_by(order_id=order_id).first_or_404()
    settings = PaymentSettings.get()
    return render_template(
        "payment.html",
        payment=payment,
        payment_mode=current_app.config["PAYMENT_MODE"],
        razorpay_key_id=current_app.config["RAZORPAY_KEY_ID"],
        settings=settings,
    )


@bp.route("/api/pay/test-confirm", methods=["POST"])
def test_confirm():
    """Only reachable if PAYMENT_MODE=test. Simulates a gateway success but goes
    through the exact same backend entitlement function as a real payment."""
    if current_app.config["PAYMENT_MODE"] != "test":
        abort(403)

    order_id = request.json.get("order_id")
    payment = Payment.query.filter_by(order_id=order_id).first_or_404()
    if payment.status == "SUCCESS":
        attempt = payment.attempt
    else:
        fake_gateway_id = "test_pay_" + payment.order_id[-10:]
        attempt = pay.mark_success_and_unlock(payment, fake_gateway_id)

    return jsonify({"ok": True, "redirect": url_for("public.challenge_gate", attempt_code=attempt.attempt_code)})


@bp.route("/api/pay/razorpay-verify", methods=["POST"])
def razorpay_verify():
    """Verifies a real Razorpay checkout response server-side before unlocking anything."""
    if current_app.config["PAYMENT_MODE"] != "live":
        abort(403)

    data = request.json
    order_id = data.get("razorpay_order_id")
    rp_payment_id = data.get("razorpay_payment_id")
    rp_signature = data.get("razorpay_signature")

    payment = Payment.query.filter_by(order_id=order_id).first_or_404()

    if not pay.verify_signature(order_id, rp_payment_id, rp_signature):
        pay.mark_failed(payment, "FAILED")
        return jsonify({"ok": False, "error": "Signature verification failed"}), 400

    attempt = pay.mark_success_and_unlock(payment, rp_payment_id)
    return jsonify({"ok": True, "redirect": url_for("public.challenge_gate", attempt_code=attempt.attempt_code)})


@bp.route("/api/pay/cancel", methods=["POST"])
def pay_cancel():
    order_id = request.json.get("order_id")
    payment = Payment.query.filter_by(order_id=order_id).first_or_404()
    pay.mark_failed(payment, "CANCELLED")
    return jsonify({"ok": True})


@bp.route("/webhooks/razorpay", methods=["POST"])
def razorpay_webhook():
    signature = request.headers.get("X-Razorpay-Signature", "")
    if not pay.verify_webhook_signature(request.get_data(), signature):
        abort(400)

    event = request.json
    event_type = event.get("event")
    payload = event.get("payload", {}).get("payment", {}).get("entity", {})
    order_id = payload.get("order_id")
    rp_payment_id = payload.get("id")

    payment = Payment.query.filter_by(order_id=order_id).first()
    if not payment:
        return jsonify({"ok": True})  # unknown order, ignore

    if event_type == "payment.captured":
        pay.mark_success_and_unlock(payment, rp_payment_id)
    elif event_type in ("payment.failed",):
        pay.mark_failed(payment, "FAILED")

    return jsonify({"ok": True})


# ---------- Challenge gate (the enforced lock) ----------

@bp.route("/challenge/<attempt_code>")
def challenge_gate(attempt_code):
    """
    This is the ONLY entry point participants use to reach the challenge.
    It re-checks entitlement server-side every time - never trusts client state.
    """
    attempt = Attempt.query.filter_by(attempt_code=attempt_code).first_or_404()
    payment = attempt.payment

    if payment.status != "SUCCESS":
        return render_template("locked.html", challenge_type=attempt.challenge_type)

    if attempt.status == "completed":
        return redirect(url_for("public.result", attempt_code=attempt.attempt_code))

    if attempt.status == "unlocked":
        attempt.question_ids = pay.draw_questions(attempt.challenge_type)
        attempt.status = "in_progress"
        attempt.started_at = datetime.utcnow()
        attempt.answers = []
        db.session.commit()

    return render_template("challenge.html", attempt=attempt)


@bp.route("/api/challenge/<attempt_code>/question")
def get_question(attempt_code):
    """Serves ONE question at a time. Verified paid + in_progress attempts only."""
    attempt = Attempt.query.filter_by(attempt_code=attempt_code).first_or_404()
    if attempt.payment.status != "SUCCESS" or attempt.status not in ("in_progress",):
        abort(403)

    idx = attempt.current_index
    qids = attempt.question_ids
    if idx >= len(qids):
        return jsonify({"done": True})

    q = Question.query.get(qids[idx])
    options = list(enumerate(q.options))
    import random
    random.shuffle(options)  # randomized option order; map back via original index
    return jsonify({
        "done": False,
        "index": idx,
        "total": len(qids),
        "text": q.text,
        "options": [{"key": orig_idx, "text": text} for orig_idx, text in options],
    })


@bp.route("/api/challenge/<attempt_code>/answer", methods=["POST"])
def submit_answer(attempt_code):
    attempt = Attempt.query.filter_by(attempt_code=attempt_code).first_or_404()
    if attempt.payment.status != "SUCCESS" or attempt.status != "in_progress":
        abort(403)

    chosen = request.json.get("chosen_index")
    answers = attempt.answers
    answers.append(chosen)
    attempt.answers = answers
    attempt.current_index += 1

    finished = attempt.current_index >= len(attempt.question_ids)
    if finished:
        _finalize_attempt(attempt)

    db.session.commit()
    return jsonify({"ok": True, "finished": finished})


def _finalize_attempt(attempt: Attempt):
    qids = attempt.question_ids
    answers = attempt.answers
    correct = 0
    ai_correct = 0
    for qid, ans in zip(qids, answers):
        q = Question.query.get(qid)
        if ans == q.correct_index:
            correct += 1
        if q.ai_correct:
            ai_correct += 1

    total = len(qids)
    human_pct = round(100 * correct / total, 1)
    ai_pct = round(100 * ai_correct / total, 1)

    if human_pct > ai_pct:
        category = "champion"
    elif ai_pct > human_pct:
        category = "survivor"
    else:
        category = "draw"

    attempt.human_score_pct = human_pct
    attempt.ai_score_pct = ai_pct
    attempt.result_category = category
    attempt.status = "completed"
    attempt.completed_at = datetime.utcnow()
    db.session.flush()

    # Certificates are a paid-tier feature - Beginner shows the result and
    # teases the certificate as the reason to unlock Intermediate/Advanced.
    if attempt.challenge_type != "beginner":
        cert_mod.generate_certificate(attempt)


# ---------- Result, thank-you & feedback ----------

@bp.route("/result/<attempt_code>")
def result(attempt_code):
    attempt = Attempt.query.filter_by(attempt_code=attempt_code).first_or_404()
    if attempt.payment.status != "SUCCESS" or attempt.status != "completed":
        abort(403)

    if attempt.challenge_type == "beginner":
        already_gave_feedback = Feedback.query.filter_by(attempt_id=attempt.id).first() is not None
        return render_template("result_beginner.html", attempt=attempt, already_gave_feedback=already_gave_feedback)

    return render_template("result.html", attempt=attempt, cert=attempt.certificate)


@bp.route("/api/feedback", methods=["POST"])
def submit_feedback():
    data = request.json
    attempt_code = data.get("attempt_code")
    reaction = data.get("reaction")
    comment = (data.get("comment") or "").strip()[:500]

    attempt = Attempt.query.filter_by(attempt_code=attempt_code).first_or_404()
    if attempt.status != "completed":
        abort(403)

    if Feedback.query.filter_by(attempt_id=attempt.id).first():
        return jsonify({"ok": True})  # already recorded, don't duplicate

    fb = Feedback(
        attempt_id=attempt.id,
        challenge_type=attempt.challenge_type,
        result_category=attempt.result_category,
        reaction=reaction,
        comment=comment or None,
    )
    db.session.add(fb)
    db.session.commit()
    return jsonify({"ok": True})


@bp.route("/certificate/<code>")
def view_certificate(code):
    """Interactive on-page certificate (animated reveal, share, download) -
    the PDF from /download is the portable copy; this is the 'feels premium' one."""
    cert = Certificate.query.filter_by(certificate_code=code).first_or_404()
    return render_template("certificate_view.html", cert=cert)


@bp.route("/certificate/<code>/download")
def download_certificate(code):
    cert = Certificate.query.filter_by(certificate_code=code).first_or_404()
    pdf_buf = cert_mod.render_certificate_pdf(cert)  # rendered fresh, no disk involved
    return send_file(pdf_buf, as_attachment=True, download_name=f"{cert.certificate_code}.pdf",
                      mimetype="application/pdf")


@bp.route("/verify/<code>")
def verify_certificate(code):
    """Public verification page - name, result, challenge type, date ONLY. No PII."""
    cert = Certificate.query.filter_by(certificate_code=code).first()
    if not cert:
        return render_template("verify.html", found=False)
    return render_template("verify.html", found=True, cert=cert)


# ---------- Leaderboard ----------

@bp.route("/leaderboard")
def leaderboard():
    tier = request.args.get("tier", "intermediate")
    if tier not in ("intermediate", "advanced"):
        tier = "intermediate"

    rows = (
        db.session.query(Attempt, Participant)
        .join(Participant, Attempt.participant_id == Participant.id)
        .filter(
            Attempt.status == "completed",
            Attempt.challenge_type == tier,
            Participant.leaderboard_optin == True,  # noqa: E712
        )
        .all()
    )
    # Sort by Human % desc, then fastest completion time as tiebreaker.
    rows.sort(key=lambda r: (-r[0].human_score_pct, r[0].duration_seconds or float("inf")))

    return render_template("leaderboard.html", tier=tier, rows=rows[:100])
