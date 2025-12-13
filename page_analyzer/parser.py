from datetime import datetime

import requests
from bs4 import BeautifulSoup


class UrlCheck:
    def __init__(self, url):
        self.url = url

    def make_check(self):
        try:
            req = requests.get(self.url.name, timeout=5)
            req.raise_for_status()
        except Exception as e:
            self.set_value("ok", False)
            self.set_value("error", f"Ошибка запроса: {e}")
            return
        self.set_value("status_code", req.status_code)
        self.set_value("ok", req.ok)
        self.set_value("created_at", datetime.now())

        bs = BeautifulSoup(req.text, "html.parser")
        h1 = bs.find("h1")
        self.set_value("h1", h1.text if h1 else "")
        title = bs.find("title")
        self.set_value("title", title.text if title else "")
        meta = bs.find('meta', attrs={"name": "description"})
        if meta and meta.get("content"):
            description = meta["content"]
        else:
            description = ""
        self.set_value("description", description)

    def set_value(self, key, value):
        self.__dict__[key] = value
