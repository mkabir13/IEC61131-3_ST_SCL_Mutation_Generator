import os
from pathlib import Path
from flask import Flask

from dashboard.config import Config
from dashboard.extensions import db


def create_app() -> Flask:
    app = Flask(__name__)
    app.config.from_object(Config)

    # Ensure the directory the SQLite URI points to actually exists —
    # Flask's auto instance_path guess doesn't reliably match a path we
    # set explicitly in Config, so create it directly from the URI.
    db_uri = app.config["SQLALCHEMY_DATABASE_URI"]
    if db_uri.startswith("sqlite:///"):
        db_path = Path(db_uri.replace("sqlite:///", "", 1))
        db_path.parent.mkdir(parents=True, exist_ok=True)

    db.init_app(app)

    from dashboard.routes import bp as dashboard_bp
    app.register_blueprint(dashboard_bp)

    with app.app_context():
        db.create_all()

    return app
