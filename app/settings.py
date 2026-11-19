"""Environment-backed settings with a mandatory Telegram allowlist."""
import os
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    telegram_token: str
    openai_api_key: str
    allowed_ids: frozenset[int]
    db_path: str
    devin_api_key: str
    devin_org_id: str


def load_settings() -> Settings:
    load_dotenv()
    telegram = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    openai = os.getenv("OPENAI_API_KEY", "").strip()
    allowed = os.getenv("ALLOWED_TELEGRAM_USER_IDS", "").strip()
    if not telegram or not openai or not allowed:
        raise ValueError(
            "Set TELEGRAM_BOT_TOKEN, OPENAI_API_KEY and ALLOWED_TELEGRAM_USER_IDS in .env"
        )
    try:
        ids = frozenset(int(part.strip()) for part in allowed.split(",") if part.strip())
    except ValueError as exc:
        raise ValueError("ALLOWED_TELEGRAM_USER_IDS must contain numeric IDs") from exc
    if not ids:
        raise ValueError("At least one allowed Telegram user ID is required")
    return Settings(
        telegram_token=telegram,
        openai_api_key=openai,
        allowed_ids=ids,
        db_path=os.getenv("SQLITE_PATH", "data/deven.sqlite3"),
        devin_api_key=os.getenv("DEVIN_API_KEY", "").strip(),
        devin_org_id=os.getenv("DEVIN_ORG_ID", "").strip(),
    )
