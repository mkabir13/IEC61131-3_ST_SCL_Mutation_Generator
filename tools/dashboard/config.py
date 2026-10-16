import os
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent.parent  # tools/ (this file is tools/dashboard/config.py)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-secret-change-me")
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + str(TOOLS_DIR / "dashboard" / "instance" / "mutate_dashboard.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    MAX_CONTENT_LENGTH = 2 * 1024 * 1024  # 2MB upload cap
