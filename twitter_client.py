import os
import re
import time
import pickle
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from utils import retry

class TwitterClient:
    def __init__(self, cookie_path="data/cookies.pkl", profile_dir="data/chrome_profile"):
        self.cookie_path = cookie_path
        self.profile_dir = profile_dir
        self.driver = self._build_driver()

    def _build_driver(self):
        options = Options()
        options.add_argument("--start-maximized")
        options.add_argument(f"--user-data-dir={os.path.abspath(self.profile_dir)}")
        options.add_argument("--profile-directory=Default")
        return webdriver.Chrome(options=options)

    def close(self):
        try:
            self.driver.quit()
        except Exception:
            pass

    @retry(max_attempts=3, delay=2.0)
    def login(self):
        if not os.path.exists(self.cookie_path):
            self.driver.get("https://twitter.com/login")
            time.sleep(120)
            pickle.dump(self.driver.get_cookies(), open(self.cookie_path, "wb"))
            return True
        self.driver.get("https://twitter.com/")
        cookies = pickle.load(open(self.cookie_path, "rb"))
        for c in cookies:
            try:
                self.driver.add_cookie(c)
            except Exception:
                pass
        self.driver.refresh()
        time.sleep(3)
        return True

    def _tweet_id(self, link):
        m = re.search(r"/status/(\d+)", link or "")
        return m.group(1) if m else ""

    def get_tweets(self, username, scrolls=5):
        self.driver.get(f"https://twitter.com/{username}")
        time.sleep(5)
        for _ in range(scrolls):
            self.driver.execute_script("window.scrollBy(0, 350);")
            time.sleep(1.5)

        tweets = self.driver.find_elements(By.XPATH, '//article[@data-testid="tweet"]')
        results = []

        for t in tweets:
            try:
                try:
                    btn = t.find_element(By.XPATH, './/button[@data-testid="tweet-text-show-more-link"]')
                    btn.click()
                    time.sleep(0.2)
                except Exception:
                    pass

                ts = t.find_element(By.XPATH, './/time').get_attribute("datetime")
                link = t.find_element(By.XPATH, './/a[@role="link" and contains(@href, "/status/")]').get_attribute("href")
                try:
                    text = t.find_element(By.XPATH, './/div[@data-testid="tweetText"]').text
                except Exception:
                    text = ""

                dt_utc = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                results.append({
                    "username": username,
                    "tweet_id": self._tweet_id(link),
                    "link": link,
                    "text": text,
                    "created_at": dt_utc,
                })
            except Exception:
                continue

        return results