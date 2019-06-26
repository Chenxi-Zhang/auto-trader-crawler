from ..util.base import (
    get_html_response,
    bs_parse,
)

class WebViewer(object):

    def __init__(self, url):
        self.url = url
        self.response = None
        self.is_content_loaded = False
        self.soup = None
        self.is_content_parsed = False

    def _load_content(self, url):
        return get_html_response(url)

    def _parse_response(self, response):
        return bs_parse(response)

    def load_content(self):
        self.response = self._load_content(self.url)
        self.is_content_loaded = True

    def parse_response(self):
        if self.is_content_loaded:
            self.soup = self._parse_response(self.response)
            self.is_content_parsed = True
