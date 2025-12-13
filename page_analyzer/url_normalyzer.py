from urllib.parse import urlparse


class Url:
    def __init__(self, dict):
        self.__dict__.update(dict)

    def is_valid(self):
        try:
            if self.scheme not in ('http', 'https'):
                return False
            if not self.netloc:
                return False
        except Exception:
            return False
        return True

    def parse(self):
        if self.text:
            parsed = urlparse(self.text)

            self.set_value("scheme", parsed.scheme)
            self.set_value("netloc", parsed.netloc)
            self.set_value("name", f'{parsed.scheme}://{parsed.netloc}')

    def set_value(self, key, value):
        self.__dict__[key] = value
