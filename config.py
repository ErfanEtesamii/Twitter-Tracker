import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    def __init__(self):
        self.bot_token = os.getenv("BOT_TOKEN", "")
        self.admin_ids = self._parse_ids(os.getenv("ADMIN_IDS", ""))
        self.google_creds_path = os.getenv("GOOGLE_CREDS_PATH", "data/service_account.json")
        self.projects_path = os.getenv("PROJECTS_PATH", "data/projects.json")
        self.cache_path = os.getenv("CACHE_PATH", "data/cache.json")
        self.log_level = os.getenv("LOG_LEVEL", "INFO")

    def _parse_ids(self, raw):
        return [x.strip() for x in raw.split(",") if x.strip()]