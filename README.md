# BEAT AI CHALLENGE

A paid Human vs AI trivia challenge platform. Strict pay → verify → play flow,
enforced server-side end to end.

## Stack
Flask + SQLAlchemy (SQLite by default) + Flask-Login for a separate admin session +
Razorpay for payments (with a guarded test mode) + ReportLab/qrcode for instant certificates.

## Setup

```bash
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env:
#   ADMIN_PASSWORD=<pick a strong password>   (admin email defaults to
#   awanishkumarmishra2005@gmail.com — change ADMIN_EMAIL if you want a different one)
#   PAYMENT_MODE=test   (leave as test until you have real Razorpay keys)

python app.py
```

Visit `http://localhost:5000`. Admin login is at `/admin/login`.

The admin account is created automatically on first run using `ADMIN_EMAIL` +
`ADMIN_PASSWORD` from `.env`. If `ADMIN_PASSWORD` is missing, no admin account is
created and the app logs a warning — set it and restart.

## Deploying to Vercel (free)

Vercel runs this as a serverless function, which means two things had to change
from local dev: the database must be an external Postgres (SQLite can't persist
on Vercel's filesystem), and certificate PDFs are generated on-demand in memory
at download time instead of being saved to disk. Both are already wired up in
this repo (`api/index.py`, `vercel.json`, `config.py`).

**1. Get a free Postgres database** (pick one):
   - [Neon](https://neon.tech) — free tier, fastest to set up. Create a project,
     copy the connection string.
   - [Supabase](https://supabase.com) — also free, includes extras like file
     storage if you want to add UPI QR uploads later.

**2. Push this folder to a GitHub repo.**
   ```bash
   git init
   git add .
   git commit -m "BEAT AI CHALLENGE"
   git remote add origin <your-repo-url>
   git push -u origin main
   ```

**3. Import the repo on [vercel.com](https://vercel.com)** — "Add New Project" →
   select your repo. Vercel will detect `vercel.json` automatically.

**4. Set environment variables** in the Vercel project's Settings → Environment
   Variables (never in code):
   - `SECRET_KEY` — any long random string
   - `DATABASE_URL` — the Postgres connection string from step 1
   - `ADMIN_EMAIL` — `awanishkumarmishra2005@gmail.com` (or your choice)
   - `ADMIN_PASSWORD` — a strong password you pick
   - `PAYMENT_MODE` — `test` until you have Razorpay keys, then `live`
   - `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, `RAZORPAY_WEBHOOK_SECRET` — add
     once you have them (leave blank in test mode)
   - `STARTER_PRICE_PAISE=2500`, `ADVANCED_PRICE_PAISE=3500` — matches the
     ₹25 / ₹35 pricing

**5. Deploy.** Vercel builds and gives you a live URL. The first request will
   create the database tables and seed your admin account automatically.

**6. When you add real Razorpay keys later:** update the env vars, flip
   `PAYMENT_MODE` to `live`, redeploy, and add the webhook URL
   (`https://<your-app>.vercel.app/webhooks/razorpay`) in the Razorpay
   dashboard. No code changes needed.

**Known Vercel limitation to plan around:** free-tier serverless functions
have a ~10 second execution timeout. That's fine for this app as built, but
worth remembering once you add the live AI-opponent feature — each AI call
needs to stay fast, or batch/stream it rather than blocking the request.

## Going live with Razorpay

1. Get your `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`, and set up a webhook in the
   Razorpay dashboard pointing at `/webhooks/razorpay`; copy its secret into
   `RAZORPAY_WEBHOOK_SECRET`.
2. Set `PAYMENT_MODE=live` in `.env`.
3. Set `FLASK_ENV=production` when you deploy — the app will refuse to start if
   `PAYMENT_MODE=test` and `FLASK_ENV=production` are set together, by design.

No code changes are needed to switch modes — `payment.py` branches on
`PAYMENT_MODE` and both paths funnel through the same
`mark_success_and_unlock()` function, which is the only place a payment is
ever allowed to flip to `SUCCESS` and unlock an attempt.

## How the "one payment = one attempt" guarantee works

- A `Payment` row is created as `PENDING` the moment an order is created.
- Only `payment.mark_success_and_unlock()` can set it to `SUCCESS`, and it
  immediately creates the linked `Attempt` in the same transaction.
- `Attempt.payment_id` is a **unique** foreign key — the database itself
  rejects a second attempt against the same payment.
- The function is idempotent, so a duplicate webhook delivery or a double
  click can never create a second attempt.

## How the lock is enforced

- `/challenge/<attempt_code>` (the only participant-facing entry point) checks
  `payment.status == "SUCCESS"` server-side on every request before rendering
  anything, and shows the 🔒 locked screen otherwise.
- `/api/challenge/<code>/question` and `/answer` re-check the same condition
  before returning any question content — there is no endpoint that returns
  question text without a verified payment.

## What's stubbed / left for you to wire up

- **UPI QR upload** — the settings page stores a UPI ID and display name;
  actual image upload storage isn't wired (add a file upload field + storage
  of your choice, e.g. S3 or local `/static/uploads/`).
- **Email/SMS receipts** — not included; hook them into
  `payment.mark_success_and_unlock()` if you want them.
- **Rate limiting** — add `Flask-Limiter` on `/api/pay/*` and `/admin/login`
  before going to production.
- **Production DB** — swap `DATABASE_URL` for Postgres/MySQL when you scale
  past SQLite's comfort zone.

## Project layout

```
app.py              # app factory, admin auto-seed
config.py           # all config from env vars, guards test-mode-in-prod
extensions.py       # db, login_manager
models.py           # Admin, Participant, Payment, Attempt, Certificate, PaymentSettings
payment.py          # order creation, signature verification, entitlement logic
certificate.py      # instant PDF certificate + QR generation
routes_public.py     # landing, register, pay, challenge, result, certificate verify
routes_admin.py      # admin auth + dashboard/payments/participants/revenue/settings
seed_data.py         # 30 starter + 30 advanced questions
templates/, static/  # Jinja templates + CSS
```
