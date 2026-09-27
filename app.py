import os
from flask import Flask
from flask_login import current_user

from config import Config
from extensions import db, login_manager
from models import Admin
from seed_data import seed_questions


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    if not Config.ON_VERCEL:
        os.makedirs(os.path.join(Config.BASE_DIR, "instance"), exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_admin(user_id):
        return Admin.query.get(int(user_id))

    from routes_public import bp as public_bp
    from routes_admin import bp as admin_bp
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)

    with app.app_context():
        db.create_all()
        seed_questions()
        _seed_admin(app)

    return app


def _seed_admin(app):
    """
    Creates the admin account on first run if it doesn't exist yet.
    Email defaults to ADMIN_EMAIL (awanishkumarmishra2005@gmail.com).
    Password comes ONLY from the ADMIN_PASSWORD env var - never hardcoded,
    never committed. If it's missing, admin login is simply unavailable
    until you set it and restart.
    """
    email = app.config["ADMIN_EMAIL"]
    password = app.config["ADMIN_PASSWORD"]

    existing = Admin.query.filter_by(email=email).first()
    if existing:
        return

    if not password:
        app.logger.warning(
            "ADMIN_PASSWORD is not set - admin account was NOT created. "
            "Set ADMIN_PASSWORD in your .env and restart to create the admin login."
        )
        return

    admin = Admin(email=email)
    admin.set_password(password)
    db.session.add(admin)
    db.session.commit()
    app.logger.info(f"Admin account created for {email}")


if __name__ == "__main__":
    app = create_app()
    app.run(debug=not app.config["IS_PRODUCTION"], port=5000)
