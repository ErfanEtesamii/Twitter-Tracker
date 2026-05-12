import logging
import asyncio
from config import Config
from storage import Storage
from sheets import SheetsClient
from project_manager import ProjectManager
from notifier import Notifier
from twitter_client import TwitterClient
from telegram_bot import TelegramBot
from utils import retry

class MonitorApp:
    def __init__(self):
        self.cfg = Config()
        logging.basicConfig(level=getattr(logging, self.cfg.log_level, logging.INFO))
        self.storage = Storage(self.cfg.projects_path, self.cfg.cache_path)
        self.pm = ProjectManager(self.storage)
        self.sheets = SheetsClient(self.cfg.google_creds_path)
        self.notifier = Notifier(self.cfg.bot_token)
        self.cache = self.storage.load_cache()
        self.twitter = TwitterClient()
        self.bot = TelegramBot(self.cfg.bot_token, self.cfg.admin_ids, self.pm, self.storage, self.sheets, self.notifier, self)

    def load_seen(self):
        return set(self.cache.get("sent", []))

    def save_seen(self, seen):
        self.cache["sent"] = list(seen)
        self.storage.save_cache(self.cache)

    def _get_usernames(self, project):
        sh = self.sheets.open_by_key(project.source_sheet_id)
        ws = sh.worksheet(project.source_ws_title)
        vals = ws.col_values(1)
        return [v.strip().lstrip("@") for v in vals if v.strip() and v.strip().lower() != "username"]

    @retry(max_attempts=3, delay=2.0)
    def run_scan_once(self):
        seen = self.load_seen()
        for project in self.pm.list_projects():
            if not project.enabled:
                continue
            compiled = self.pm.compiled_regexes(project.name)
            if not compiled:
                continue

            ws = self.sheets.get_or_create_ws(
                project.sent_sheet_id,
                project.sent_ws_title,
                header=["timestamp_local", "username", "tweet_link", "project", "regex"]
            )
            rows_to_append = []

            for username in self._get_usernames(project):
                tweets = self.twitter.get_tweets(username)
                for tw in tweets:
                    link = tw["link"]
                    if link in seen:
                        continue

                    matched = None
                    for rx in compiled:
                        if rx.search(tw["text"]):
                            matched = rx.pattern
                            break
                    if not matched:
                        continue

                    ts_local = tw["created_at"].astimezone().strftime("%Y-%m-%d %H:%M:%S")
                    msg = f"🔔 <b>@{username}</b>\n{link}"
                    for cid in project.chat_ids:
                        self.notifier.send(cid, msg)

                    rows_to_append.append([ts_local, username, link, project.name, matched])
                    seen.add(link)

            if rows_to_append:
                self.sheets.append_rows(ws, rows_to_append)

        self.save_seen(seen)

    async def run(self):
        self.twitter.login()
        app = self.bot.build_app()
        asyncio.create_task(self._monitor_loop())
        await app.initialize()
        await app.start()
        await app.updater.start_polling()
        await app.updater.idle()

    async def _monitor_loop(self):
        while True:
            try:
                self.run_scan_once()
            except Exception as e:
                logging.exception(e)
            await asyncio.sleep(120)

if __name__ == "__main__":
    asyncio.run(MonitorApp().run())