import json
import logging
import os
import asyncio
from pathlib import Path
from typing import Optional

import httpx
from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)


class TgBot:
    """
    Utility for sending messages via Telegram Bot API.
    Configuration is stored in a JSON file (default: ~/.geo_recon.conf).
    Does not use long-polling – only direct HTTP calls for sending.
    """

    DEFAULT_CONFIG_PATH = Path.home() / ".geo_recon.conf"

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self._token: Optional[str] = None
        self._chat_id: Optional[int] = None
        self._enabled: bool = False
        self._bot: Optional[Bot] = None
        self._load_config()

    def _load_config(self) -> None:
        if not self.config_path.exists():
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return

        token = data.get("token")
        chat_id = data.get("chat_id")
        enabled = data.get("enabled", False)

        if token and chat_id and enabled:
            self._token = token
            self._chat_id = int(chat_id)
            self._enabled = True
            self._bot = Bot(token=self._token)
            return True
        return False

    def _save_config(self, data: dict) -> None:
        # Restrict file permissions to owner-only (600)."""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        os.chmod(self.config_path, 0o600)  # owner read/write only

    @property
    def enabled(self) -> bool:
        """Check if Telegram integration is active by re-reading config."""
        self._load_config()
        return self._enabled

    # for cli
    def setup_interactive(self) -> bool:
        if self._load_config():
            use_exist = input("There is already telegram config, do you want to use it? [y/n] -> ")
            if use_exist.lower() != "n":
                logger.info("Telegram configuration loaded.")
                return True

            self._token = None
            self._chat_id = None
            self._enabled = False
            self._bot = None

        logger.info("=== Telegram bot setup ===")
        token = input("Enter bot token: ").strip()
        if not token:
            logger.warning("❌ Token cannot be empty.")
            return False

        # validate config (by calling getMe)
        try:
            with httpx.Client() as client:
                response = client.get(
                    f"https://api.telegram.org/bot{token}/getMe",
                    timeout=10,
                )
            if response.status_code != 200 or not response.json().get("ok"):
                logger.error("Invalid token or chat id")
                return False
            bot_info = response.json().get("result")
            logger.info(f"Bot @{bot_info['username']} verified.")
        except (httpx.HTTPStatusError, json.JSONDecodeError) as e:
            logger.error(f"Failed to get bot info")

        chat_id_str = input("Enter target chat ID (numeric): ").strip()
        try:
            chat_id = int(chat_id_str)
        except ValueError:
            logger.error("Chat ID must be a number.")
            return False

        # Persist configuration
        data = {
            "token": token,
            "chat_id": chat_id,
            "enabled": True
        }
        self._save_config(data)
        self._load_config()  # refresh internal state
        logger.info("Telegram configuration saved and activated.")
        return True

    async def send_message(
            self,
            text: str,
            disable_web_page_preview: bool = True
    ):
        """
        Send a message to the configured Telegram chat asynchronously.
        Returns True on successful delivery, False otherwise.
        """
        if not self._enabled or not self._bot:
            return False

        try:
            await self._bot.send_message(
                chat_id=self._chat_id,
                text=text,
                disable_web_page_preview=disable_web_page_preview,
                parse_mode="HTML"
            )
            return True
        except TelegramError as e:
            logger.error(f"Failed to send message {e}")
            return False

    def configure_app_state(self, app) -> None:
        app.state.use_tg = self.enabled

tgBot = TgBot()