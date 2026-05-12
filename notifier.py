import time
import requests

class Notifier:
    def __init__(self, bot_token, min_interval=1.2):
        self.bot_token = bot_token
        self.min_interval = min_interval
        self._last_send = 0.0

    def send(self, chat_id, text, parse_mode="HTML"):
        now = time.time()
        if now - self._last_send < self.min_interval:
            return False
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        r = requests.get(url, params={"chat_id": chat_id, "text": text, "parse_mode": parse_mode}, timeout=15)
        self._last_send = now
        return r.status_code == 200

    def send_document(self, chat_id, file_path, caption=""):
        url = f"https://api.telegram.org/bot{self.bot_token}/sendDocument"
        with open(file_path, "rb") as f:
            r = requests.post(url, data={"chat_id": chat_id, "caption": caption}, files={"document": f}, timeout=30)
        return r.status_code == 200